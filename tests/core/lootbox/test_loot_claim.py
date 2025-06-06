import pytest
import boa

from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS
from conf_utils import filter_logs


def test_loot_claim_basic(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setRipeRewardsConfig()

    # Setup deposit points
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    
    # Time travel to accumulate points
    boa.env.time_travel(blocks=20)

    # update deposit points
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # user points
    up = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert up.balancePoints != 0

    claimable = lootbox.getClaimableLoot(bob)
    assert claimable != 0

    asset_claimable = lootbox.getClaimableDepositLootForAsset(bob, vault_id, alpha_token)
    assert asset_claimable != 0

    # claim loot
    total_ripe = teller.claimLoot(bob, False, sender=bob)
    assert total_ripe != 0

    assert ripe_token.balanceOf(bob) == total_ripe

    # verify points are reset
    up = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert up.balancePoints == 0
    
    # verify claimable amount is now zero
    claimable = lootbox.getClaimableLoot(bob)
    assert claimable == 0


def test_loot_claim_multiple_users(
    bob,
    alice,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    setUserDelegation,
    sally,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setRipeRewardsConfig()

    setUserDelegation(bob, sally)
    setUserDelegation(alice, sally)

    # Setup deposit points for both users
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    performDeposit(alice, 50 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    
    # Time travel to accumulate points
    boa.env.time_travel(blocks=20)

    # update deposit points for both users
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(alice, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # claim loot for both users
    total_ripe = teller.claimLootForManyUsers([bob, alice], False, sender=sally)
    assert total_ripe != 0

    # verify both users received their share
    bob_ripe = ripe_token.balanceOf(bob)
    alice_ripe = ripe_token.balanceOf(alice)
    assert bob_ripe + alice_ripe == total_ripe
    assert bob_ripe > alice_ripe  # Bob deposited more, should get more rewards


def test_loot_claim_specific_asset(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setRipeRewardsConfig()

    # Setup deposit points
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    
    # Time travel to accumulate points
    boa.env.time_travel(blocks=20)

    # update deposit points
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # claim loot for specific asset
    total_ripe = lootbox.claimDepositLootForAsset(bob, vault_id, alpha_token, sender=teller.address)
    assert total_ripe != 0

    assert ripe_token.balanceOf(bob) == total_ripe

    # verify points are reset for this asset
    up = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert up.balancePoints == 0


def test_loot_claim_points_disabled(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    alpha_token,
    alpha_token_whale,
):
    # basic setup with points disabled
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setRipeRewardsConfig(_arePointsEnabled=False)

    # Setup deposit points
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    
    # Time travel to accumulate points
    boa.env.time_travel(blocks=20)

    # update deposit points
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # verify no points accumulated
    up = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert up.balancePoints == 0

    # verify no claimable loot
    claimable = lootbox.getClaimableLoot(bob)
    assert claimable == 0

    # attempt to claim loot
    total_ripe = teller.claimLoot(bob, False, sender=bob)
    assert total_ripe == 0


def test_loot_claim_different_allocations(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
):
    # basic setup with different reward allocations
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=80, _voterPointsAlloc=20)
    setRipeRewardsConfig(
        _borrowersAlloc=20,
        _stakersAlloc=40,
        _votersAlloc=20,
        _genDepositorsAlloc=20,
    )

    # Setup deposit points
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    
    # Time travel to accumulate points
    boa.env.time_travel(blocks=20)

    # update deposit points
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # claim loot
    total_ripe = teller.claimLoot(bob, False, sender=bob)
    assert total_ripe != 0

    assert ripe_token.balanceOf(bob) == total_ripe

    # verify points are reset
    up = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert up.balancePoints == 0


def test_loot_claim_borrow_basic(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    ripe_token,
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

    # Check claimable amount
    claimable = lootbox.getClaimableBorrowLoot(bob)
    assert claimable != 0

    # Claim borrow loot
    total_ripe = lootbox.claimBorrowLoot(bob, sender=teller.address)
    assert total_ripe == claimable
    assert ripe_token.balanceOf(bob) == total_ripe

    # Verify points are reset
    up = ledger.userBorrowPoints(bob)
    assert up.points == 0


def test_loot_claim_borrow_multiple_users(
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

    # Claim borrow loot for both users
    bob_ripe = lootbox.claimBorrowLoot(bob, sender=teller.address)
    alice_ripe = lootbox.claimBorrowLoot(alice, sender=teller.address)

    # Verify rewards are proportional to debt
    assert bob_ripe > 0
    assert alice_ripe > 0
    assert alice_ripe > bob_ripe  # Alice has more debt, should get more rewards

    # Verify points are reset for both users
    up_bob = ledger.userBorrowPoints(bob)
    up_alice = ledger.userBorrowPoints(alice)
    assert up_bob.points == 0
    assert up_alice.points == 0


def test_loot_claim_borrow_points_disabled(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    ripe_token,
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

    # Verify no claimable loot
    claimable = lootbox.getClaimableBorrowLoot(bob)
    assert claimable == 0

    # Attempt to claim
    total_ripe = lootbox.claimBorrowLoot(bob, sender=teller.address)
    assert total_ripe == 0
    assert ripe_token.balanceOf(bob) == 0


def test_loot_claim_borrow_debt_changes(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    ripe_token,
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

    # Claim borrow loot
    total_ripe = lootbox.claimBorrowLoot(bob, sender=teller.address)
    assert total_ripe > 0
    assert ripe_token.balanceOf(bob) == total_ripe

    # Verify points are reset
    up = ledger.userBorrowPoints(bob)
    assert up.points == 0


def test_loot_claim_borrow_zero_debt(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    ripe_token,
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

    # Claim borrow loot
    total_ripe = lootbox.claimBorrowLoot(bob, sender=teller.address)
    assert total_ripe > 0  # Should still get rewards for period with debt
    assert ripe_token.balanceOf(bob) == total_ripe

    # Verify points are reset
    up = ledger.userBorrowPoints(bob)
    assert up.points == 0


def test_loot_claim_borrow_different_allocations(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    ripe_token,
):
    # basic setup with different reward allocations
    setGeneralConfig()
    setRipeRewardsConfig(
        True,
        _borrowersAlloc=50,  # Higher allocation for borrowers
        _stakersAlloc=20,
        _votersAlloc=20,
        _genDepositorsAlloc=10,
    )

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

    # Claim borrow loot
    total_ripe = lootbox.claimBorrowLoot(bob, sender=teller.address)
    assert total_ripe > 0
    assert ripe_token.balanceOf(bob) == total_ripe

    # Verify points are reset
    up = ledger.userBorrowPoints(bob)
    assert up.points == 0


def test_loot_claim_borrow_large_debt(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    ripe_token,
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

    # Claim borrow loot
    total_ripe = lootbox.claimBorrowLoot(bob, sender=teller.address)
    assert total_ripe > 0
    assert ripe_token.balanceOf(bob) == total_ripe

    # Verify points are reset
    up = ledger.userBorrowPoints(bob)
    assert up.points == 0


def test_loot_claim_borrow_permission_checks(
    bob,
    alice,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    switchboard_one,
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

    # Test unauthorized caller
    with boa.reverts("no perms"):
        lootbox.claimBorrowLoot(bob, sender=alice)

    # Test paused state
    lootbox.pause(True, sender=switchboard_one.address)
    with boa.reverts("contract paused"):
        lootbox.claimBorrowLoot(bob, sender=teller.address)

    # Unpause and verify it works
    lootbox.pause(False, sender=switchboard_one.address)
    total_ripe = lootbox.claimBorrowLoot(bob, sender=teller.address)
    assert total_ripe > 0


def test_loot_claim_borrow_rapid_claims(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    ripe_token,
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

    # First claim
    first_claim = lootbox.claimBorrowLoot(bob, sender=teller.address)
    assert first_claim > 0
    assert ripe_token.balanceOf(bob) == first_claim

    # Try to claim again immediately
    second_claim = lootbox.claimBorrowLoot(bob, sender=teller.address)
    assert second_claim == 0  # No new rewards to claim
    assert ripe_token.balanceOf(bob) == first_claim  # Balance shouldn't change

    # Time travel and update points again
    boa.env.time_travel(blocks=20)
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Third claim after new points
    third_claim = lootbox.claimBorrowLoot(bob, sender=teller.address)
    assert third_claim > 0  # Should have new rewards
    assert ripe_token.balanceOf(bob) == first_claim + third_claim


def test_loot_claim_borrow_event_emission(
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

    # Claim borrow loot and check event
    ripe_amount = lootbox.claimBorrowLoot(bob, sender=teller.address)
    log = filter_logs(lootbox, "BorrowLootClaimed")[0]
    assert log.user == bob
    assert log.ripeAmount == ripe_amount


def test_loot_claim_borrow_empty_address(
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    ripe_token,
):
    # basic setup
    setGeneralConfig()
    setRipeRewardsConfig(True)

    # Try to claim for empty address
    total_ripe = lootbox.claimBorrowLoot(ZERO_ADDRESS, sender=teller.address)
    assert total_ripe == 0
    assert ripe_token.balanceOf(ZERO_ADDRESS) == 0

    # Verify no points accumulated
    up = ledger.userBorrowPoints(ZERO_ADDRESS)
    assert up.points == 0


def test_loot_claim_borrow_no_debt(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    ripe_token,
):
    # basic setup
    setGeneralConfig()
    setRipeRewardsConfig(True)

    # First update with no debt
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Time travel
    elapsed = 20
    boa.env.time_travel(blocks=elapsed)

    # Update again
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Try to claim
    total_ripe = lootbox.claimBorrowLoot(bob, sender=teller.address)
    assert total_ripe == 0
    assert ripe_token.balanceOf(bob) == 0

    # Verify no points accumulated
    up = ledger.userBorrowPoints(bob)
    assert up.points == 0


def test_loot_claim_combined_deposit_and_borrow(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    ripe_token,
    alpha_token,
    alpha_token_whale,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setRipeRewardsConfig(True)

    # Setup deposit points
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    
    # Setup borrow points
    debt_terms = createDebtTerms()
    user_debt = (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(bob, user_debt, 0, (0, 0), sender=credit_engine.address)

    # first update
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Time travel to accumulate points
    boa.env.time_travel(blocks=20)

    # Update both deposit and borrow points
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Get claimable amounts
    deposit_claimable = lootbox.getClaimableDepositLootForAsset(bob, vault_id, alpha_token)
    borrow_claimable = lootbox.getClaimableBorrowLoot(bob)
    total_claimable = lootbox.getClaimableLoot(bob)

    assert deposit_claimable > 0
    assert borrow_claimable > 0
    assert total_claimable == deposit_claimable + borrow_claimable

    # Claim all loot
    total_ripe = teller.claimLoot(bob, False, sender=bob)
    assert total_ripe == total_claimable
    assert ripe_token.balanceOf(bob) == total_ripe

    # Verify points are reset
    up_deposit = ledger.userDepositPoints(bob, vault_id, alpha_token)
    up_borrow = ledger.userBorrowPoints(bob)
    assert up_deposit.balancePoints == 0
    assert up_borrow.points == 0


def test_loot_claim_borrow_integer_overflow_protection(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    ripe_token,
):
    # basic setup
    setGeneralConfig()
    setRipeRewardsConfig(True)

    # set up extremely large debt
    debt_terms = createDebtTerms()
    max_debt = (MAX_UINT256, MAX_UINT256, debt_terms, 0, False)
    ledger.setUserDebt(bob, max_debt, 0, (0, 0), sender=credit_engine.address)

    # First update
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Time travel
    elapsed = 1000
    boa.env.time_travel(blocks=elapsed)

    # Update again
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Claim borrow loot - should not overflow
    total_ripe = lootbox.claimBorrowLoot(bob, sender=teller.address)
    assert total_ripe > 0
    assert total_ripe < MAX_UINT256  # Should not overflow
    assert ripe_token.balanceOf(bob) == total_ripe

    # Verify points are reset
    up = ledger.userBorrowPoints(bob)
    assert up.points == 0


def test_loot_claim_borrow_zero_rewards(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    ripe_token,
):
    # basic setup with zero rewards
    setGeneralConfig()
    setRipeRewardsConfig(
        True,
        _borrowersAlloc=0,  # No rewards for borrowers
        _stakersAlloc=100,
        _votersAlloc=0,
        _genDepositorsAlloc=0,
    )

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

    # Try to claim
    total_ripe = lootbox.claimBorrowLoot(bob, sender=teller.address)
    assert total_ripe == 0  # No rewards allocated to borrowers
    assert ripe_token.balanceOf(bob) == 0

    # Verify points are still tracked
    up = ledger.userBorrowPoints(bob)
    assert up.points > 0  # Points should still accumulate even with no rewards


# auto-staking ripe claims


def test_loot_claim_no_auto_staking(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    mission_control,
    switchboard_one,
    ripe_gov_vault,
):
    """Test that with autoStakeRatio=0, all rewards go directly to user"""
    # Setup with no auto-staking
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setRipeRewardsConfig(_autoStakeRatio=0, _autoStakeDurationRatio=0)
    
    # Configure RipeGov vault for ripe token
    mission_control.setRipeGovVaultConfig(
        ripe_token,
        100_00,  # 100% asset weight
        (86400, 2592000, 200_00, True, 5_00),  # 1 day min, 30 days max, 200% boost, can exit, 5% fee
        sender=switchboard_one.address
    )

    # Setup deposit to earn rewards
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # Accumulate rewards
    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Record balances before claim
    initial_wallet_balance = ripe_token.balanceOf(bob)
    initial_vault_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)

    # Claim loot without staking
    total_ripe = teller.claimLoot(bob, False, sender=bob)
    assert total_ripe > 0

    # Verify all rewards went to wallet, none to vault
    final_wallet_balance = ripe_token.balanceOf(bob)
    final_vault_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    
    assert final_wallet_balance == initial_wallet_balance + total_ripe
    assert final_vault_balance == initial_vault_balance  # No change in vault


def test_loot_claim_full_auto_staking(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    mission_control,
    switchboard_one,
    ripe_gov_vault,
    _test,
):
    """Test that with autoStakeRatio=100%, all rewards get staked"""
    # Setup with full auto-staking
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(ripe_token, _vaultIds=[2])  # Configure ripe token for vault 2
    setRipeRewardsConfig(_autoStakeRatio=100_00, _autoStakeDurationRatio=50_00)  # 100% stake, 50% duration
    
    # Configure RipeGov vault for ripe token
    mission_control.setRipeGovVaultConfig(
        ripe_token,
        100_00,  # 100% asset weight
        (86400, 2592000, 200_00, True, 5_00),  # 1 day min, 30 days max, 200% boost, can exit, 5% fee
        sender=switchboard_one.address
    )

    # Setup deposit to earn rewards
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # Accumulate rewards
    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Record balances before claim
    initial_wallet_balance = ripe_token.balanceOf(bob)
    initial_vault_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)

    # Claim loot without explicit staking (auto-staking should kick in)
    total_ripe = teller.claimLoot(bob, False, sender=bob)
    assert total_ripe > 0

    # Verify all rewards went to vault, none to wallet
    final_wallet_balance = ripe_token.balanceOf(bob)
    final_vault_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    
    assert final_wallet_balance == initial_wallet_balance  # No change in wallet
    assert final_vault_balance > initial_vault_balance  # Increased vault balance
    _test(final_vault_balance, initial_vault_balance + total_ripe)

    # Verify the lock duration was calculated correctly
    # Expected: 50% of (30 days - 1 day) = 50% of 29 days = ~14.5 days = ~1,252,800 blocks
    userData = ripe_gov_vault.userGovData(bob, ripe_token)
    expected_duration_range = 2592000 - 86400  # max - min
    expected_lock_duration = expected_duration_range * 50_00 // 100_00  # 50% of range
    _test(expected_lock_duration, userData.unlock)
    

def test_loot_claim_partial_auto_staking(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    mission_control,
    switchboard_one,
    ripe_gov_vault,
    _test,
):
    """Test that with autoStakeRatio=60%, 60% gets staked and 40% sent to user"""
    # Setup with partial auto-staking
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(ripe_token, _vaultIds=[2])  # Configure ripe token for vault 2
    setRipeRewardsConfig(_autoStakeRatio=60_00, _autoStakeDurationRatio=25_00)  # 60% stake, 25% duration
    
    # Configure RipeGov vault for ripe token
    mission_control.setRipeGovVaultConfig(
        ripe_token,
        100_00,  # 100% asset weight
        (100, 1000, 100_00, False, 0),  # 100 min, 1000 max, 100% boost, cannot exit, 0% fee
        sender=switchboard_one.address
    )

    # Setup deposit to earn rewards
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # Accumulate rewards
    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Record balances before claim
    initial_wallet_balance = ripe_token.balanceOf(bob)
    initial_vault_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)

    # Claim loot without explicit staking
    total_ripe = teller.claimLoot(bob, False, sender=bob)
    assert total_ripe > 0

    # Verify correct split between wallet and vault
    final_wallet_balance = ripe_token.balanceOf(bob)
    final_vault_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    
    expected_staked = total_ripe * 60_00 // 100_00  # 60% staked
    expected_to_wallet = total_ripe - expected_staked  # 40% to wallet
    
    actual_to_wallet = final_wallet_balance - initial_wallet_balance
    actual_vault_increase = final_vault_balance - initial_vault_balance
    
    # Use _test for approximate comparisons (allowing small rounding differences)
    _test(expected_to_wallet, actual_to_wallet)
    _test(expected_staked, actual_vault_increase)

    # Verify the lock duration was calculated correctly
    # Expected: 25% of (1000 - 100) = 25% of 900 = 225 blocks
    userData = ripe_gov_vault.userGovData(bob, ripe_token)
    expected_duration_range = 1000 - 100  # max - min
    expected_lock_duration = expected_duration_range * 25_00 // 100_00  # 25% of range
    
    # Calculate the actual lock duration by looking at what was set
    current_block = boa.env.evm.patch.block_number
    actual_lock_duration = userData.unlock - current_block
    
    # The lock duration should be exactly what we expect (225 blocks)
    assert actual_lock_duration == expected_lock_duration


def test_loot_claim_explicit_staking_overrides_auto(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    mission_control,
    switchboard_one,
    ripe_gov_vault,
):
    """Test that _shouldStake=True overrides autoStakeRatio and stakes everything"""
    # Setup with low auto-staking
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(ripe_token.address, _vaultIds=[2])  # Configure ripe token for vault 2
    setRipeRewardsConfig(_autoStakeRatio=20_00, _autoStakeDurationRatio=30_00)  # Only 20% auto-stake
    
    # Configure RipeGov vault for ripe token
    mission_control.setRipeGovVaultConfig(
        ripe_token.address,
        100_00,  # 100% asset weight
        (100, 1000, 100_00, False, 0),  # 100 min, 1000 max, 100% boost, cannot exit, 0% fee
        sender=switchboard_one.address
    )

    # Setup deposit to earn rewards
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # Accumulate rewards
    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Record balances before claim
    initial_wallet_balance = ripe_token.balanceOf(bob)
    initial_vault_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)

    # Claim loot WITH explicit staking - should override autoStakeRatio
    total_ripe = teller.claimLoot(bob, True, sender=bob)  # _shouldStake=True
    assert total_ripe > 0

    # Verify ALL rewards went to vault (despite low autoStakeRatio)
    final_wallet_balance = ripe_token.balanceOf(bob)
    final_vault_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    
    assert final_wallet_balance == initial_wallet_balance  # No change in wallet
    assert final_vault_balance > initial_vault_balance  # All rewards went to vault


def test_loot_claim_zero_lock_duration_range(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    mission_control,
    switchboard_one,
    ripe_gov_vault,
):
    """Test that when min=max lock duration, vault still enforces minimum lock duration"""
    # Setup with auto-staking but zero duration range
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(ripe_token.address, _vaultIds=[2])  # Configure ripe token for vault 2
    setRipeRewardsConfig(_autoStakeRatio=100_00, _autoStakeDurationRatio=50_00)
    
    # Configure RipeGov vault with same min/max lock duration
    mission_control.setRipeGovVaultConfig(
        ripe_token.address,
        100_00,  # 100% asset weight
        (500, 500, 200_00, True, 5_00),  # min = max = 500 blocks
        sender=switchboard_one.address
    )

    # Setup deposit to earn rewards
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # Accumulate rewards
    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Claim loot
    total_ripe = teller.claimLoot(bob, False, sender=bob)
    assert total_ripe > 0

    # Verify tokens were staked with minimum lock duration (vault enforces minimum)
    # When min=max, the vault still enforces the minimum lock duration for security
    userData = ripe_gov_vault.userGovData(bob, ripe_token)
    current_block = boa.env.evm.patch.block_number
    expected_unlock = current_block + 500  # Minimum lock duration of 500 blocks
    assert userData.unlock == expected_unlock


def test_loot_claim_max_lock_duration_ratio(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    mission_control,
    switchboard_one,
    ripe_gov_vault,
):
    """Test that autoStakeDurationRatio=100% uses the full lock duration range"""
    # Setup with auto-staking and max duration ratio
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(ripe_token.address, _vaultIds=[2])  # Configure ripe token for vault 2
    setRipeRewardsConfig(_autoStakeRatio=100_00, _autoStakeDurationRatio=100_00)  # Max duration
    
    # Configure RipeGov vault
    mission_control.setRipeGovVaultConfig(
        ripe_token.address,
        100_00,  # 100% asset weight
        (200, 1000, 200_00, True, 5_00),  # 200 min, 1000 max
        sender=switchboard_one.address
    )

    # Setup deposit to earn rewards
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # Accumulate rewards
    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Claim loot
    total_ripe = teller.claimLoot(bob, False, sender=bob)
    assert total_ripe > 0

    # Verify tokens were staked with maximum lock duration
    userData = ripe_gov_vault.userGovData(bob, ripe_token)
    expected_duration_range = 1000 - 200  # max - min = 800
    expected_lock_duration = expected_duration_range  # 100% of range
    
    current_block = boa.env.evm.patch.block_number
    expected_unlock = current_block + expected_lock_duration
    assert userData.unlock == expected_unlock


def test_loot_claim_zero_rewards_no_staking_calls(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    teller,
    ripe_token,
    alpha_token,
    mission_control,
    switchboard_one,
    ripe_gov_vault,
):
    """Test that zero rewards don't trigger any staking operations"""
    # Setup with auto-staking
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(ripe_token.address, _vaultIds=[2])  # Configure ripe token for vault 2
    setRipeRewardsConfig(_autoStakeRatio=100_00, _autoStakeDurationRatio=50_00)
    
    # Configure RipeGov vault
    mission_control.setRipeGovVaultConfig(
        ripe_token.address,
        100_00,  # 100% asset weight
        (100, 1000, 200_00, True, 5_00),
        sender=switchboard_one.address
    )

    # Don't setup any deposits or debt - no rewards to claim
    
    # Record balances before claim
    initial_wallet_balance = ripe_token.balanceOf(bob)
    initial_vault_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)

    # Attempt to claim loot
    total_ripe = teller.claimLoot(bob, False, sender=bob)
    assert total_ripe == 0

    # Verify no changes occurred
    final_wallet_balance = ripe_token.balanceOf(bob)
    final_vault_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    
    assert final_wallet_balance == initial_wallet_balance
    assert final_vault_balance == initial_vault_balance


def test_loot_claim_calculation_consistency_with_partial_auto_staking(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    mission_control,
    switchboard_one,
):
    """Test that getClaimableLoot() matches actual claimLoot() returns with partial auto-staking"""
    # Setup with partial auto-staking
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(ripe_token.address, _vaultIds=[2])  # Configure ripe token for vault 2
    setRipeRewardsConfig(_autoStakeRatio=50_00, _autoStakeDurationRatio=50_00)  # 50% stake, 50% send
    
    # Configure RipeGov vault
    mission_control.setRipeGovVaultConfig(
        ripe_token.address,
        100_00,  # 100% asset weight
        (100, 1000, 100_00, False, 0),
        sender=switchboard_one.address
    )

    # Setup deposit to earn rewards
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # Accumulate rewards
    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Get expected claimable amount
    claimable = lootbox.getClaimableLoot(bob)
    assert claimable > 0

    # Claim loot - should match the calculated claimable amount
    total_ripe = teller.claimLoot(bob, False, sender=bob)
    assert total_ripe == claimable

    # Verify the user received some tokens (50% should go to wallet with partial auto-staking)
    final_wallet_balance = ripe_token.balanceOf(bob)
    assert final_wallet_balance > 0  # Should have received 50% of claimed tokens


def test_loot_claim_multiple_claims_with_staking(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    mission_control,
    switchboard_one,
    ripe_gov_vault,
):
    """Test multiple claims with auto-staking to verify cumulative behavior"""
    # Setup with auto-staking
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(ripe_token.address, _vaultIds=[2])  # Configure ripe token for vault 2
    setRipeRewardsConfig(_autoStakeRatio=100_00, _autoStakeDurationRatio=50_00)
    
    # Configure RipeGov vault
    mission_control.setRipeGovVaultConfig(
        ripe_token.address,
        100_00,  # 100% asset weight
        (100, 1000, 200_00, True, 5_00),
        sender=switchboard_one.address
    )

    # Setup deposit to earn rewards
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # First claim cycle
    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    
    first_vault_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    first_claim = teller.claimLoot(bob, False, sender=bob)
    assert first_claim > 0
    
    after_first_vault_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    assert after_first_vault_balance > first_vault_balance

    # Second claim cycle - accumulate more rewards
    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    
    second_claim = teller.claimLoot(bob, False, sender=bob)
    assert second_claim > 0
    
    final_vault_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    assert final_vault_balance > after_first_vault_balance

    # Verify cumulative staking worked
    total_expected_staked = first_claim + second_claim
    total_actual_staked = final_vault_balance - first_vault_balance
    assert total_actual_staked == total_expected_staked

    # Verify wallet balance remained unchanged (all auto-staked)
    wallet_balance = ripe_token.balanceOf(bob)
    assert wallet_balance == 0


def test_loot_claim_auto_stake_configuration_updates(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    mission_control,
    switchboard_one,
    ripe_gov_vault,
):
    """Test that configuration changes affect subsequent claims correctly"""
    # Initial setup with no auto-staking
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(ripe_token.address, _vaultIds=[2])  # Configure ripe token for vault 2
    setRipeRewardsConfig(_autoStakeRatio=0, _autoStakeDurationRatio=0)
    
    # Configure RipeGov vault
    mission_control.setRipeGovVaultConfig(
        ripe_token.address,
        100_00,  # 100% asset weight
        (100, 1000, 100_00, False, 0),
        sender=switchboard_one.address
    )

    # Setup deposit to earn rewards
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # First claim with no auto-staking
    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    
    first_claim = teller.claimLoot(bob, False, sender=bob)
    assert first_claim > 0
    assert ripe_token.balanceOf(bob) == first_claim  # All to wallet
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 0  # None to vault

    # Update configuration to enable auto-staking
    setRipeRewardsConfig(_autoStakeRatio=100_00, _autoStakeDurationRatio=50_00)
    
    # Second claim with auto-staking enabled
    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    
    second_claim = teller.claimLoot(bob, False, sender=bob)
    assert second_claim > 0
    assert ripe_token.balanceOf(bob) == first_claim  # Wallet unchanged from first claim
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) > 0  # Second claim went to vault
