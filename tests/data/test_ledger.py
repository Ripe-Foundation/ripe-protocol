import pytest
import boa

from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS


############
# Fixtures #
############

@pytest.fixture
def sample_user_debt():
    return (
        1000 * EIGHTEEN_DECIMALS,  # amount
        800 * EIGHTEEN_DECIMALS,   # principal
        (50_00, 60_00, 70_00, 10_00, 5_00, 0),  # debtTerms (ltv, redemptionThreshold, liqThreshold, liqFee, borrowRate, daowry)
        1000,  # lastTimestamp
        False  # inLiquidation
    )

@pytest.fixture
def sample_ripe_rewards():
    return (
        100 * EIGHTEEN_DECIMALS,  # borrowers
        200 * EIGHTEEN_DECIMALS,  # stakers
        150 * EIGHTEEN_DECIMALS,  # voters
        250 * EIGHTEEN_DECIMALS,  # genDepositors
        50 * EIGHTEEN_DECIMALS,   # newRipeRewards
        2000  # lastUpdate
    )

@pytest.fixture
def sample_fungible_auction(alice, bob):
    return (
        alice,         # liqUser
        1,             # vaultId
        bob,           # asset (using bob as mock asset address)
        10_00,         # startDiscount
        50_00,         # maxDiscount
        1000,          # startBlock
        2000,          # endBlock
        True           # isActive
    )

###################
# User Vault Tests #
###################

def test_ledger_initial_state(ledger):
    """Test initial state of ledger contract."""
    assert ledger.totalDebt() == 0
    assert ledger.unrealizedYield() == 0
    assert ledger.numBorrowers() == 0
    assert ledger.numFungLiqUsers() == 0
    assert ledger.badDebt() == 0
    assert ledger.ripePaidOutForBadDebt() == 0

def test_ledger_add_vault_to_user_basic(ledger, alice, teller):
    """Test adding a vault to a user."""
    vault_id = 1
    
    # Initially user has no vaults
    assert ledger.getNumUserVaults(alice) == 0
    assert ledger.numUserVaults(alice) == 0
    assert not ledger.isParticipatingInVault(alice, vault_id)
    
    # Add vault
    ledger.addVaultToUser(alice, vault_id, sender=teller.address)
    
    # Check updated state
    assert ledger.getNumUserVaults(alice) == 1
    assert ledger.numUserVaults(alice) == 2  # internal uses 1-based indexing
    assert ledger.isParticipatingInVault(alice, vault_id)
    assert ledger.userVaults(alice, 1) == vault_id
    assert ledger.indexOfVault(alice, vault_id) == 1

def test_ledger_add_vault_to_user_multiple_vaults(ledger, alice, teller):
    """Test adding multiple vaults to a user."""
    vault_id_1 = 1
    vault_id_2 = 2
    vault_id_3 = 3
    
    # Add first vault
    ledger.addVaultToUser(alice, vault_id_1, sender=teller.address)
    assert ledger.getNumUserVaults(alice) == 1
    assert ledger.userVaults(alice, 1) == vault_id_1
    
    # Add second vault
    ledger.addVaultToUser(alice, vault_id_2, sender=teller.address)
    assert ledger.getNumUserVaults(alice) == 2
    assert ledger.userVaults(alice, 2) == vault_id_2
    
    # Add third vault
    ledger.addVaultToUser(alice, vault_id_3, sender=teller.address)
    assert ledger.getNumUserVaults(alice) == 3
    assert ledger.userVaults(alice, 3) == vault_id_3
    
    # Check all vaults are properly indexed
    assert ledger.indexOfVault(alice, vault_id_1) == 1
    assert ledger.indexOfVault(alice, vault_id_2) == 2
    assert ledger.indexOfVault(alice, vault_id_3) == 3

def test_ledger_add_vault_duplicate_fails_gracefully(ledger, alice, teller):
    """Test that adding same vault twice fails gracefully."""
    vault_id = 1
    
    # Add vault first time
    ledger.addVaultToUser(alice, vault_id, sender=teller.address)
    initial_count = ledger.getNumUserVaults(alice)
    
    # Add same vault again - should fail gracefully
    ledger.addVaultToUser(alice, vault_id, sender=teller.address)
    
    # Count should remain the same
    assert ledger.getNumUserVaults(alice) == initial_count
    assert ledger.indexOfVault(alice, vault_id) == 1

def test_ledger_add_vault_unauthorized_caller(ledger, alice, bob):
    """Test that only authorized contracts can add vaults."""
    vault_id = 1
    
    with boa.reverts("not allowed"):
        ledger.addVaultToUser(alice, vault_id, sender=bob)

def test_ledger_add_vault_contract_paused(ledger, alice, teller, switchboard_alpha):
    """Test that adding vault fails when contract is paused."""
    vault_id = 1
    
    # Pause the ledger
    ledger.pause(True, sender=switchboard_alpha.address)
    
    with boa.reverts("not activated"):
        ledger.addVaultToUser(alice, vault_id, sender=teller.address)
    
    # Unpause and try again
    ledger.pause(False, sender=switchboard_alpha.address)
    ledger.addVaultToUser(alice, vault_id, sender=teller.address)
    assert ledger.isParticipatingInVault(alice, vault_id)

def test_ledger_remove_vault_from_user_basic(ledger, alice, teller, lootbox):
    """Test removing a vault from a user."""
    vault_id = 1
    
    # Add vault first
    ledger.addVaultToUser(alice, vault_id, sender=teller.address)
    assert ledger.isParticipatingInVault(alice, vault_id)
    
    # Remove vault
    ledger.removeVaultFromUser(alice, vault_id, sender=lootbox.address)
    
    # Check vault is removed
    assert not ledger.isParticipatingInVault(alice, vault_id)
    assert ledger.getNumUserVaults(alice) == 0
    assert ledger.indexOfVault(alice, vault_id) == 0

def test_ledger_remove_vault_from_user_middle_vault(ledger, alice, teller, lootbox):
    """Test removing a vault from the middle of user's vault list."""
    vault_id_1 = 1
    vault_id_2 = 2
    vault_id_3 = 3
    
    # Add three vaults
    ledger.addVaultToUser(alice, vault_id_1, sender=teller.address)
    ledger.addVaultToUser(alice, vault_id_2, sender=teller.address)
    ledger.addVaultToUser(alice, vault_id_3, sender=teller.address)
    
    # Remove middle vault
    ledger.removeVaultFromUser(alice, vault_id_2, sender=lootbox.address)
    
    # Check that vault 3 moved to position 2
    assert ledger.getNumUserVaults(alice) == 2
    assert ledger.userVaults(alice, 1) == vault_id_1
    assert ledger.userVaults(alice, 2) == vault_id_3
    assert ledger.indexOfVault(alice, vault_id_1) == 1
    assert ledger.indexOfVault(alice, vault_id_2) == 0  # removed
    assert ledger.indexOfVault(alice, vault_id_3) == 2  # moved

def test_ledger_remove_vault_nonexistent_vault(ledger, alice, lootbox):
    """Test removing a vault that doesn't exist fails gracefully."""
    vault_id = 999
    
    # Try to remove non-existent vault
    ledger.removeVaultFromUser(alice, vault_id, sender=lootbox.address)
    
    # Should not cause any issues
    assert ledger.getNumUserVaults(alice) == 0

def test_ledger_remove_vault_unauthorized_caller(ledger, alice, bob):
    """Test that only Lootbox can remove vaults."""
    vault_id = 1
    
    with boa.reverts("only Lootbox allowed"):
        ledger.removeVaultFromUser(alice, vault_id, sender=bob)

def test_ledger_get_deposit_ledger_data(ledger, alice, teller):
    """Test getting deposit ledger data bundle."""
    vault_id = 1
    
    # Initially no participation
    data = ledger.getDepositLedgerData(alice, vault_id)
    assert not data.isParticipatingInVault
    assert data.numUserVaults == 0
    
    # Add vault and check again
    ledger.addVaultToUser(alice, vault_id, sender=teller.address)
    data = ledger.getDepositLedgerData(alice, vault_id)
    assert data.isParticipatingInVault
    assert data.numUserVaults == 1

##############
# Debt Tests #
##############

def test_ledger_set_user_debt_basic(ledger, alice, credit_engine, sample_user_debt):
    """Test setting user debt."""
    interval = (1000, 500 * EIGHTEEN_DECIMALS)  # start, amount
    new_yield = 10 * EIGHTEEN_DECIMALS
    
    # Initially no debt
    assert not ledger.hasDebt(alice)
    assert ledger.totalDebt() == 0
    assert not ledger.isBorrower(alice)
    
    # Set user debt
    ledger.setUserDebt(alice, sample_user_debt, new_yield, interval, sender=credit_engine.address)
    
    # Check debt was set
    assert ledger.hasDebt(alice)
    assert ledger.totalDebt() == sample_user_debt[0]  # amount
    assert ledger.isBorrower(alice)
    assert ledger.getNumBorrowers() == 1
    
    # Check unrealized yield was updated
    assert ledger.unrealizedYield() == new_yield
    
    # Check user debt details
    user_debt = ledger.userDebt(alice)
    assert user_debt.amount == sample_user_debt[0]
    assert user_debt.principal == sample_user_debt[1]
    assert not user_debt.inLiquidation
    
    # Check borrow interval
    borrow_interval = ledger.borrowIntervals(alice)
    assert borrow_interval.start == interval[0]
    assert borrow_interval.amount == interval[1]

def test_ledger_set_user_debt_update_existing(ledger, alice, credit_engine, sample_user_debt):
    """Test updating existing user debt."""
    interval = (1000, 500 * EIGHTEEN_DECIMALS)
    new_yield = 10 * EIGHTEEN_DECIMALS
    
    # Set initial debt
    ledger.setUserDebt(alice, sample_user_debt, new_yield, interval, sender=credit_engine.address)
    initial_total = ledger.totalDebt()
    
    # Update debt with higher amount
    updated_debt = list(sample_user_debt)
    updated_debt[0] = 2000 * EIGHTEEN_DECIMALS  # double the amount
    updated_debt = tuple(updated_debt)
    
    new_interval = (2000, 800 * EIGHTEEN_DECIMALS)
    additional_yield = 5 * EIGHTEEN_DECIMALS
    
    ledger.setUserDebt(alice, updated_debt, additional_yield, new_interval, sender=credit_engine.address)
    
    # Check updated debt
    assert ledger.totalDebt() == updated_debt[0]
    assert ledger.unrealizedYield() == new_yield + additional_yield
    assert ledger.getNumBorrowers() == 1  # still just one borrower

def test_ledger_set_user_debt_clear_debt(ledger, alice, credit_engine, sample_user_debt):
    """Test clearing user debt."""
    interval = (1000, 500 * EIGHTEEN_DECIMALS)
    new_yield = 10 * EIGHTEEN_DECIMALS
    
    # Set initial debt
    ledger.setUserDebt(alice, sample_user_debt, new_yield, interval, sender=credit_engine.address)
    assert ledger.hasDebt(alice)
    assert ledger.isBorrower(alice)
    
    # Clear debt
    no_debt = (0, 0, (0, 0, 0, 0, 0, 0), 0, False)
    empty_interval = (0, 0)
    ledger.setUserDebt(alice, no_debt, 0, empty_interval, sender=credit_engine.address)
    
    # Check debt is cleared
    assert not ledger.hasDebt(alice)
    assert ledger.totalDebt() == 0
    assert not ledger.isBorrower(alice)
    assert ledger.getNumBorrowers() == 0

def test_ledger_set_user_debt_multiple_borrowers(ledger, alice, bob, charlie, credit_engine, sample_user_debt):
    """Test managing multiple borrowers."""
    interval = (1000, 500 * EIGHTEEN_DECIMALS)
    new_yield = 10 * EIGHTEEN_DECIMALS
    
    # Add three borrowers
    ledger.setUserDebt(alice, sample_user_debt, new_yield, interval, sender=credit_engine.address)
    ledger.setUserDebt(bob, sample_user_debt, new_yield, interval, sender=credit_engine.address)
    ledger.setUserDebt(charlie, sample_user_debt, new_yield, interval, sender=credit_engine.address)
    
    assert ledger.getNumBorrowers() == 3
    assert ledger.totalDebt() == sample_user_debt[0] * 3
    assert ledger.isBorrower(alice)
    assert ledger.isBorrower(bob)
    assert ledger.isBorrower(charlie)
    
    # Remove middle borrower
    no_debt = (0, 0, (0, 0, 0, 0, 0, 0), 0, False)
    empty_interval = (0, 0)
    ledger.setUserDebt(bob, no_debt, 0, empty_interval, sender=credit_engine.address)
    
    assert ledger.getNumBorrowers() == 2
    assert not ledger.isBorrower(bob)
    assert ledger.isBorrower(alice)
    assert ledger.isBorrower(charlie)

def test_ledger_set_user_debt_unauthorized_caller(ledger, alice, bob, sample_user_debt):
    """Test that only CreditEngine can set user debt."""
    interval = (1000, 500 * EIGHTEEN_DECIMALS)
    new_yield = 10 * EIGHTEEN_DECIMALS
    
    with boa.reverts("only CreditEngine allowed"):
        ledger.setUserDebt(alice, sample_user_debt, new_yield, interval, sender=bob)

def test_ledger_set_user_debt_contract_paused(ledger, alice, credit_engine, sample_user_debt, switchboard_alpha):
    """Test that setting debt fails when contract is paused."""
    interval = (1000, 500 * EIGHTEEN_DECIMALS)
    new_yield = 10 * EIGHTEEN_DECIMALS
    
    # Pause the ledger
    ledger.pause(True, sender=switchboard_alpha.address)
    
    with boa.reverts("not activated"):
        ledger.setUserDebt(alice, sample_user_debt, new_yield, interval, sender=credit_engine.address)

def test_ledger_flush_unrealized_yield(ledger, alice, credit_engine, sample_user_debt):
    """Test flushing unrealized yield."""
    interval = (1000, 500 * EIGHTEEN_DECIMALS)
    new_yield = 50 * EIGHTEEN_DECIMALS
    
    # Set debt with yield
    ledger.setUserDebt(alice, sample_user_debt, new_yield, interval, sender=credit_engine.address)
    assert ledger.unrealizedYield() == new_yield
    
    # Flush yield
    flushed_yield = ledger.flushUnrealizedYield(sender=credit_engine.address)
    
    assert flushed_yield == new_yield
    assert ledger.unrealizedYield() == 0

def test_ledger_flush_unrealized_yield_unauthorized(ledger, alice):
    """Test that only CreditEngine can flush yield."""
    with boa.reverts("only CreditEngine allowed"):
        ledger.flushUnrealizedYield(sender=alice)

def test_ledger_get_borrow_data_bundle(ledger, alice, teller, credit_engine, sample_user_debt):
    """Test getting borrow data bundle."""
    vault_id = 1
    interval = (1000, 500 * EIGHTEEN_DECIMALS)
    new_yield = 10 * EIGHTEEN_DECIMALS
    
    # Add user to vault
    ledger.addVaultToUser(alice, vault_id, sender=teller.address)
    
    # Set debt
    ledger.setUserDebt(alice, sample_user_debt, new_yield, interval, sender=credit_engine.address)
    
    # Get bundle
    bundle = ledger.getBorrowDataBundle(alice)
    
    assert bundle.userDebt.amount == sample_user_debt[0]
    assert bundle.userBorrowInterval.start == interval[0]
    assert bundle.userBorrowInterval.amount == interval[1]
    assert bundle.isUserBorrower
    assert bundle.numUserVaults == 2  # internal uses 1-based indexing
    assert bundle.totalDebt == sample_user_debt[0]
    assert bundle.numBorrowers == 1

def test_ledger_get_repay_data_bundle(ledger, alice, teller, credit_engine, sample_user_debt):
    """Test getting repay data bundle."""
    vault_id = 1
    interval = (1000, 500 * EIGHTEEN_DECIMALS)
    new_yield = 10 * EIGHTEEN_DECIMALS
    
    # Add user to vault
    ledger.addVaultToUser(alice, vault_id, sender=teller.address)
    
    # Set debt
    ledger.setUserDebt(alice, sample_user_debt, new_yield, interval, sender=credit_engine.address)
    
    # Get bundle
    bundle = ledger.getRepayDataBundle(alice)
    
    assert bundle.userDebt.amount == sample_user_debt[0]
    assert bundle.numUserVaults == 2  # internal uses 1-based indexing

def test_ledger_is_user_in_liquidation(ledger, alice, credit_engine):
    """Test checking if user is in liquidation."""
    # Initially not in liquidation
    assert not ledger.isUserInLiquidation(alice)
    
    # Set debt with liquidation flag
    debt_in_liq = (
        1000 * EIGHTEEN_DECIMALS,  # amount
        800 * EIGHTEEN_DECIMALS,   # principal
        (50_00, 60_00, 70_00, 10_00, 5_00, 0),  # debtTerms
        1000,  # lastTimestamp
        True   # inLiquidation
    )
    interval = (1000, 500 * EIGHTEEN_DECIMALS)
    
    ledger.setUserDebt(alice, debt_in_liq, 0, interval, sender=credit_engine.address)
    
    assert ledger.isUserInLiquidation(alice)

####################
# Rewards/Points Tests #
####################

def test_ledger_set_ripe_rewards(ledger, lootbox, sample_ripe_rewards):
    """Test setting RIPE rewards."""
    initial_avail = ledger.ripeAvailForRewards()
    
    # Set RIPE rewards
    ledger.setRipeRewards(sample_ripe_rewards, sender=lootbox.address)
    
    # Check rewards were set
    rewards = ledger.ripeRewards()
    assert rewards.borrowers == sample_ripe_rewards[0]
    assert rewards.stakers == sample_ripe_rewards[1]
    assert rewards.voters == sample_ripe_rewards[2]
    assert rewards.genDepositors == sample_ripe_rewards[3]
    assert rewards.newRipeRewards == sample_ripe_rewards[4]
    assert rewards.lastUpdate == sample_ripe_rewards[5]
    
    # Check available RIPE was reduced
    expected_avail = initial_avail - sample_ripe_rewards[4]  # newRipeRewards
    assert ledger.ripeAvailForRewards() == max(0, expected_avail)

def test_ledger_set_ripe_rewards_unauthorized(ledger, alice, sample_ripe_rewards):
    """Test that only Lootbox can set RIPE rewards."""
    with boa.reverts("only Lootbox allowed"):
        ledger.setRipeRewards(sample_ripe_rewards, sender=alice)

def test_ledger_set_ripe_avail_for_rewards(ledger, switchboard_alpha):
    """Test setting RIPE available for rewards."""
    new_amount = 1000 * EIGHTEEN_DECIMALS
    
    ledger.setRipeAvailForRewards(new_amount, sender=switchboard_alpha.address)
    assert ledger.ripeAvailForRewards() == new_amount

def test_ledger_set_ripe_avail_for_rewards_unauthorized(ledger, alice):
    """Test that only Switchboard can set RIPE available for rewards."""
    new_amount = 1000 * EIGHTEEN_DECIMALS
    
    with boa.reverts("no perms"):
        ledger.setRipeAvailForRewards(new_amount, sender=alice)

def test_ledger_did_get_rewards_from_stab_claims(ledger, vault_book):
    """Test tracking rewards from stability pool claims."""
    initial_avail = ledger.ripeAvailForRewards()
    claim_amount = 100 * EIGHTEEN_DECIMALS
    
    ledger.didGetRewardsFromStabClaims(claim_amount, sender=vault_book.address)
    
    expected_avail = initial_avail - claim_amount
    assert ledger.ripeAvailForRewards() == expected_avail

def test_ledger_did_get_rewards_from_stab_claims_unauthorized(ledger, alice):
    """Test that only VaultBook can track stab claims."""
    claim_amount = 100 * EIGHTEEN_DECIMALS
    
    with boa.reverts("no perms"):
        ledger.didGetRewardsFromStabClaims(claim_amount, sender=alice)

def test_ledger_set_deposit_points_and_ripe_rewards(ledger, alice, lootbox, sample_ripe_rewards):
    """Test setting deposit points and RIPE rewards."""
    vault_id = 1
    asset = alice  # using alice as mock asset address
    
    # Create sample points
    user_points = (1000 * EIGHTEEN_DECIMALS, 500 * EIGHTEEN_DECIMALS, 2000)  # balancePoints, lastBalance, lastUpdate
    asset_points = (
        2000 * EIGHTEEN_DECIMALS,  # balancePoints
        1000 * EIGHTEEN_DECIMALS,  # lastBalance
        800 * EIGHTEEN_DECIMALS,   # lastUsdValue
        500 * EIGHTEEN_DECIMALS,   # ripeStakerPoints
        300 * EIGHTEEN_DECIMALS,   # ripeVotePoints
        200 * EIGHTEEN_DECIMALS,   # ripeGenPoints
        2000,  # lastUpdate
        EIGHTEEN_DECIMALS  # precision
    )
    global_points = (
        5000 * EIGHTEEN_DECIMALS,  # lastUsdValue
        1500 * EIGHTEEN_DECIMALS,  # ripeStakerPoints
        1200 * EIGHTEEN_DECIMALS,  # ripeVotePoints
        1000 * EIGHTEEN_DECIMALS,  # ripeGenPoints
        2000   # lastUpdate
    )
    
    ledger.setDepositPointsAndRipeRewards(
        alice, vault_id, asset, user_points, asset_points, global_points, sample_ripe_rewards,
        sender=lootbox.address
    )
    
    # Check user points were set
    stored_user_points = ledger.userDepositPoints(alice, vault_id, asset)
    assert stored_user_points.balancePoints == user_points[0]
    assert stored_user_points.lastBalance == user_points[1]
    assert stored_user_points.lastUpdate == user_points[2]
    
    # Check asset points were set
    stored_asset_points = ledger.assetDepositPoints(vault_id, asset)
    assert stored_asset_points.balancePoints == asset_points[0]
    assert stored_asset_points.lastBalance == asset_points[1]
    assert stored_asset_points.precision == asset_points[7]
    
    # Check global points were set
    stored_global_points = ledger.globalDepositPoints()
    assert stored_global_points.lastUsdValue == global_points[0]
    assert stored_global_points.ripeStakerPoints == global_points[1]

def test_ledger_set_borrow_points_and_ripe_rewards(ledger, alice, lootbox, sample_ripe_rewards):
    """Test setting borrow points and RIPE rewards."""
    user_points = (800 * EIGHTEEN_DECIMALS, 1000 * EIGHTEEN_DECIMALS, 2000)  # lastPrincipal, points, lastUpdate
    global_points = (1500 * EIGHTEEN_DECIMALS, 5000 * EIGHTEEN_DECIMALS, 2000)  # lastPrincipal, points, lastUpdate
    
    ledger.setBorrowPointsAndRipeRewards(
        alice, user_points, global_points, sample_ripe_rewards,
        sender=lootbox.address
    )
    
    # Check user borrow points
    stored_user_points = ledger.userBorrowPoints(alice)
    assert stored_user_points.lastPrincipal == user_points[0]
    assert stored_user_points.points == user_points[1]
    assert stored_user_points.lastUpdate == user_points[2]
    
    # Check global borrow points
    stored_global_points = ledger.globalBorrowPoints()
    assert stored_global_points.lastPrincipal == global_points[0]
    assert stored_global_points.points == global_points[1]
    assert stored_global_points.lastUpdate == global_points[2]

def test_ledger_get_ripe_rewards_bundle(ledger, lootbox, sample_ripe_rewards):
    """Test getting RIPE rewards bundle."""
    # Set some rewards first
    ledger.setRipeRewards(sample_ripe_rewards, sender=lootbox.address)
    
    bundle = ledger.getRipeRewardsBundle()
    
    assert bundle.ripeRewards.borrowers == sample_ripe_rewards[0]
    assert bundle.ripeRewards.stakers == sample_ripe_rewards[1]
    assert bundle.ripeAvailForRewards == ledger.ripeAvailForRewards()

def test_ledger_get_borrow_points_bundle(ledger, alice, lootbox, credit_engine, sample_user_debt, sample_ripe_rewards):
    """Test getting borrow points bundle."""
    # Set up user debt
    interval = (1000, 500 * EIGHTEEN_DECIMALS)
    ledger.setUserDebt(alice, sample_user_debt, 0, interval, sender=credit_engine.address)
    
    # Set borrow points
    user_points = (800 * EIGHTEEN_DECIMALS, 1000 * EIGHTEEN_DECIMALS, 2000)
    global_points = (1500 * EIGHTEEN_DECIMALS, 5000 * EIGHTEEN_DECIMALS, 2000)
    ledger.setBorrowPointsAndRipeRewards(alice, user_points, global_points, sample_ripe_rewards, sender=lootbox.address)
    
    bundle = ledger.getBorrowPointsBundle(alice)
    
    assert bundle.userPoints.points == user_points[1]
    assert bundle.globalPoints.points == global_points[1]
    assert bundle.userDebtPrincipal == sample_user_debt[1]  # principal

def test_ledger_get_deposit_points_bundle(ledger, alice, lootbox, sample_ripe_rewards):
    """Test getting deposit points bundle."""
    vault_id = 1
    asset = alice  # using alice as mock asset address
    
    # Set up points
    user_points = (1000 * EIGHTEEN_DECIMALS, 500 * EIGHTEEN_DECIMALS, 2000)
    asset_points = (
        2000 * EIGHTEEN_DECIMALS, 1000 * EIGHTEEN_DECIMALS, 800 * EIGHTEEN_DECIMALS,
        500 * EIGHTEEN_DECIMALS, 300 * EIGHTEEN_DECIMALS, 200 * EIGHTEEN_DECIMALS,
        2000, EIGHTEEN_DECIMALS
    )
    global_points = (5000 * EIGHTEEN_DECIMALS, 1500 * EIGHTEEN_DECIMALS, 1200 * EIGHTEEN_DECIMALS, 1000 * EIGHTEEN_DECIMALS, 2000)
    
    ledger.setDepositPointsAndRipeRewards(
        alice, vault_id, asset, user_points, asset_points, global_points, sample_ripe_rewards,
        sender=lootbox.address
    )
    
    bundle = ledger.getDepositPointsBundle(alice, vault_id, asset)
    
    assert bundle.userPoints.balancePoints == user_points[0]
    assert bundle.assetPoints.balancePoints == asset_points[0]
    assert bundle.globalPoints.lastUsdValue == global_points[0]

def test_ledger_get_deposit_points_bundle_empty_user(ledger):
    """Test getting deposit points bundle with empty user address."""
    vault_id = 1
    asset = ZERO_ADDRESS
    
    bundle = ledger.getDepositPointsBundle(ZERO_ADDRESS, vault_id, asset)
    
    # User points should be empty
    assert bundle.userPoints.balancePoints == 0
    assert bundle.userPoints.lastBalance == 0
    assert bundle.userPoints.lastUpdate == 0

##################
# Auction Tests  #
##################

def test_ledger_create_new_fungible_auction(ledger, alice, auction_house, sample_fungible_auction):
    """Test creating a new fungible auction."""
    # Initially no auctions
    assert not ledger.hasFungibleAuctions(alice)
    assert ledger.numFungibleAuctions(alice) == 0
    assert ledger.numFungLiqUsers() == 0
    
    # Create auction
    aid = ledger.createNewFungibleAuction(sample_fungible_auction, sender=auction_house.address)
    
    assert aid == 1
    assert ledger.hasFungibleAuctions(alice)
    assert ledger.numFungibleAuctions(alice) == 2  # 1-based indexing
    assert ledger.numFungLiqUsers() == 2  # 1-based indexing
    
    # Check auction details
    auction = ledger.fungibleAuctions(alice, 1)
    assert auction.liqUser == sample_fungible_auction[0]
    assert auction.vaultId == sample_fungible_auction[1]
    assert auction.asset == sample_fungible_auction[2]
    assert auction.isActive == sample_fungible_auction[7]
    
    # Check indexing
    vault_id = sample_fungible_auction[1]
    asset = sample_fungible_auction[2]
    assert ledger.fungibleAuctionIndex(alice, vault_id, asset) == 1
    assert ledger.hasFungibleAuction(alice, vault_id, asset)

def test_ledger_create_fungible_auction_duplicate_fails_gracefully(ledger, alice, auction_house, sample_fungible_auction):
    """Test creating duplicate auction fails gracefully."""
    # Create first auction
    aid1 = ledger.createNewFungibleAuction(sample_fungible_auction, sender=auction_house.address)
    assert aid1 == 1
    
    # Try to create duplicate
    aid2 = ledger.createNewFungibleAuction(sample_fungible_auction, sender=auction_house.address)
    assert aid2 == 0  # should return 0 for duplicate
    
    # Check only one auction exists
    assert ledger.numFungibleAuctions(alice) == 2  # 1-based, so 1 auction

def test_ledger_create_multiple_fungible_auctions(ledger, alice, auction_house, sample_fungible_auction):
    """Test creating multiple fungible auctions for same user."""
    vault_id_1 = 1
    vault_id_2 = 2
    asset_1 = alice
    asset_2 = alice
    
    # Create first auction
    auction_1 = (alice, vault_id_1, asset_1, 10_00, 50_00, 1000, 2000, True)
    aid1 = ledger.createNewFungibleAuction(auction_1, sender=auction_house.address)
    
    # Create second auction
    auction_2 = (alice, vault_id_2, asset_2, 15_00, 60_00, 1100, 2100, True)
    aid2 = ledger.createNewFungibleAuction(auction_2, sender=auction_house.address)
    
    assert aid1 == 1
    assert aid2 == 2
    assert ledger.numFungibleAuctions(alice) == 3  # 1-based, so 2 auctions
    
    # Check both auctions exist
    assert ledger.hasFungibleAuction(alice, vault_id_1, asset_1)
    assert ledger.hasFungibleAuction(alice, vault_id_2, asset_2)

def test_ledger_remove_fungible_auction(ledger, alice, auction_house, sample_fungible_auction):
    """Test removing a fungible auction."""
    # Create auction first
    ledger.createNewFungibleAuction(sample_fungible_auction, sender=auction_house.address)
    
    vault_id = sample_fungible_auction[1]
    asset = sample_fungible_auction[2]
    
    assert ledger.hasFungibleAuction(alice, vault_id, asset)
    
    # Remove auction
    ledger.removeFungibleAuction(alice, vault_id, asset, sender=auction_house.address)
    
    # Check auction is removed
    assert not ledger.hasFungibleAuction(alice, vault_id, asset)
    assert not ledger.hasFungibleAuctions(alice)
    assert ledger.numFungibleAuctions(alice) == 0

def test_ledger_remove_fungible_auction_middle(ledger, alice, auction_house):
    """Test removing auction from middle of list."""
    # Create three auctions
    auction_1 = (alice, 1, alice, 10_00, 50_00, 1000, 2000, True)
    auction_2 = (alice, 2, alice, 15_00, 60_00, 1100, 2100, True)
    auction_3 = (alice, 3, alice, 20_00, 70_00, 1200, 2200, True)
    
    ledger.createNewFungibleAuction(auction_1, sender=auction_house.address)
    ledger.createNewFungibleAuction(auction_2, sender=auction_house.address)
    ledger.createNewFungibleAuction(auction_3, sender=auction_house.address)
    
    # Remove middle auction
    ledger.removeFungibleAuction(alice, 2, alice, sender=auction_house.address)
    
    # Check auction 3 moved to position 2
    assert ledger.numFungibleAuctions(alice) == 3  # 1-based, so 2 auctions
    assert ledger.hasFungibleAuction(alice, 1, alice)
    assert not ledger.hasFungibleAuction(alice, 2, alice)
    assert ledger.hasFungibleAuction(alice, 3, alice)
    
    # Check auction 3 moved to index 2
    assert ledger.fungibleAuctionIndex(alice, 3, alice) == 2

def test_ledger_remove_fungible_auction_nonexistent(ledger, alice, auction_house):
    """Test removing non-existent auction fails gracefully."""
    # Try to remove from empty list
    ledger.removeFungibleAuction(alice, 999, alice, sender=auction_house.address)
    
    # Should not cause issues
    assert not ledger.hasFungibleAuctions(alice)

def test_ledger_set_fungible_auction(ledger, alice, auction_house, sample_fungible_auction):
    """Test updating an existing fungible auction."""
    # Create auction first
    ledger.createNewFungibleAuction(sample_fungible_auction, sender=auction_house.address)
    
    vault_id = sample_fungible_auction[1]
    asset = sample_fungible_auction[2]
    
    # Update auction
    updated_auction = (alice, vault_id, asset, 25_00, 80_00, 1500, 2500, False)
    success = ledger.setFungibleAuction(alice, vault_id, asset, updated_auction, sender=auction_house.address)
    
    assert success
    
    # Check auction was updated
    stored_auction = ledger.fungibleAuctions(alice, 1)
    assert stored_auction.startDiscount == 25_00
    assert stored_auction.maxDiscount == 80_00
    assert not stored_auction.isActive

def test_ledger_set_fungible_auction_nonexistent(ledger, alice, auction_house):
    """Test updating non-existent auction returns False."""
    updated_auction = (alice, 999, alice, 25_00, 80_00, 1500, 2500, False)
    success = ledger.setFungibleAuction(alice, 999, alice, updated_auction, sender=auction_house.address)
    
    assert not success

def test_ledger_remove_all_fungible_auctions(ledger, alice, auction_house, credit_engine):
    """Test removing all fungible auctions."""
    # Create multiple auctions
    auction_1 = (alice, 1, alice, 10_00, 50_00, 1000, 2000, True)
    auction_2 = (alice, 2, alice, 15_00, 60_00, 1100, 2100, True)
    auction_3 = (alice, 3, alice, 20_00, 70_00, 1200, 2200, True)
    
    ledger.createNewFungibleAuction(auction_1, sender=auction_house.address)
    ledger.createNewFungibleAuction(auction_2, sender=auction_house.address)
    ledger.createNewFungibleAuction(auction_3, sender=auction_house.address)
    
    assert ledger.numFungibleAuctions(alice) == 4  # 1-based, so 3 auctions
    
    # Remove all auctions via CreditEngine
    ledger.removeAllFungibleAuctions(alice, sender=credit_engine.address)
    
    # Check all auctions removed
    assert ledger.numFungibleAuctions(alice) == 0
    assert not ledger.hasFungibleAuctions(alice)
    assert not ledger.hasFungibleAuction(alice, 1, alice)
    assert not ledger.hasFungibleAuction(alice, 2, alice)
    assert not ledger.hasFungibleAuction(alice, 3, alice)

def test_ledger_get_fungible_auction(ledger, alice, auction_house, sample_fungible_auction):
    """Test getting fungible auction details."""
    # Create auction
    ledger.createNewFungibleAuction(sample_fungible_auction, sender=auction_house.address)
    
    vault_id = sample_fungible_auction[1]
    asset = sample_fungible_auction[2]
    
    # Get auction
    auction = ledger.getFungibleAuction(alice, vault_id, asset)
    
    assert auction.liqUser == sample_fungible_auction[0]
    assert auction.vaultId == sample_fungible_auction[1]
    assert auction.asset == sample_fungible_auction[2]
    assert auction.startDiscount == sample_fungible_auction[3]
    assert auction.maxDiscount == sample_fungible_auction[4]
    assert auction.isActive == sample_fungible_auction[7]

def test_ledger_get_fungible_auction_during_purchase(ledger, alice, auction_house, credit_engine, sample_fungible_auction):
    """Test getting auction during purchase (requires liquidation state)."""
    vault_id = sample_fungible_auction[1]
    asset = sample_fungible_auction[2]
    
    # Create auction
    ledger.createNewFungibleAuction(sample_fungible_auction, sender=auction_house.address)
    
    # Without liquidation state, should return empty auction
    auction = ledger.getFungibleAuctionDuringPurchase(alice, vault_id, asset)
    assert auction.liqUser == ZERO_ADDRESS
    
    # Set user in liquidation
    debt_in_liq = (1000 * EIGHTEEN_DECIMALS, 800 * EIGHTEEN_DECIMALS, (50_00, 60_00, 70_00, 10_00, 5_00, 0), 1000, True)
    interval = (1000, 500 * EIGHTEEN_DECIMALS)
    ledger.setUserDebt(alice, debt_in_liq, 0, interval, sender=credit_engine.address)
    
    # Now should return the auction
    auction = ledger.getFungibleAuctionDuringPurchase(alice, vault_id, asset)
    assert auction.liqUser == alice
    assert auction.vaultId == vault_id

def test_ledger_auction_unauthorized_calls(ledger, alice, bob, sample_fungible_auction):
    """Test that only authorized contracts can manage auctions."""
    vault_id = sample_fungible_auction[1]
    asset = sample_fungible_auction[2]
    
    with boa.reverts("only AuctionHouse allowed"):
        ledger.createNewFungibleAuction(sample_fungible_auction, sender=bob)
    
    with boa.reverts("only AuctionHouse allowed"):
        ledger.removeFungibleAuction(alice, vault_id, asset, sender=bob)
    
    with boa.reverts("only AuctionHouse allowed"):
        ledger.setFungibleAuction(alice, vault_id, asset, sample_fungible_auction, sender=bob)
    
    with boa.reverts("only AuctionHouse or CreditEngine allowed"):
        ledger.removeAllFungibleAuctions(alice, sender=bob)

#########################
# Human Resources Tests #
#########################

def test_ledger_add_hr_contributor(ledger, alice, human_resources):
    """Test adding HR contributor."""
    compensation = 1000 * EIGHTEEN_DECIMALS
    initial_avail = ledger.ripeAvailForHr()
    
    # Initially not a contributor
    assert not ledger.isHrContributor(alice)
    assert ledger.numContributors() == 0
    
    # Add contributor
    ledger.addHrContributor(alice, compensation, sender=human_resources.address)
    
    # Check contributor was added
    assert ledger.isHrContributor(alice)
    assert ledger.numContributors() == 2  # 1-based indexing
    assert ledger.contributors(1) == alice
    assert ledger.indexOfContributor(alice) == 1
    
    # Check compensation was deducted
    expected_avail = initial_avail - compensation
    assert ledger.ripeAvailForHr() == expected_avail

def test_ledger_add_hr_contributor_duplicate(ledger, alice, human_resources):
    """Test adding duplicate HR contributor fails gracefully."""
    compensation = 1000 * EIGHTEEN_DECIMALS
    
    # Add contributor first time
    ledger.addHrContributor(alice, compensation, sender=human_resources.address)
    initial_count = ledger.numContributors()
    initial_avail = ledger.ripeAvailForHr()
    
    # Try to add again
    ledger.addHrContributor(alice, compensation, sender=human_resources.address)
    
    # Should not change anything
    assert ledger.numContributors() == initial_count
    assert ledger.ripeAvailForHr() == initial_avail

def test_ledger_add_hr_contributor_unauthorized(ledger, alice, bob):
    """Test that only HumanResources can add contributors."""
    compensation = 1000 * EIGHTEEN_DECIMALS
    
    with boa.reverts("only hr allowed"):
        ledger.addHrContributor(alice, compensation, sender=bob)

def test_ledger_set_ripe_avail_for_hr(ledger, switchboard_alpha, human_resources):
    """Test setting RIPE available for HR."""
    new_amount = 5000 * EIGHTEEN_DECIMALS
    
    # Test via Switchboard
    ledger.setRipeAvailForHr(new_amount, sender=switchboard_alpha.address)
    assert ledger.ripeAvailForHr() == new_amount
    
    # Test via HumanResources
    new_amount_2 = 3000 * EIGHTEEN_DECIMALS
    ledger.setRipeAvailForHr(new_amount_2, sender=human_resources.address)
    assert ledger.ripeAvailForHr() == new_amount_2

def test_ledger_set_ripe_avail_for_hr_unauthorized(ledger, alice):
    """Test that only authorized contracts can set HR RIPE."""
    new_amount = 5000 * EIGHTEEN_DECIMALS
    
    with boa.reverts("no perms"):
        ledger.setRipeAvailForHr(new_amount, sender=alice)

##############
# Bond Tests #
##############

def test_ledger_get_epoch_data(ledger):
    """Test getting epoch data."""
    start, end = ledger.getEpochData()
    assert start == ledger.epochStart()
    assert end == ledger.epochEnd()

def test_ledger_get_ripe_bond_data(ledger):
    """Test getting RIPE bond data."""
    data = ledger.getRipeBondData()
    assert data.paymentAmountAvailInEpoch == ledger.paymentAmountAvailInEpoch()
    assert data.ripeAvailForBonds == ledger.ripeAvailForBonds()
    assert data.badDebt == ledger.badDebt()

def test_ledger_set_ripe_avail_for_bonds(ledger, switchboard_alpha):
    """Test setting RIPE available for bonds."""
    new_amount = 10000 * EIGHTEEN_DECIMALS
    
    ledger.setRipeAvailForBonds(new_amount, sender=switchboard_alpha.address)
    assert ledger.ripeAvailForBonds() == new_amount

def test_ledger_set_ripe_avail_for_bonds_unauthorized(ledger, alice):
    """Test that only Switchboard can set RIPE for bonds."""
    new_amount = 10000 * EIGHTEEN_DECIMALS
    
    with boa.reverts("no perms"):
        ledger.setRipeAvailForBonds(new_amount, sender=alice)

def test_ledger_set_bad_debt(ledger, switchboard_alpha):
    """Test setting bad debt."""
    bad_debt_amount = 5000 * EIGHTEEN_DECIMALS
    
    ledger.setBadDebt(bad_debt_amount, sender=switchboard_alpha.address)
    assert ledger.badDebt() == bad_debt_amount

def test_ledger_set_bad_debt_unauthorized(ledger, alice):
    """Test that only Switchboard can set bad debt."""
    bad_debt_amount = 5000 * EIGHTEEN_DECIMALS
    
    with boa.reverts("no perms"):
        ledger.setBadDebt(bad_debt_amount, sender=alice)

def test_ledger_did_clear_bad_debt(ledger, bond_room, switchboard_alpha):
    """Test clearing bad debt."""
    # Set initial bad debt
    initial_bad_debt = 5000 * EIGHTEEN_DECIMALS
    ledger.setBadDebt(initial_bad_debt, sender=switchboard_alpha.address)
    
    # Clear some bad debt
    cleared_amount = 2000 * EIGHTEEN_DECIMALS
    ripe_amount = 500 * EIGHTEEN_DECIMALS
    
    ledger.didClearBadDebt(cleared_amount, ripe_amount, sender=bond_room.address)
    
    # Check bad debt was reduced and RIPE tracking updated
    assert ledger.badDebt() == initial_bad_debt - cleared_amount
    assert ledger.ripePaidOutForBadDebt() == ripe_amount

def test_ledger_did_clear_bad_debt_unauthorized(ledger, alice):
    """Test that only BondRoom can clear bad debt."""
    cleared_amount = 2000 * EIGHTEEN_DECIMALS
    ripe_amount = 500 * EIGHTEEN_DECIMALS
    
    with boa.reverts("no perms"):
        ledger.didClearBadDebt(cleared_amount, ripe_amount, sender=alice)

def test_ledger_did_purchase_ripe_bond(ledger, bond_room, switchboard_alpha):
    """Test tracking RIPE bond purchases."""
    # Set initial values
    initial_payment_avail = 10000 * EIGHTEEN_DECIMALS
    initial_ripe_avail = 5000 * EIGHTEEN_DECIMALS
    
    ledger.setEpochData(1000, 2000, initial_payment_avail, sender=bond_room.address)
    ledger.setRipeAvailForBonds(initial_ripe_avail, sender=switchboard_alpha.address)
    
    # Purchase bond
    amount_paid = 1000 * EIGHTEEN_DECIMALS
    ripe_payout = 200 * EIGHTEEN_DECIMALS
    
    ledger.didPurchaseRipeBond(amount_paid, ripe_payout, sender=bond_room.address)
    
    # Check values were updated
    assert ledger.paymentAmountAvailInEpoch() == initial_payment_avail - amount_paid
    assert ledger.ripeAvailForBonds() == initial_ripe_avail - ripe_payout

def test_ledger_did_purchase_ripe_bond_no_payout(ledger, bond_room, switchboard_alpha):
    """Test bond purchase with zero RIPE payout."""
    initial_payment_avail = 10000 * EIGHTEEN_DECIMALS
    initial_ripe_avail = 5000 * EIGHTEEN_DECIMALS
    
    ledger.setEpochData(1000, 2000, initial_payment_avail, sender=bond_room.address)
    ledger.setRipeAvailForBonds(initial_ripe_avail, sender=switchboard_alpha.address)
    
    # Purchase bond with no RIPE payout
    amount_paid = 1000 * EIGHTEEN_DECIMALS
    ripe_payout = 0
    
    ledger.didPurchaseRipeBond(amount_paid, ripe_payout, sender=bond_room.address)
    
    # Payment should be deducted but RIPE should remain unchanged
    assert ledger.paymentAmountAvailInEpoch() == initial_payment_avail - amount_paid
    assert ledger.ripeAvailForBonds() == initial_ripe_avail

def test_ledger_did_purchase_ripe_bond_unauthorized(ledger, alice):
    """Test that only BondRoom can track bond purchases."""
    amount_paid = 1000 * EIGHTEEN_DECIMALS
    ripe_payout = 200 * EIGHTEEN_DECIMALS
    
    with boa.reverts("no perms"):
        ledger.didPurchaseRipeBond(amount_paid, ripe_payout, sender=alice)

def test_ledger_set_epoch_data(ledger, bond_room):
    """Test setting epoch data."""
    epoch_start = 1000
    epoch_end = 2000
    amount_avail = 15000 * EIGHTEEN_DECIMALS
    
    ledger.setEpochData(epoch_start, epoch_end, amount_avail, sender=bond_room.address)
    
    assert ledger.epochStart() == epoch_start
    assert ledger.epochEnd() == epoch_end
    assert ledger.paymentAmountAvailInEpoch() == amount_avail

def test_ledger_set_epoch_data_unauthorized(ledger, alice):
    """Test that only BondRoom can set epoch data."""
    epoch_start = 1000
    epoch_end = 2000
    amount_avail = 15000 * EIGHTEEN_DECIMALS
    
    with boa.reverts("no perms"):
        ledger.setEpochData(epoch_start, epoch_end, amount_avail, sender=alice)

###################
# Endaoment Tests #
###################

def test_ledger_update_green_pool_debt_increment(ledger, alice, endaoment):
    """Test incrementing green pool debt."""
    pool_address = alice
    debt_amount = 1000 * EIGHTEEN_DECIMALS
    
    # Initially no debt
    assert ledger.greenPoolDebt(pool_address) == 0
    
    # Increment debt
    ledger.updateGreenPoolDebt(pool_address, debt_amount, True, sender=endaoment.address)
    
    assert ledger.greenPoolDebt(pool_address) == debt_amount
    
    # Increment again
    additional_debt = 500 * EIGHTEEN_DECIMALS
    ledger.updateGreenPoolDebt(pool_address, additional_debt, True, sender=endaoment.address)
    
    assert ledger.greenPoolDebt(pool_address) == debt_amount + additional_debt

def test_ledger_update_green_pool_debt_decrement(ledger, alice, endaoment):
    """Test decrementing green pool debt."""
    pool_address = alice
    initial_debt = 1000 * EIGHTEEN_DECIMALS
    
    # Set initial debt
    ledger.updateGreenPoolDebt(pool_address, initial_debt, True, sender=endaoment.address)
    
    # Decrement debt
    repay_amount = 300 * EIGHTEEN_DECIMALS
    ledger.updateGreenPoolDebt(pool_address, repay_amount, False, sender=endaoment.address)
    
    assert ledger.greenPoolDebt(pool_address) == initial_debt - repay_amount

def test_ledger_update_green_pool_debt_decrement_more_than_available(ledger, alice, endaoment):
    """Test decrementing more debt than available."""
    pool_address = alice
    initial_debt = 1000 * EIGHTEEN_DECIMALS
    
    # Set initial debt
    ledger.updateGreenPoolDebt(pool_address, initial_debt, True, sender=endaoment.address)
    
    # Try to decrement more than available
    excessive_repay = 1500 * EIGHTEEN_DECIMALS
    ledger.updateGreenPoolDebt(pool_address, excessive_repay, False, sender=endaoment.address)
    
    # Should reduce to zero, not go negative
    assert ledger.greenPoolDebt(pool_address) == 0

def test_ledger_update_green_pool_debt_unauthorized(ledger, alice, bob):
    """Test that only Endaoment can update green pool debt."""
    pool_address = alice
    debt_amount = 1000 * EIGHTEEN_DECIMALS
    
    with boa.reverts("no perms"):
        ledger.updateGreenPoolDebt(pool_address, debt_amount, True, sender=bob)

#########################
# DeptBasics Inherited  #
#########################

def test_ledger_can_mint_green(ledger):
    """Test that Ledger cannot mint GREEN tokens."""
    assert not ledger.canMintGreen()

def test_ledger_can_mint_ripe(ledger):
    """Test that Ledger cannot mint RIPE tokens."""
    assert not ledger.canMintRipe()

def test_ledger_recover_funds(ledger, switchboard_alpha, alice, alpha_token, governance):
    """Test fund recovery functionality."""
    # Setup: send some tokens to the ledger
    initial_balance = 1000 * EIGHTEEN_DECIMALS
    alpha_token.mint(alice, initial_balance, sender=governance.address)
    alpha_token.transfer(ledger.address, initial_balance, sender=alice)
    
    # Check initial state
    assert alpha_token.balanceOf(ledger.address) == initial_balance
    initial_alice_balance = alpha_token.balanceOf(alice)
    
    # Recover funds
    ledger.recoverFunds(alice, alpha_token.address, sender=switchboard_alpha.address)
    
    # Check funds were recovered
    assert alpha_token.balanceOf(ledger.address) == 0
    assert alpha_token.balanceOf(alice) == initial_alice_balance + initial_balance

def test_ledger_recover_funds_many(ledger, switchboard_alpha, alice, alpha_token, green_token, governance, whale):
    """Test recovery of multiple assets."""
    # Setup: send tokens to the ledger
    erc20_amount = 1000 * EIGHTEEN_DECIMALS
    green_amount = 500 * EIGHTEEN_DECIMALS
    
    alpha_token.mint(alice, erc20_amount, sender=governance.address)
    alpha_token.transfer(ledger.address, erc20_amount, sender=alice)
    green_token.transfer(ledger.address, green_amount, sender=whale)
    
    # Check initial state
    assert alpha_token.balanceOf(ledger.address) == erc20_amount
    assert green_token.balanceOf(ledger.address) == green_amount
    
    initial_alice_alpha = alpha_token.balanceOf(alice)
    initial_alice_green = green_token.balanceOf(alice)
    
    # Recover multiple assets
    assets = [alpha_token.address, green_token.address]
    ledger.recoverFundsMany(alice, assets, sender=switchboard_alpha.address)
    
    # Check all funds were recovered
    assert alpha_token.balanceOf(ledger.address) == 0
    assert green_token.balanceOf(ledger.address) == 0
    assert alpha_token.balanceOf(alice) == initial_alice_alpha + erc20_amount
    assert green_token.balanceOf(alice) == initial_alice_green + green_amount

def test_ledger_recover_funds_unauthorized(ledger, alice, alpha_token):
    """Test that only Switchboard can recover funds."""
    with boa.reverts("no perms"):
        ledger.recoverFunds(alice, alpha_token.address, sender=alice)

def test_ledger_recover_funds_many_unauthorized(ledger, alice, alpha_token):
    """Test that only Switchboard can recover multiple funds."""
    assets = [alpha_token.address]
    with boa.reverts("no perms"):
        ledger.recoverFundsMany(alice, assets, sender=alice)

def test_ledger_recover_funds_zero_balance(ledger, switchboard_alpha, alice, alpha_token):
    """Test that recovery fails when no balance exists."""
    # Ensure ledger has no balance
    assert alpha_token.balanceOf(ledger.address) == 0
    
    with boa.reverts("nothing to recover"):
        ledger.recoverFunds(alice, alpha_token.address, sender=switchboard_alpha.address)

def test_ledger_recover_funds_empty_recipient(ledger, switchboard_alpha, alpha_token):
    """Test that recovery fails with empty recipient."""
    with boa.reverts("invalid recipient or asset"):
        ledger.recoverFunds(ZERO_ADDRESS, alpha_token.address, sender=switchboard_alpha.address)

def test_ledger_recover_funds_empty_asset(ledger, switchboard_alpha, alice):
    """Test that recovery fails with empty asset."""
    with boa.reverts("invalid recipient or asset"):
        ledger.recoverFunds(alice, ZERO_ADDRESS, sender=switchboard_alpha.address)

#############################
# Authorized Callers Tests #
#############################

def test_ledger_add_vault_all_authorized_callers(ledger, alice, teller, credit_engine, auction_house, human_resources):
    """Test that all authorized contracts can call addVaultToUser."""
    vault_id_1 = 1
    vault_id_2 = 2
    vault_id_3 = 3
    vault_id_4 = 4
    
    # Test Teller
    ledger.addVaultToUser(alice, vault_id_1, sender=teller.address)
    assert ledger.isParticipatingInVault(alice, vault_id_1)
    
    # Test CreditEngine  
    ledger.addVaultToUser(alice, vault_id_2, sender=credit_engine.address)
    assert ledger.isParticipatingInVault(alice, vault_id_2)
    
    # Test AuctionHouse
    ledger.addVaultToUser(alice, vault_id_3, sender=auction_house.address)
    assert ledger.isParticipatingInVault(alice, vault_id_3)
    
    # Test HumanResources
    ledger.addVaultToUser(alice, vault_id_4, sender=human_resources.address)
    assert ledger.isParticipatingInVault(alice, vault_id_4)

#######################
# Comprehensive Pause #
#######################

def test_ledger_all_functions_paused(ledger, switchboard_alpha, alice, teller, lootbox, credit_engine, auction_house, 
                                   human_resources, vault_book, bond_room, endaoment, sample_user_debt, 
                                   sample_ripe_rewards, sample_fungible_auction):
    """Test that all external functions respect pause state."""
    # Pause the contract
    ledger.pause(True, sender=switchboard_alpha.address)
    
    # Test all external functions that should be paused
    vault_id = 1
    interval = (1000, 500 * EIGHTEEN_DECIMALS)
    
    # User Vaults
    with boa.reverts("not activated"):
        ledger.addVaultToUser(alice, vault_id, sender=teller.address)
    
    with boa.reverts("not activated"):
        ledger.removeVaultFromUser(alice, vault_id, sender=lootbox.address)
    
    # Debt
    with boa.reverts("not activated"):
        ledger.setUserDebt(alice, sample_user_debt, 0, interval, sender=credit_engine.address)
    
    with boa.reverts("not activated"):
        ledger.flushUnrealizedYield(sender=credit_engine.address)
    
    # Rewards
    with boa.reverts("not activated"):
        ledger.setRipeRewards(sample_ripe_rewards, sender=lootbox.address)
    
    with boa.reverts("not activated"):
        ledger.setRipeAvailForRewards(1000, sender=switchboard_alpha.address)
    
    with boa.reverts("not activated"):
        ledger.didGetRewardsFromStabClaims(100, sender=vault_book.address)
    
    # Points
    user_points = (1000 * EIGHTEEN_DECIMALS, 500 * EIGHTEEN_DECIMALS, 2000)
    asset_points = (2000 * EIGHTEEN_DECIMALS, 1000 * EIGHTEEN_DECIMALS, 800 * EIGHTEEN_DECIMALS, 
                   500 * EIGHTEEN_DECIMALS, 300 * EIGHTEEN_DECIMALS, 200 * EIGHTEEN_DECIMALS, 
                   2000, EIGHTEEN_DECIMALS)
    global_points = (5000 * EIGHTEEN_DECIMALS, 1500 * EIGHTEEN_DECIMALS, 1200 * EIGHTEEN_DECIMALS, 
                    1000 * EIGHTEEN_DECIMALS, 2000)
    
    with boa.reverts("not activated"):
        ledger.setDepositPointsAndRipeRewards(alice, vault_id, alice, user_points, asset_points, 
                                            global_points, sample_ripe_rewards, sender=lootbox.address)
    
    borrow_user_points = (800 * EIGHTEEN_DECIMALS, 1000 * EIGHTEEN_DECIMALS, 2000)
    borrow_global_points = (1500 * EIGHTEEN_DECIMALS, 5000 * EIGHTEEN_DECIMALS, 2000)
    
    with boa.reverts("not activated"):
        ledger.setBorrowPointsAndRipeRewards(alice, borrow_user_points, borrow_global_points, 
                                           sample_ripe_rewards, sender=lootbox.address)
    
    # Auctions
    with boa.reverts("not activated"):
        ledger.createNewFungibleAuction(sample_fungible_auction, sender=auction_house.address)
    
    with boa.reverts("not activated"):
        ledger.removeFungibleAuction(alice, vault_id, alice, sender=auction_house.address)
    
    with boa.reverts("not activated"):
        ledger.setFungibleAuction(alice, vault_id, alice, sample_fungible_auction, sender=auction_house.address)
    
    with boa.reverts("not activated"):
        ledger.removeAllFungibleAuctions(alice, sender=auction_house.address)
    
    # HR
    with boa.reverts("not activated"):
        ledger.addHrContributor(alice, 1000, sender=human_resources.address)
    
    with boa.reverts("not activated"):
        ledger.setRipeAvailForHr(5000, sender=switchboard_alpha.address)
    
    # Bonds
    with boa.reverts("not activated"):
        ledger.setRipeAvailForBonds(10000, sender=switchboard_alpha.address)
    
    with boa.reverts("not activated"):
        ledger.setBadDebt(5000, sender=switchboard_alpha.address)
    
    with boa.reverts("not activated"):
        ledger.didClearBadDebt(1000, 200, sender=bond_room.address)
    
    with boa.reverts("not activated"):
        ledger.didPurchaseRipeBond(1000, 200, sender=bond_room.address)
    
    with boa.reverts("not activated"):
        ledger.setEpochData(1000, 2000, 15000, sender=bond_room.address)
    
    # Endaoment
    with boa.reverts("not activated"):
        ledger.updateGreenPoolDebt(alice, 1000, True, sender=endaoment.address)

######################
# Edge Cases & Limits #
######################

def test_ledger_set_ripe_rewards_insufficient_available(ledger, lootbox, switchboard_alpha):
    """Test setting RIPE rewards when insufficient available."""
    # Set low available amount
    initial_avail = 100 * EIGHTEEN_DECIMALS
    ledger.setRipeAvailForRewards(initial_avail, sender=switchboard_alpha.address)
    
    # Try to set rewards higher than available
    large_rewards = (
        500 * EIGHTEEN_DECIMALS,  # borrowers
        200 * EIGHTEEN_DECIMALS,  # stakers  
        150 * EIGHTEEN_DECIMALS,  # voters
        250 * EIGHTEEN_DECIMALS,  # genDepositors
        1000 * EIGHTEEN_DECIMALS, # newRipeRewards (much larger than available)
        2000  # lastUpdate
    )
    
    ledger.setRipeRewards(large_rewards, sender=lootbox.address)
    
    # Should reduce available to 0, not go negative
    assert ledger.ripeAvailForRewards() == 0

def test_ledger_did_clear_bad_debt_more_than_exists(ledger, bond_room, switchboard_alpha):
    """Test that clearing more bad debt than exists reverts (secure behavior)."""
    # Set initial bad debt
    initial_bad_debt = 1000 * EIGHTEEN_DECIMALS
    ledger.setBadDebt(initial_bad_debt, sender=switchboard_alpha.address)
    
    # Try to clear more than exists - should revert due to safesub
    excessive_clear = 2000 * EIGHTEEN_DECIMALS
    ripe_amount = 500 * EIGHTEEN_DECIMALS
    
    with boa.reverts():  # safesub will cause revert
        ledger.didClearBadDebt(excessive_clear, ripe_amount, sender=bond_room.address)
    
    # Bad debt should remain unchanged
    assert ledger.badDebt() == initial_bad_debt
    assert ledger.ripePaidOutForBadDebt() == 0

def test_ledger_hr_contributor_compensation_exceeds_available(ledger, human_resources, alice, switchboard_alpha):
    """Test that adding HR contributor with excessive compensation reverts (secure behavior)."""
    # Set low available amount
    low_avail = 100 * EIGHTEEN_DECIMALS
    ledger.setRipeAvailForHr(low_avail, sender=switchboard_alpha.address)
    
    # Try to add contributor with higher compensation - should revert due to safesub
    high_compensation = 200 * EIGHTEEN_DECIMALS
    
    with boa.reverts():  # safesub will cause revert
        ledger.addHrContributor(alice, high_compensation, sender=human_resources.address)
    
    # Contributor should not be added and available RIPE unchanged
    assert not ledger.isHrContributor(alice)
    assert ledger.ripeAvailForHr() == low_avail

####################
# Boundary Testing #
####################

def test_ledger_max_user_vaults(ledger, alice, teller, lootbox):
    """Test behavior with many vaults."""
    # Add many vaults
    num_vaults = 20
    for i in range(1, num_vaults + 1):
        ledger.addVaultToUser(alice, i, sender=teller.address)
        assert ledger.isParticipatingInVault(alice, i)
        assert ledger.getNumUserVaults(alice) == i
    
    # Remove from middle and verify structure integrity
    middle_vault = num_vaults // 2
    ledger.removeVaultFromUser(alice, middle_vault, sender=lootbox.address)
    
    assert not ledger.isParticipatingInVault(alice, middle_vault)
    assert ledger.getNumUserVaults(alice) == num_vaults - 1

def test_ledger_auction_boundary_conditions(ledger, alice, auction_house):
    """Test auction creation with boundary values."""
    # Test auction with max discount values
    max_auction = (alice, 1, alice, 10000, 10000, 1000, 2000, True)  # 100% discounts
    aid = ledger.createNewFungibleAuction(max_auction, sender=auction_house.address)
    assert aid == 1
    
    auction = ledger.getFungibleAuction(alice, 1, alice)
    assert auction.startDiscount == 10000
    assert auction.maxDiscount == 10000

########################
# Edge Cases and Misc #
########################

def test_ledger_contract_pause_functionality(ledger, switchboard_alpha):
    """Test contract pause/unpause functionality."""
    # Initially not paused
    assert not ledger.isPaused()
    
    # Pause contract
    ledger.pause(True, sender=switchboard_alpha.address)
    assert ledger.isPaused()
    
    # Unpause contract
    ledger.pause(False, sender=switchboard_alpha.address)
    assert not ledger.isPaused()

def test_ledger_debt_liquidation_removes_auctions(ledger, alice, auction_house, credit_engine, sample_fungible_auction):
    """Test that exiting liquidation removes all auctions."""
    # Create auction
    ledger.createNewFungibleAuction(sample_fungible_auction, sender=auction_house.address)
    assert ledger.hasFungibleAuctions(alice)
    
    # Set user in liquidation
    debt_in_liq = (1000 * EIGHTEEN_DECIMALS, 800 * EIGHTEEN_DECIMALS, (50_00, 60_00, 70_00, 10_00, 5_00, 0), 1000, True)
    interval = (1000, 500 * EIGHTEEN_DECIMALS)
    ledger.setUserDebt(alice, debt_in_liq, 0, interval, sender=credit_engine.address)
    
    # Exit liquidation
    debt_no_liq = (1000 * EIGHTEEN_DECIMALS, 800 * EIGHTEEN_DECIMALS, (50_00, 60_00, 70_00, 10_00, 5_00, 0), 1000, False)
    ledger.setUserDebt(alice, debt_no_liq, 0, interval, sender=credit_engine.address)
    
    # Auctions should be removed
    assert not ledger.hasFungibleAuctions(alice)

def test_ledger_comprehensive_integration(ledger, alice, teller, credit_engine, lootbox, auction_house, sample_user_debt, sample_ripe_rewards):
    """Test comprehensive integration of all systems."""
    vault_id = 1
    
    # 1. Add user to vault
    ledger.addVaultToUser(alice, vault_id, sender=teller.address)
    assert ledger.isParticipatingInVault(alice, vault_id)
    
    # 2. Set user debt
    interval = (1000, 500 * EIGHTEEN_DECIMALS)
    ledger.setUserDebt(alice, sample_user_debt, 10 * EIGHTEEN_DECIMALS, interval, sender=credit_engine.address)
    assert ledger.hasDebt(alice)
    
    # 3. Set rewards and points
    user_points = (1000 * EIGHTEEN_DECIMALS, 500 * EIGHTEEN_DECIMALS, 2000)
    asset_points = (2000 * EIGHTEEN_DECIMALS, 1000 * EIGHTEEN_DECIMALS, 800 * EIGHTEEN_DECIMALS, 500 * EIGHTEEN_DECIMALS, 300 * EIGHTEEN_DECIMALS, 200 * EIGHTEEN_DECIMALS, 2000, EIGHTEEN_DECIMALS)
    global_points = (5000 * EIGHTEEN_DECIMALS, 1500 * EIGHTEEN_DECIMALS, 1200 * EIGHTEEN_DECIMALS, 1000 * EIGHTEEN_DECIMALS, 2000)
    
    ledger.setDepositPointsAndRipeRewards(alice, vault_id, alice, user_points, asset_points, global_points, sample_ripe_rewards, sender=lootbox.address)
    
    # 4. Create auction
    auction = (alice, vault_id, alice, 10_00, 50_00, 1000, 2000, True)
    ledger.createNewFungibleAuction(auction, sender=auction_house.address)
    assert ledger.hasFungibleAuctions(alice)
    
    # 5. Verify all data bundles work
    borrow_bundle = ledger.getBorrowDataBundle(alice)
    assert borrow_bundle.userDebt.amount == sample_user_debt[0]
    assert borrow_bundle.isUserBorrower
    
    deposit_bundle = ledger.getDepositPointsBundle(alice, vault_id, alice)
    assert deposit_bundle.userPoints.balancePoints == user_points[0]
    
    rewards_bundle = ledger.getRipeRewardsBundle()
    assert rewards_bundle.ripeRewards.borrowers == sample_ripe_rewards[0]
    
    # 6. Clear debt and verify cleanup
    no_debt = (0, 0, (0, 0, 0, 0, 0, 0), 0, False)
    empty_interval = (0, 0)
    ledger.setUserDebt(alice, no_debt, 0, empty_interval, sender=credit_engine.address)
    
    assert not ledger.hasDebt(alice)
    assert not ledger.isBorrower(alice)
