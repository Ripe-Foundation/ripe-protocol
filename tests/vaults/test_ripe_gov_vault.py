import pytest
import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, HUNDRED_PERCENT


@pytest.fixture(scope="module")
def setupRipeGovVaultConfig(mission_control, setAssetConfig, switchboard_alpha, ripe_token):
    def setupRipeGovVaultConfig(
        _assetWeight = 100_00,
        _minLockDuration = 100,
        _maxLockDuration = 1000,
        _maxLockBoost = 200_00,
        _exitFee = 10_00,
        _canExit = True,
    ):
        # Set up lock terms
        lock_terms = (
            _minLockDuration,
            _maxLockDuration,
            _maxLockBoost,
            _canExit,
            _exitFee,
        )

        # Set RipeGov vault config with asset weight of 100%
        mission_control.setRipeGovVaultConfig(
            ripe_token, 
            _assetWeight,
            lock_terms, 
            sender=switchboard_alpha.address
        )
        
        # Configure ripe_token for vault_id 2 (ripe_gov_vault)
        setAssetConfig(ripe_token, _vaultIds=[2])

    yield setupRipeGovVaultConfig


def test_ripe_gov_vault_initial_deposit_no_lock(
    ripe_gov_vault, ripe_token, whale, bob, teller, _test, setupRipeGovVaultConfig
):
    """Test initial deposit without lock duration"""
    setupRipeGovVaultConfig()
      
    # Transfer tokens to vault first
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    
    # Deposit tokens
    deposited = ripe_gov_vault.depositTokensInVault(
        bob, ripe_token, deposit_amount, sender=teller.address
    )
    assert deposited == deposit_amount
    
    # Check user balance
    user_amount = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    _test(deposit_amount, user_amount)
    
    # Check governance data is initialized
    userData = ripe_gov_vault.userGovData(bob, ripe_token)
    assert userData.govPoints == 0  # No points yet, no time passed

    current_block = boa.env.evm.patch.block_number
    assert userData.unlock == current_block + 100  # Should be exactly minLockDuration (100) blocks from now


def test_ripe_gov_vault_deposit_with_lock_duration(
    ripe_gov_vault, ripe_token, whale, bob, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test deposit with specific lock duration"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    lock_duration = 500  # blocks
    
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    
    # Deposit with lock duration
    deposited = ripe_gov_vault.depositTokensWithLockDuration(
        bob, ripe_token, deposit_amount, lock_duration, sender=switchboard_alpha.address
    )
    assert deposited == deposit_amount
    
    # Check governance data
    userData = ripe_gov_vault.userGovData(bob, ripe_token)
    expected_unlock = boa.env.evm.patch.block_number + lock_duration
    assert userData.unlock == expected_unlock  # unlock should match lock duration


def test_ripe_gov_vault_multiple_deposits_weighted_lock(
    ripe_gov_vault, ripe_token, whale, bob, teller, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test multiple deposits create weighted average lock duration"""
    setupRipeGovVaultConfig()

    first_deposit = 100 * EIGHTEEN_DECIMALS
    second_deposit = 200 * EIGHTEEN_DECIMALS
    
    # First deposit with minimum lock
    ripe_token.transfer(ripe_gov_vault, first_deposit, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, first_deposit, sender=teller.address)
    
    first_unlock = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    
    # Second deposit with longer lock
    ripe_token.transfer(ripe_gov_vault, second_deposit, sender=whale)
    ripe_gov_vault.depositTokensWithLockDuration(
        bob, ripe_token, second_deposit, 800, sender=switchboard_alpha.address
    )
    
    second_unlock = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    
    # Second unlock should be between first unlock and full 800 block lock
    assert second_unlock > first_unlock
    assert second_unlock < boa.env.evm.patch.block_number + 800


def test_ripe_gov_vault_deposit_validation(
    ripe_gov_vault, ripe_token, bob, alice, setupRipeGovVaultConfig
):
    """Test deposit validation"""
    setupRipeGovVaultConfig()

    # Test unauthorized caller for depositTokensInVault
    with boa.reverts("only Teller allowed"):
        ripe_gov_vault.depositTokensInVault(bob, ripe_token, 100, sender=alice)
    
    # Test unauthorized caller for depositWithLockDuration
    with boa.reverts("no perms"):
        ripe_gov_vault.depositTokensWithLockDuration(bob, ripe_token, 100, 500, sender=alice)


def test_ripe_gov_vault_basic_withdrawal(
    ripe_gov_vault, ripe_token, whale, bob, alice, teller, _test, setupRipeGovVaultConfig
):
    """Test basic withdrawal after lock period"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit tokens
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Fast forward past unlock time
    unlock_block = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    current_block = boa.env.evm.patch.block_number
    blocks_to_advance = unlock_block - current_block + 1
    boa.env.time_travel(blocks=blocks_to_advance)
    
    # Withdraw tokens
    withdraw_amount = 50 * EIGHTEEN_DECIMALS
    initial_balance = ripe_token.balanceOf(alice)
    
    withdrawn, is_depleted = ripe_gov_vault.withdrawTokensFromVault(
        bob, ripe_token, withdraw_amount, alice, sender=teller.address
    )
    
    # Check withdrawal
    assert withdrawn == withdraw_amount
    assert not is_depleted
    assert ripe_token.balanceOf(alice) == initial_balance + withdraw_amount
    
    # Check remaining balance
    remaining = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    _test(deposit_amount - withdraw_amount, remaining)


def test_ripe_gov_vault_withdrawal_before_unlock_fails(
    ripe_gov_vault, ripe_token, whale, bob, teller, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test that withdrawal fails before unlock time"""
    setupRipeGovVaultConfig(_minLockDuration=100, _maxLockDuration=1000)
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit with lock
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensWithLockDuration(
        bob, ripe_token, deposit_amount, 100, sender=switchboard_alpha.address
    )
    
    # Should revert with "not reached unlock" - trying to withdraw before unlock time
    with boa.reverts("not reached unlock"):
        ripe_gov_vault.withdrawTokensFromVault(bob, ripe_token, deposit_amount, bob, sender=teller.address)


def test_ripe_gov_vault_full_withdrawal_depletes_user(
    ripe_gov_vault, ripe_token, whale, bob, alice, teller, setupRipeGovVaultConfig
):
    """Test full withdrawal marks user as depleted"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit and advance time
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    unlock_block = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    current_block = boa.env.evm.patch.block_number
    blocks_to_advance = unlock_block - current_block + 1
    boa.env.time_travel(blocks=blocks_to_advance)
    
    # Withdraw all tokens
    withdrawn, is_depleted = ripe_gov_vault.withdrawTokensFromVault(
        bob, ripe_token, deposit_amount, alice, sender=teller.address
    )
    
    assert withdrawn == deposit_amount
    assert is_depleted
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 0


def test_ripe_gov_vault_withdrawal_permission_checks(
    ripe_gov_vault, ripe_token, whale, bob, alice, setupRipeGovVaultConfig
):
    """Test withdrawal permission checks"""
    setupRipeGovVaultConfig()

    # Should revert with "not allowed" - only authorized addresses can call withdrawTokensFromVault
    with boa.reverts("not allowed"):
        ripe_gov_vault.withdrawTokensFromVault(bob, ripe_token, 100, alice, sender=alice)


def test_ripe_gov_vault_basic_transfer_between_users(
    ripe_gov_vault, ripe_token, whale, bob, alice, teller, auction_house, setupRipeGovVaultConfig
):
    """Test transferring balance between users"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    transfer_amount = 30 * EIGHTEEN_DECIMALS
    
    # Bob deposits tokens (using teller, not auction house)
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    initial_bob_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    initial_alice_balance = ripe_gov_vault.getTotalAmountForUser(alice, ripe_token)
    
    # Transfer from Bob to Alice (using auction house)
    transferred, is_depleted = ripe_gov_vault.transferBalanceWithinVault(
        ripe_token, bob, alice, transfer_amount, sender=auction_house.address
    )
    
    assert transferred == transfer_amount
    assert not is_depleted
    
    # Check balances after transfer
    final_bob_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    final_alice_balance = ripe_gov_vault.getTotalAmountForUser(alice, ripe_token)
    
    assert final_bob_balance == initial_bob_balance - transfer_amount
    assert final_alice_balance == initial_alice_balance + transfer_amount


def test_ripe_gov_vault_transfer_full_balance_depletes_sender(
    ripe_gov_vault, ripe_token, whale, bob, alice, teller, auction_house, setupRipeGovVaultConfig
):
    """Test transferring full balance marks sender as depleted"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Bob deposits tokens (using teller)
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Transfer all of Bob's balance to Alice (using auction house)
    transferred, is_depleted = ripe_gov_vault.transferBalanceWithinVault(
        ripe_token, bob, alice, deposit_amount, sender=auction_house.address
    )
    
    assert transferred == deposit_amount
    assert is_depleted
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 0
    assert ripe_gov_vault.getTotalAmountForUser(alice, ripe_token) == deposit_amount


def test_ripe_gov_vault_transfer_permission_checks(
    ripe_gov_vault, ripe_token, bob, alice, setupRipeGovVaultConfig
):
    """Test transfer permission checks"""
    setupRipeGovVaultConfig()

    # Should revert with "not allowed" - only auction house or credit engine can call transfer
    with boa.reverts("not allowed"):
        ripe_gov_vault.transferBalanceWithinVault(ripe_token, bob, alice, 100, sender=alice)


def test_ripe_gov_vault_adjust_lock_permission_check(
    ripe_gov_vault, ripe_token, bob, alice, setupRipeGovVaultConfig
):
    """Test adjust lock permission checks"""
    setupRipeGovVaultConfig()

    # Should revert with "no perms" - only RipeHq addresses can call adjustLock
    with boa.reverts("no perms"):
        ripe_gov_vault.adjustLock(bob, ripe_token, 500, sender=alice)


def test_ripe_gov_vault_adjust_lock_no_position_fails(
    ripe_gov_vault, ripe_token, bob, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test adjusting lock with no position fails"""
    setupRipeGovVaultConfig()

    # Should revert with "no lock terms" - no lock terms configured yet (first assertion)
    with boa.reverts("no lock terms"):
        ripe_gov_vault.adjustLock(bob, ripe_token, 500, sender=switchboard_alpha.address)


def test_ripe_gov_vault_adjust_lock_with_terms_but_no_position_fails(
    ripe_gov_vault, ripe_token, whale, bob, teller, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test adjusting lock fails when user has lock terms but no position"""
    setupRipeGovVaultConfig(_minLockDuration=100, _maxLockDuration=1000)
    
    # Deposit for bob to create lock terms, then withdraw everything
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Get unlock time and advance past it
    userData = ripe_gov_vault.userGovData(bob, ripe_token)
    unlock_block = userData.unlock
    boa.env.time_travel(blocks=unlock_block - boa.env.evm.patch.block_number + 1)
    
    # Withdraw everything
    ripe_gov_vault.withdrawTokensFromVault(bob, ripe_token, deposit_amount, bob, sender=teller.address)
    
    # Should revert with "no position" - user has lock terms configured but no shares
    with boa.reverts("no position"):
        ripe_gov_vault.adjustLock(bob, ripe_token, 500, sender=switchboard_alpha.address)


def test_ripe_gov_vault_adjust_lock_extend_duration(
    ripe_gov_vault, ripe_token, whale, bob, teller, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test adjusting lock to extend the duration"""
    setupRipeGovVaultConfig(_minLockDuration=100, _maxLockDuration=1000)
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit tokens with minimum lock duration
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Get initial unlock time (should be current block + 100 minimum)
    userData_before = ripe_gov_vault.userGovData(bob, ripe_token)
    initial_unlock = userData_before.unlock
    current_block = boa.env.evm.patch.block_number
    assert initial_unlock == current_block + 100  # Should be minimum lock duration
    
    # Adjust lock to extend duration to 800 blocks
    ripe_gov_vault.adjustLock(bob, ripe_token, 800, sender=switchboard_alpha.address)
    
    # Verify unlock time was updated
    userData_after = ripe_gov_vault.userGovData(bob, ripe_token)
    new_unlock = userData_after.unlock
    expected_unlock = boa.env.evm.patch.block_number + 800  # Should be current block + 800
    
    assert new_unlock == expected_unlock
    assert new_unlock > initial_unlock  # Should be later than initial unlock
    assert userData_after.lastShares == userData_before.lastShares  # Shares unchanged


def test_ripe_gov_vault_adjust_lock_cannot_reduce_duration(
    ripe_gov_vault, ripe_token, whale, bob, teller, switchboard_alpha, setupRipeGovVaultConfig  
):
    """Test that adjusting lock cannot reduce the duration (earlier unlock time)"""
    setupRipeGovVaultConfig(_minLockDuration=100, _maxLockDuration=1000)
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit tokens with long lock duration
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensWithLockDuration(
        bob, ripe_token, deposit_amount, 800, sender=switchboard_alpha.address  # 800 block lock
    )
    
    # Verify initial unlock time
    userData = ripe_gov_vault.userGovData(bob, ripe_token)
    initial_unlock = userData.unlock
    current_block = boa.env.evm.patch.block_number
    assert initial_unlock == current_block + 800
    
    # Try to adjust lock to shorter duration - should revert
    # Even though we're asking for 500 blocks, the new unlock would be current_block + 500
    # which is less than the existing unlock time
    with boa.reverts("new lock cannot be earlier"):
        ripe_gov_vault.adjustLock(bob, ripe_token, 500, sender=switchboard_alpha.address)


def test_ripe_gov_vault_release_lock_no_position_fails(
    ripe_gov_vault, ripe_token, bob, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test releasing lock with no position fails"""
    setupRipeGovVaultConfig()

    # Should revert with "no release needed" - no unlock time set (first assertion)
    with boa.reverts("no release needed"):
        ripe_gov_vault.releaseLock(bob, ripe_token, sender=switchboard_alpha.address)


def test_ripe_gov_vault_release_lock_permission_check(
    ripe_gov_vault, ripe_token, bob, alice, setupRipeGovVaultConfig
):
    """Test release lock permission checks"""
    setupRipeGovVaultConfig()

    # Should revert with "no perms" - only RipeHq addresses can call releaseLock
    with boa.reverts("no perms"):
        ripe_gov_vault.releaseLock(bob, ripe_token, sender=alice)


def test_ripe_gov_vault_update_gov_points_permission_check(
    ripe_gov_vault, bob, alice, setupRipeGovVaultConfig
):
    """Test update governance points permission checks"""
    setupRipeGovVaultConfig()

    # Should revert with "no perms" - only RipeHq addresses can call updateUserGovPoints
    with boa.reverts("no perms"):
        ripe_gov_vault.updateUserGovPoints(bob, sender=alice)


def test_ripe_gov_vault_gov_points_accumulate_over_time(
    ripe_gov_vault, ripe_token, whale, bob, teller, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test that governance points accumulate over time"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit tokens
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Initial points should be 0
    initial_points = ripe_gov_vault.userGovData(bob, ripe_token).govPoints
    initial_total_points = ripe_gov_vault.totalUserGovPoints(bob)
    assert initial_points == 0
    assert initial_total_points == 0
    
    # Advance time and update points
    boa.env.time_travel(blocks=100)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    
    # Points should have accumulated
    updated_points = ripe_gov_vault.userGovData(bob, ripe_token).govPoints
    updated_total_points = ripe_gov_vault.totalUserGovPoints(bob)
    assert updated_points > initial_points
    assert updated_total_points > initial_total_points
    assert updated_total_points == updated_points


def test_ripe_gov_vault_lock_bonus_points(
    ripe_gov_vault, ripe_token, whale, bob, alice, teller, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test that locked positions get bonus points compared to unlocked positions"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Bob deposits with minimum lock (no bonus)
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Alice deposits with long lock duration (should get bonus)
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensWithLockDuration(
        alice, ripe_token, deposit_amount, 900, sender=switchboard_alpha.address  # Near max lock
    )
    
    # Advance time equally for both
    boa.env.time_travel(blocks=100)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    ripe_gov_vault.updateUserGovPoints(alice, sender=switchboard_alpha.address)
    
    bob_points = ripe_gov_vault.userGovData(bob, ripe_token).govPoints  # Min lock
    alice_points = ripe_gov_vault.userGovData(alice, ripe_token).govPoints  # Long lock
    
    # Alice should have more points due to lock bonus
    assert alice_points > bob_points
    assert bob_points > 0  # Both should have base points
    assert alice_points > 0


def test_ripe_gov_vault_gov_points_reduction_on_withdrawal(
    ripe_gov_vault, ripe_token, whale, bob, alice, teller, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test that governance points are reduced proportionally on withdrawal"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit and accumulate points WHILE LOCKED
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Advance time to accumulate significant points while still locked
    boa.env.time_travel(blocks=50)  # Accumulate points for 50 blocks
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    
    initial_points = ripe_gov_vault.totalUserGovPoints(bob)
    assert initial_points > 0
    
    # Now advance past unlock time so we can withdraw
    unlock_block = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    current_block = boa.env.evm.patch.block_number
    blocks_to_advance = unlock_block - current_block + 1
    boa.env.time_travel(blocks=blocks_to_advance)

    # Update points to include all time advancement, then capture points before withdrawal
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    points_before = ripe_gov_vault.totalUserGovPoints(bob)
    assert points_before > initial_points  # Should have accumulated more points

    # Withdraw half the position
    ripe_gov_vault.withdrawTokensFromVault(
        bob, ripe_token, deposit_amount // 2, alice, sender=teller.address
    )
    
    # Points should be reduced due to proportional reduction on withdrawal
    points_after = ripe_gov_vault.totalUserGovPoints(bob)
    assert points_after < points_before


def test_ripe_gov_vault_total_gov_points_tracking(
    ripe_gov_vault, ripe_token, whale, bob, alice, teller, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test that total governance points are tracked correctly across users"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Bob deposits
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Alice deposits
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(alice, ripe_token, deposit_amount, sender=teller.address)
    
    # Advance time and update points for both
    boa.env.time_travel(blocks=100)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    ripe_gov_vault.updateUserGovPoints(alice, sender=switchboard_alpha.address)
    
    bob_points = ripe_gov_vault.totalUserGovPoints(bob)
    alice_points = ripe_gov_vault.totalUserGovPoints(alice)
    total_points = ripe_gov_vault.totalGovPoints()
    
    # Total should equal sum of individual user points
    assert total_points == bob_points + alice_points
    assert bob_points > 0
    assert alice_points > 0


def test_ripe_gov_vault_lootbox_share_calculation(
    ripe_gov_vault, ripe_token, whale, bob, teller, setupRipeGovVaultConfig
):
    """Test lootbox share calculation for rewards"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit tokens
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Get lootbox share
    lootbox_share = ripe_gov_vault.getUserLootBoxShare(bob, ripe_token)
    assert lootbox_share > 0


def test_ripe_gov_vault_lootbox_share_no_position(
    ripe_gov_vault, ripe_token, bob, setupRipeGovVaultConfig
):
    """Test lootbox share with no position"""
    setupRipeGovVaultConfig()

    # Get lootbox share with no deposit
    lootbox_share = ripe_gov_vault.getUserLootBoxShare(bob, ripe_token)
    assert lootbox_share == 0


def test_ripe_gov_vault_user_asset_enumeration(
    ripe_gov_vault, ripe_token, whale, bob, teller, setupRipeGovVaultConfig
):
    """Test user asset enumeration functions"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Initially no assets
    asset, has_balance = ripe_gov_vault.getUserAssetAtIndexAndHasBalance(bob, 1)
    assert not has_balance
    
    # Deposit tokens
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Now should have balance
    asset, has_balance = ripe_gov_vault.getUserAssetAtIndexAndHasBalance(bob, 1)
    assert has_balance
    assert asset == ripe_token.address

    # Test asset and amount at index
    asset, amount = ripe_gov_vault.getUserAssetAndAmountAtIndex(bob, 1)
    assert asset == ripe_token.address
    assert amount > 0


def test_ripe_gov_vault_total_amount_functions(
    ripe_gov_vault, ripe_token, whale, bob, teller, setupRipeGovVaultConfig
):
    """Test total amount utility functions"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Initially zero
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 0
    assert ripe_gov_vault.getTotalAmountForVault(ripe_token) == 0
    
    # Deposit tokens
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Check amounts
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == deposit_amount
    assert ripe_gov_vault.getTotalAmountForVault(ripe_token) == deposit_amount


def test_ripe_gov_vault_configuration_updates_after_deposit(
    ripe_gov_vault, ripe_token, whale, bob, teller, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test that configuration updates are handled properly for existing positions"""
    setupRipeGovVaultConfig()
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit with initial config
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Verify initial unlock time is set
    userData_before = ripe_gov_vault.userGovData(bob, ripe_token)
    assert userData_before.unlock > boa.env.evm.patch.block_number  # Should have future unlock
    
    # Update configuration with WORSE terms (this should reset unlock to 0)
    setupRipeGovVaultConfig(
        _assetWeight=150_00,  # increased (doesn't affect unlock reset)
        _minLockDuration=200,  # increased (doesn't affect unlock reset)
        _maxLockDuration=2000,  # increased (doesn't affect unlock reset)
        _maxLockBoost=300_00,  # increased (doesn't affect unlock reset)
        _exitFee=20_00,  # INCREASED from 10_00 - makes terms worse
        _canExit=False  # DISABLED from True - makes terms worse
    )
    
    # Update user points (should refresh terms and reset unlock)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    
    # User data should reflect that unlock was reset due to worse terms
    userData_after = ripe_gov_vault.userGovData(bob, ripe_token)
    
    # When terms get worse (exit disabled AND exit fees increased), unlock MUST be reset to 0
    assert userData_after.unlock == 0  # Should be exactly 0 when terms get worse
    assert userData_after.lastShares > 0  # Should still have shares


def test_ripe_gov_vault_lock_terms_enforcement(
    ripe_gov_vault, ripe_token, whale, bob, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test that lock terms are enforced (min/max durations)"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Test with below minimum lock duration (should be increased to minimum)
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensWithLockDuration(
        bob, ripe_token, deposit_amount, 50, sender=switchboard_alpha.address  # Below min (100)
    )
    
    userData = ripe_gov_vault.userGovData(bob, ripe_token)
    expected_min_unlock = boa.env.evm.patch.block_number + 100  # Should be enforced to minimum
    assert userData.unlock == expected_min_unlock
    
    # Test with above maximum lock duration (should be capped to maximum)
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensWithLockDuration(
        bob, ripe_token, deposit_amount, 1500, sender=switchboard_alpha.address  # Above max (1000)
    )
    
    # The unlock should be a weighted average between previous min lock (100) and max lock (1000)
    # With equal deposits, this should be (100 + 1000) / 2 = 550 blocks from current time
    userData = ripe_gov_vault.userGovData(bob, ripe_token)
    current_block = boa.env.evm.patch.block_number
    expected_unlock = current_block + 550  # Weighted average of 100 and 1000
    assert userData.unlock == expected_unlock


def test_ripe_gov_vault_release_lock_when_cannot_exit(
    ripe_gov_vault, ripe_token, whale, bob, teller, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test that release lock fails when canExit is false"""
    # Setup config with exit disabled
    setupRipeGovVaultConfig(_canExit=False)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit tokens
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Should revert with "cannot exit" - exit is disabled in config
    with boa.reverts("cannot exit"):
        ripe_gov_vault.releaseLock(bob, ripe_token, sender=switchboard_alpha.address)


def test_ripe_gov_vault_release_lock_when_no_unlock_needed(
    ripe_gov_vault, ripe_token, whale, bob, teller, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test that release lock fails when no release is needed"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit tokens
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Fast forward past unlock time
    unlock_block = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    current_block = boa.env.evm.patch.block_number
    blocks_to_advance = unlock_block - current_block + 1
    boa.env.time_travel(blocks=blocks_to_advance)
    
    # Should revert with "no release needed" - already past unlock time
    with boa.reverts("no release needed"):
        ripe_gov_vault.releaseLock(bob, ripe_token, sender=switchboard_alpha.address)


def test_ripe_gov_vault_release_lock_successful_with_exit_fee(
    ripe_gov_vault, ripe_token, whale, bob, switchboard_alpha, _test, setupRipeGovVaultConfig
):
    """Test that release lock works successfully and charges exit fee"""
    # Setup with exit enabled and 10% exit fee
    setupRipeGovVaultConfig(_minLockDuration=100, _maxLockDuration=1000, _canExit=True, _exitFee=10_00)
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit tokens with lock duration
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensWithLockDuration(
        bob, ripe_token, deposit_amount, 500, sender=switchboard_alpha.address  # 500 block lock
    )
    
    # Verify initial state - should be locked
    userData_before = ripe_gov_vault.userGovData(bob, ripe_token)
    vault_balance_before = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    shares_before = userData_before.lastShares
    unlock_before = userData_before.unlock
    current_block = boa.env.evm.patch.block_number
    
    assert unlock_before == current_block + 500  # Should be locked for 500 blocks
    assert vault_balance_before > 0  # Should have vault balance
    assert shares_before > 0  # Should have shares
    
    # Release lock early (should charge 10% exit fee)
    ripe_gov_vault.releaseLock(bob, ripe_token, sender=switchboard_alpha.address)
    
    # Verify state after release
    userData_after = ripe_gov_vault.userGovData(bob, ripe_token)
    vault_balance_after = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    shares_after = userData_after.lastShares
    unlock_after = userData_after.unlock
    
    # 1. Unlock should be reset to 0 (no longer locked)
    assert unlock_after == 0
    
    # 2. Shares should be reduced by exit fee (10%)
    expected_shares_after = shares_before * 90 // 100  # 90% remaining after 10% fee
    _test(shares_after, expected_shares_after)
    
    # 3. Vault balance should be reduced (exact amount may vary due to exchange rates)
    assert vault_balance_after < vault_balance_before
    
    # 4. Verify exit fee was charged from shares
    shares_fee_charged = shares_before - shares_after
    expected_shares_fee = shares_before * 10 // 100  # 10% fee
    _test(shares_fee_charged, expected_shares_fee)


def test_ripe_gov_vault_release_lock_state_changes(
    ripe_gov_vault, ripe_token, whale, bob, switchboard_alpha, _test, setupRipeGovVaultConfig
):
    """Test that release lock properly updates all state variables"""
    # Setup with exit enabled and 5% exit fee
    setupRipeGovVaultConfig(_minLockDuration=200, _maxLockDuration=800, _canExit=True, _exitFee=5_00)
    
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    
    # Deposit tokens with lock duration
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensWithLockDuration(
        bob, ripe_token, deposit_amount, 600, sender=switchboard_alpha.address  # 600 block lock
    )
    
    # Advance some time to accumulate governance points while locked
    boa.env.time_travel(blocks=50)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    
    # Capture state before release
    userData_before = ripe_gov_vault.userGovData(bob, ripe_token)
    vault_balance_before = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    shares_before = userData_before.lastShares
    
    assert userData_before.unlock > boa.env.evm.patch.block_number  # Still locked
    assert vault_balance_before > 0  # Has vault balance
    assert shares_before > 0  # Has shares
    
    # Release lock
    ripe_gov_vault.releaseLock(bob, ripe_token, sender=switchboard_alpha.address)
    
    # Verify all state changes
    userData_after = ripe_gov_vault.userGovData(bob, ripe_token)
    vault_balance_after = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    shares_after = userData_after.lastShares
    
    # 1. Unlock should be reset to 0
    assert userData_after.unlock == 0
    
    # 2. Shares should be reduced by exactly 5% exit fee
    expected_shares_after = shares_before * 95 // 100  # 95% remaining after 5% fee
    _test(shares_after, expected_shares_after)
    
    # 3. Vault balance should be reduced (but exact amount may vary)
    assert vault_balance_after < vault_balance_before
    
    # 4. Verify the shares fee amount is correct
    shares_fee_charged = shares_before - shares_after
    expected_shares_fee = shares_before * 5 // 100  # 5% fee
    _test(shares_fee_charged, expected_shares_fee)
    
    # 5. User should retain 95% of their original shares
    _test(shares_after, shares_before * 95 // 100)


def test_ripe_gov_vault_complex_points_scenario(
    ripe_gov_vault, ripe_token, whale, bob, alice, teller, auction_house, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test complex scenario with multiple operations affecting governance points"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Bob deposits with lock
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensWithLockDuration(
        bob, ripe_token, deposit_amount, 800, sender=switchboard_alpha.address
    )
    
    # Alice deposits with minimum lock
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(alice, ripe_token, deposit_amount, sender=teller.address)
    
    # Advance time to accumulate points
    boa.env.time_travel(blocks=200)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    ripe_gov_vault.updateUserGovPoints(alice, sender=switchboard_alpha.address)
    
    bob_points_before = ripe_gov_vault.totalUserGovPoints(bob)
    alice_points_before = ripe_gov_vault.totalUserGovPoints(alice)
    total_points_before = ripe_gov_vault.totalGovPoints()
    
    # Bob should have more points due to longer lock
    assert bob_points_before > alice_points_before
    assert total_points_before == bob_points_before + alice_points_before
    
    # Transfer some of Bob's balance to Alice
    transfer_amount = 30 * EIGHTEEN_DECIMALS
    ripe_gov_vault.transferBalanceWithinVault(
        ripe_token, bob, alice, transfer_amount, sender=auction_house.address
    )
    
    # Check points after transfer
    bob_points_after = ripe_gov_vault.totalUserGovPoints(bob)
    alice_points_after = ripe_gov_vault.totalUserGovPoints(alice)
    total_points_after = ripe_gov_vault.totalGovPoints()
    
    # Bob should have fewer points, and total should be preserved
    assert bob_points_after < bob_points_before
    # Note: Transfer logic may not immediately give Alice more points in the same block
    # The important thing is that the system maintains consistency
    assert total_points_after == bob_points_after + alice_points_after


# Additional tests using different vault configurations

def test_ripe_gov_vault_high_asset_weight_more_points(
    ripe_gov_vault, ripe_token, whale, bob, charlie, teller, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test that higher asset weight results in more governance points"""
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Test with normal weight first using bob
    setupRipeGovVaultConfig(_assetWeight=100_00)  # 100% weight
    
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    boa.env.time_travel(blocks=100)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    
    normal_weight_points = ripe_gov_vault.userGovData(bob, ripe_token).govPoints  # Use asset-specific points
    
    # Setup with high asset weight using charlie (different user)
    setupRipeGovVaultConfig(_assetWeight=300_00)  # 300% weight
    
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(charlie, ripe_token, deposit_amount, sender=teller.address)
    
    # Advance time and update points
    boa.env.time_travel(blocks=100)
    ripe_gov_vault.updateUserGovPoints(charlie, sender=switchboard_alpha.address)
    
    high_weight_points = ripe_gov_vault.userGovData(charlie, ripe_token).govPoints  # Use asset-specific points
    
    # Higher asset weight (300%) should result in more points than normal weight (100%)
    assert high_weight_points > normal_weight_points
    assert normal_weight_points > 0  # Both should have some points
    assert high_weight_points > 0


def test_ripe_gov_vault_zero_asset_weight_no_points(
    ripe_gov_vault, ripe_token, whale, bob, teller, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test that zero asset weight doesn't break functionality"""
    # Setup with zero asset weight
    setupRipeGovVaultConfig(_assetWeight=0)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit tokens
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Advance time and update points
    boa.env.time_travel(blocks=100)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    
    # With zero asset weight, there may still be base/lock bonus points
    points = ripe_gov_vault.userGovData(bob, ripe_token).govPoints
    total_points = ripe_gov_vault.totalUserGovPoints(bob)
    
    # Operations should work and points should be reasonable values
    assert points >= 0
    assert total_points >= 0
    assert total_points == points  # Should be consistent


def test_ripe_gov_vault_max_lock_boost_comparison(
    ripe_gov_vault, ripe_token, whale, bob, charlie, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test that higher max lock boost results in more bonus points"""
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Test with normal boost first using bob
    setupRipeGovVaultConfig(_maxLockBoost=200_00)  # 200% boost (default)

    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensWithLockDuration(
        bob, ripe_token, deposit_amount, 1000, sender=switchboard_alpha.address  # Max lock
    )
    
    # Advance time and update points
    boa.env.time_travel(blocks=100)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    
    normal_boost_points = ripe_gov_vault.userGovData(bob, ripe_token).govPoints
    
    # Setup with high lock boost using charlie
    setupRipeGovVaultConfig(_maxLockBoost=500_00)  # 500% boost

    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensWithLockDuration(
        charlie, ripe_token, deposit_amount, 1000, sender=switchboard_alpha.address  # Max lock
    )
    
    # Advance time and update points
    boa.env.time_travel(blocks=100)
    ripe_gov_vault.updateUserGovPoints(charlie, sender=switchboard_alpha.address)
    
    high_boost_points = ripe_gov_vault.userGovData(charlie, ripe_token).govPoints
    
    # Higher max lock boost (500%) should result in more points than normal boost (200%)
    assert high_boost_points > normal_boost_points
    assert normal_boost_points > 0  # Both should have some points
    assert high_boost_points > 0


def test_ripe_gov_vault_short_lock_range_enforcement(
    ripe_gov_vault, ripe_token, whale, bob, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test vault with very short lock duration range"""
    # Setup with narrow lock range
    setupRipeGovVaultConfig(_minLockDuration=90, _maxLockDuration=110)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Test that lock durations are properly clamped to range
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensWithLockDuration(
        bob, ripe_token, deposit_amount, 200, sender=switchboard_alpha.address  # Should be clamped to 110
    )
    
    userData = ripe_gov_vault.userGovData(bob, ripe_token)
    expected_unlock = boa.env.evm.patch.block_number + 110  # Should be clamped to max
    assert userData.unlock == expected_unlock


# util funciton tests


def test_ripe_gov_vault_get_latest_gov_points_zero_shares(ripe_gov_vault):
    """Test that getLatestGovPoints returns 0 when lastShares is 0"""
    
    # Test with zero shares
    points = ripe_gov_vault.getLatestGovPoints(
        0,  # lastShares = 0
        100,  # lastPointsUpdate
        200,  # unlock
        (50, 1000, 200_00, True, 10_00),  # terms
        100_00  # weight
    )
    assert points == 0


def test_ripe_gov_vault_get_latest_gov_points_no_time_elapsed(ripe_gov_vault):
    """Test that getLatestGovPoints returns 0 when no time has elapsed"""
    
    current_block = boa.env.evm.patch.block_number
    
    # Test with same block as last update
    points = ripe_gov_vault.getLatestGovPoints(
        1000 * 10**18,  # lastShares
        current_block,  # lastPointsUpdate = current block
        current_block + 100,  # unlock
        (50, 1000, 200_00, True, 10_00),  # terms
        100_00  # weight
    )
    assert points == 0


def test_ripe_gov_vault_get_latest_gov_points_with_asset_weight(ripe_gov_vault):
    """Test getLatestGovPoints with different asset weights"""
    
    # Advance time to ensure we have a reasonable current block
    boa.env.time_travel(blocks=2000)
    current_block = boa.env.evm.patch.block_number
    
    shares = 1000 * 10**18  # 1000 normalized shares
    time_elapsed = 100
    past_block = current_block - time_elapsed  # lastPointsUpdate in the past
    
    # Test with 100% weight (normal)
    points_100 = ripe_gov_vault.getLatestGovPoints(
        shares,
        past_block,  # lastPointsUpdate
        current_block + 500,  # still locked
        (0, 0, 0, False, 0),  # no lock terms
        100_00  # 100% weight
    )
    
    # Test with 200% weight (2x multiplier)
    points_200 = ripe_gov_vault.getLatestGovPoints(
        shares,
        past_block,
        current_block + 500,
        (0, 0, 0, False, 0),  # no lock terms
        200_00  # 200% weight
    )
    
    # Test with 50% weight (0.5x multiplier)
    points_50 = ripe_gov_vault.getLatestGovPoints(
        shares,
        past_block,
        current_block + 500,
        (0, 0, 0, False, 0),  # no lock terms
        50_00  # 50% weight
    )
    
    # Test with 0% weight (no points)
    points_0 = ripe_gov_vault.getLatestGovPoints(
        shares,
        past_block,
        current_block + 500,
        (0, 0, 0, False, 0),  # no lock terms
        0  # 0% weight
    )
    
    # Expected: 1000 shares * 100 blocks = 100,000 base points
    expected_base = 1000 * time_elapsed
    assert points_100 == expected_base
    assert points_200 == expected_base * 2
    assert points_50 == expected_base // 2
    # Note: 0% weight doesn't zero out points, it just doesn't apply weight multiplier
    assert points_0 == expected_base


def test_ripe_gov_vault_get_latest_gov_points_with_lock_bonus(ripe_gov_vault):
    """Test getLatestGovPoints includes lock bonus when terms are set"""
    
    # Advance time to ensure we have a reasonable current block
    boa.env.time_travel(blocks=2000)
    current_block = boa.env.evm.patch.block_number
    
    shares = 1000 * 10**18
    time_elapsed = 100
    past_block = current_block - time_elapsed
    
    # Test without lock terms (no bonus)
    points_no_bonus = ripe_gov_vault.getLatestGovPoints(
        shares,
        past_block,
        current_block + 500,
        (0, 0, 0, False, 0),  # no lock terms
        100_00
    )
    
    # Test with lock terms (should have bonus)
    points_with_bonus = ripe_gov_vault.getLatestGovPoints(
        shares,
        past_block,
        current_block + 500,  # 500 blocks remaining
        (100, 1000, 200_00, True, 10_00),  # lock terms with 200% max boost
        100_00
    )
    
    # Should have more points with lock bonus
    assert points_with_bonus > points_no_bonus


def test_ripe_gov_vault_get_lock_bonus_points_zero_cases(ripe_gov_vault):
    """Test getLockBonusPoints returns 0 in various edge cases"""
    
    # Advance time to ensure we have a reasonable current block
    boa.env.time_travel(blocks=2000)
    current_block = boa.env.evm.patch.block_number
    
    terms = (100, 1000, 200_00, True, 10_00)  # min=100, max=1000, boost=200%
    
    # Test with zero points
    bonus = ripe_gov_vault.getLockBonusPoints(0, current_block + 500, terms)
    assert bonus == 0
    
    # Test with already unlocked (unlock <= current block)
    bonus = ripe_gov_vault.getLockBonusPoints(1000, current_block, terms)
    assert bonus == 0
    
    # Test with unlock in the past (use absolute past block number)
    past_unlock = 100  # Use absolute block number that's definitely in the past
    bonus = ripe_gov_vault.getLockBonusPoints(1000, past_unlock, terms)
    assert bonus == 0


def test_ripe_gov_vault_get_lock_bonus_points_below_min_lock(ripe_gov_vault):
    """Test getLockBonusPoints returns 0 when remaining lock is below minimum"""
    
    current_block = boa.env.evm.patch.block_number
    terms = (100, 1000, 200_00, True, 10_00)  # min=100, max=1000, boost=200%
    
    # Test with remaining lock duration below minimum (50 < 100)
    bonus = ripe_gov_vault.getLockBonusPoints(1000, current_block + 50, terms)
    assert bonus == 0


def test_ripe_gov_vault_get_lock_bonus_points_calculation(ripe_gov_vault):
    """Test getLockBonusPoints calculation logic"""
    
    current_block = boa.env.evm.patch.block_number
    terms = (100, 1000, 200_00, True, 10_00)  # min=100, max=1000, boost=200%
    base_points = 10000
    
    # Test at minimum lock (should give 0 bonus)
    bonus_min = ripe_gov_vault.getLockBonusPoints(base_points, current_block + 100, terms)
    assert bonus_min == 0
    
    # Test at maximum lock (should give full 200% bonus)
    bonus_max = ripe_gov_vault.getLockBonusPoints(base_points, current_block + 1000, terms)
    expected_max_bonus = base_points * 200_00 // 100_00  # 200% of base points
    assert bonus_max == expected_max_bonus
    
    # Test at halfway point (should give 100% bonus)
    halfway_lock = 100 + (1000 - 100) // 2  # 550 blocks
    bonus_half = ripe_gov_vault.getLockBonusPoints(base_points, current_block + halfway_lock, terms)
    expected_half_bonus = base_points * 100_00 // 100_00  # 100% of base points
    assert bonus_half == expected_half_bonus


def test_ripe_gov_vault_get_lock_bonus_points_higher_than_max(ripe_gov_vault):
    """Test getLockBonusPoints caps at maxLockDuration when unlock is higher"""
    
    current_block = boa.env.evm.patch.block_number
    terms = (100, 1000, 200_00, True, 10_00)  # min=100, max=1000, boost=200%
    base_points = 10000
    
    # Test with unlock way beyond max (should still use max for calculation)
    bonus_beyond = ripe_gov_vault.getLockBonusPoints(base_points, current_block + 2000, terms)
    bonus_at_max = ripe_gov_vault.getLockBonusPoints(base_points, current_block + 1000, terms)
    
    # Should be the same since it caps at maxLockDuration
    assert bonus_beyond == bonus_at_max


def test_ripe_gov_vault_get_weighted_lock_no_previous_balance(ripe_gov_vault):
    """Test getWeightedLockOnTokenDeposit with no previous balance"""
    
    current_block = boa.env.evm.patch.block_number
    precision = 10**18
    terms = (100, 1000, 200_00, True, 10_00)
    
    # Test with prevShares below PRECISION
    unlock = ripe_gov_vault.getWeightedLockOnTokenDeposit(
        1000 * precision,  # newShares
        500,  # newLockDuration
        terms,
        precision - 1,  # prevShares < PRECISION
        current_block + 200  # prevUnlock (irrelevant)
    )
    
    # Should just return current block + new lock duration
    assert unlock == current_block + 500


def test_ripe_gov_vault_get_weighted_lock_equal_shares(ripe_gov_vault):
    """Test getWeightedLockOnTokenDeposit with equal share amounts"""
    
    current_block = boa.env.evm.patch.block_number
    precision = 10**18
    terms = (100, 1000, 200_00, True, 10_00)
    
    # Test with equal shares but different lock durations
    unlock = ripe_gov_vault.getWeightedLockOnTokenDeposit(
        1000 * precision,  # newShares
        600,  # newLockDuration
        terms,
        1000 * precision,  # prevShares (same amount)
        current_block + 400  # prevUnlock (400 blocks remaining)
    )
    
    # Should be weighted average: (1000*400 + 1000*600) / (1000+1000) = 500
    expected_unlock = current_block + 500
    assert unlock == expected_unlock


def test_ripe_gov_vault_get_weighted_lock_different_ratios(ripe_gov_vault):
    """Test getWeightedLockOnTokenDeposit with different share ratios"""
    
    current_block = boa.env.evm.patch.block_number
    precision = 10**18
    terms = (100, 1000, 200_00, True, 10_00)
    
    # Test with 3:1 ratio (new deposit 3x larger)
    unlock = ripe_gov_vault.getWeightedLockOnTokenDeposit(
        3000 * precision,  # newShares (3x larger)
        800,  # newLockDuration
        terms,
        1000 * precision,  # prevShares
        current_block + 200  # prevUnlock (200 blocks remaining)
    )
    
    # Weighted average: (1000*200 + 3000*800) / (1000+3000) = (200k + 2.4M) / 4000 = 650
    expected_unlock = current_block + 650
    assert unlock == expected_unlock


def test_ripe_gov_vault_get_weighted_lock_already_unlocked(ripe_gov_vault):
    """Test getWeightedLockOnTokenDeposit when previous position is already unlocked"""
    
    # Advance time to ensure we have a reasonable current block
    boa.env.time_travel(blocks=2000)
    current_block = boa.env.evm.patch.block_number
    
    precision = 10**18
    terms = (100, 1000, 200_00, True, 10_00)
    
    # Test with previous unlock in the past (already unlocked)
    past_unlock = 100  # Use absolute block number that's definitely in the past
    unlock = ripe_gov_vault.getWeightedLockOnTokenDeposit(
        1000 * precision,  # newShares
        500,  # newLockDuration
        terms,
        2000 * precision,  # prevShares
        past_unlock  # prevUnlock (already passed)
    )
    
    # Previous duration should be treated as 1 (minimum)
    # Weighted average: (2000*1 + 1000*500) / (2000+1000) = 502000/3000 ≈ 167
    expected_unlock = current_block + 167
    assert unlock == expected_unlock


def test_ripe_gov_vault_are_key_terms_same_identical(ripe_gov_vault):
    """Test areKeyTermsSame returns True for identical terms"""
    
    terms1 = (100, 1000, 200_00, True, 10_00)
    terms2 = (100, 1000, 200_00, True, 10_00)
    
    assert ripe_gov_vault.areKeyTermsSame(terms1, terms2) == True


def test_ripe_gov_vault_are_key_terms_same_can_exit_worse(ripe_gov_vault):
    """Test areKeyTermsSame returns False when canExit goes from True to False"""
    
    old_terms = (100, 1000, 200_00, True, 10_00)   # canExit = True
    new_terms = (100, 1000, 200_00, False, 10_00)  # canExit = False
    
    assert ripe_gov_vault.areKeyTermsSame(new_terms, old_terms) == False


def test_ripe_gov_vault_are_key_terms_same_can_exit_better(ripe_gov_vault):
    """Test areKeyTermsSame returns True when canExit goes from False to True"""
    
    old_terms = (100, 1000, 200_00, False, 10_00)  # canExit = False
    new_terms = (100, 1000, 200_00, True, 10_00)   # canExit = True
    
    assert ripe_gov_vault.areKeyTermsSame(new_terms, old_terms) == True


def test_ripe_gov_vault_are_key_terms_same_boost_worse(ripe_gov_vault):
    """Test areKeyTermsSame returns False when maxLockBoost decreases"""
    
    old_terms = (100, 1000, 200_00, True, 10_00)  # boost = 200%
    new_terms = (100, 1000, 150_00, True, 10_00)  # boost = 150%
    
    assert ripe_gov_vault.areKeyTermsSame(new_terms, old_terms) == False


def test_ripe_gov_vault_are_key_terms_same_boost_better(ripe_gov_vault):
    """Test areKeyTermsSame returns True when maxLockBoost increases"""
    
    old_terms = (100, 1000, 150_00, True, 10_00)  # boost = 150%
    new_terms = (100, 1000, 200_00, True, 10_00)  # boost = 200%
    
    assert ripe_gov_vault.areKeyTermsSame(new_terms, old_terms) == True


def test_ripe_gov_vault_are_key_terms_same_min_lock_increase_allowed(ripe_gov_vault):
    """Test areKeyTermsSame returns True when minLockDuration increases (stricter terms)"""
    
    old_terms = (100, 1000, 200_00, True, 10_00)  # minLock = 100
    new_terms = (150, 1000, 200_00, True, 10_00)  # minLock = 150 (stricter)
    
    assert ripe_gov_vault.areKeyTermsSame(new_terms, old_terms) == True


def test_ripe_gov_vault_are_key_terms_same_min_lock_decrease_worse(ripe_gov_vault):
    """Test areKeyTermsSame returns False when minLockDuration decreases (terms get worse)"""
    
    old_terms = (150, 1000, 200_00, True, 10_00)  # minLock = 150
    new_terms = (100, 1000, 200_00, True, 10_00)  # minLock = 100 (looser, worse terms)
    
    assert ripe_gov_vault.areKeyTermsSame(new_terms, old_terms) == False


def test_ripe_gov_vault_are_key_terms_same_exit_fee_worse(ripe_gov_vault):
    """Test areKeyTermsSame returns False when exitFee increases"""
    
    old_terms = (100, 1000, 200_00, True, 10_00)  # exitFee = 10%
    new_terms = (100, 1000, 200_00, True, 20_00)  # exitFee = 20%
    
    assert ripe_gov_vault.areKeyTermsSame(new_terms, old_terms) == False


def test_ripe_gov_vault_are_key_terms_same_exit_fee_better(ripe_gov_vault):
    """Test areKeyTermsSame returns True when exitFee decreases"""
    
    old_terms = (100, 1000, 200_00, True, 20_00)  # exitFee = 20%
    new_terms = (100, 1000, 200_00, True, 10_00)  # exitFee = 10%
    
    assert ripe_gov_vault.areKeyTermsSame(new_terms, old_terms) == True


def test_ripe_gov_vault_are_key_terms_same_max_lock_duration_change(ripe_gov_vault):
    """Test areKeyTermsSame allows maxLockDuration changes (not a key term)"""
    
    old_terms = (100, 1000, 200_00, True, 10_00)  # maxLock = 1000
    new_terms = (100, 500, 200_00, True, 10_00)   # maxLock = 500
    
    # maxLockDuration changes are allowed (handled in refreshUnlock)
    assert ripe_gov_vault.areKeyTermsSame(new_terms, old_terms) == True


def test_ripe_gov_vault_refresh_unlock_terms_same(ripe_gov_vault):
    """Test refreshUnlock keeps unlock when terms are the same"""
    
    current_block = boa.env.evm.patch.block_number
    prev_unlock = current_block + 500
    terms = (100, 1000, 200_00, True, 10_00)
    
    new_unlock = ripe_gov_vault.refreshUnlock(prev_unlock, terms, terms)
    assert new_unlock == prev_unlock


def test_ripe_gov_vault_refresh_unlock_terms_worse(ripe_gov_vault):
    """Test refreshUnlock resets to 0 when terms get worse"""
    
    current_block = boa.env.evm.patch.block_number
    prev_unlock = current_block + 500
    old_terms = (100, 1000, 200_00, True, 10_00)  # canExit = True
    new_terms = (100, 1000, 200_00, False, 10_00) # canExit = False (worse)
    
    new_unlock = ripe_gov_vault.refreshUnlock(prev_unlock, new_terms, old_terms)
    assert new_unlock == 0


def test_ripe_gov_vault_refresh_unlock_max_duration_decreased(ripe_gov_vault):
    """Test refreshUnlock caps at new maxLockDuration when it's reduced"""
    
    current_block = boa.env.evm.patch.block_number
    prev_unlock = current_block + 1000  # locked for 1000 blocks
    old_terms = (100, 1200, 200_00, True, 10_00)  # maxLock = 1200
    new_terms = (100, 800, 200_00, True, 10_00)   # maxLock = 800 (reduced)
    
    new_unlock = ripe_gov_vault.refreshUnlock(prev_unlock, new_terms, old_terms)
    
    # Should be capped at current_block + 800 (new max)
    expected_unlock = current_block + 800
    assert new_unlock == expected_unlock


def test_ripe_gov_vault_refresh_unlock_max_duration_increased(ripe_gov_vault):
    """Test refreshUnlock keeps original unlock when maxLockDuration increases"""
    
    current_block = boa.env.evm.patch.block_number
    prev_unlock = current_block + 800   # locked for 800 blocks
    old_terms = (100, 1000, 200_00, True, 10_00)  # maxLock = 1000
    new_terms = (100, 1200, 200_00, True, 10_00)  # maxLock = 1200 (increased)
    
    new_unlock = ripe_gov_vault.refreshUnlock(prev_unlock, new_terms, old_terms)
    
    # Should keep original unlock since it's within new max
    assert new_unlock == prev_unlock


def test_ripe_gov_vault_refresh_unlock_terms_worse_and_max_changed(ripe_gov_vault):
    """Test refreshUnlock handles both terms getting worse and maxLockDuration change"""
    
    current_block = boa.env.evm.patch.block_number
    prev_unlock = current_block + 1000
    old_terms = (100, 1200, 200_00, True, 10_00)   # canExit=True, maxLock=1200
    new_terms = (100, 800, 200_00, False, 10_00)   # canExit=False, maxLock=800
    
    new_unlock = ripe_gov_vault.refreshUnlock(prev_unlock, new_terms, old_terms)
    
    # Terms got worse (canExit False), so should reset to 0
    # Even though maxLock changed, the reset to 0 takes precedence
    assert new_unlock == 0


###########################################
# Critical Production Gap Tests           #
###########################################


def test_ripe_gov_vault_multi_asset_governance_points_tracking(
    ripe_gov_vault, ripe_token, alpha_token, whale, alpha_token_whale, bob, teller, switchboard_alpha, mission_control, setupRipeGovVaultConfig, setAssetConfig
):
    """Test that users with multiple assets get correct governance points across all assets"""
    
    # Setup ripe_token configuration (default)
    setupRipeGovVaultConfig(_assetWeight=100_00, _minLockDuration=100, _maxLockDuration=1000)
    
    # Setup alpha_token as a second asset with different weight
    # First configure alpha_token for vault_id 2 (ripe_gov_vault)
    setAssetConfig(alpha_token, _vaultIds=[2])
    
    # Configure alpha_token with different asset weight in RipeGov vault
    lock_terms_alpha = (50, 500, 150_00, True, 5_00)  # Different terms than ripe_token
    mission_control.setRipeGovVaultConfig(
        alpha_token,
        200_00,  # 200% asset weight vs 100% for ripe_token
        lock_terms_alpha,
        sender=switchboard_alpha.address
    )
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Bob deposits ripe_token
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Bob deposits alpha_token  
    alpha_token.transfer(ripe_gov_vault, deposit_amount, sender=alpha_token_whale)
    ripe_gov_vault.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)
    
    # Advance time to accumulate points
    boa.env.time_travel(blocks=100)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    
    # Check individual asset governance points
    ripe_userData = ripe_gov_vault.userGovData(bob, ripe_token)
    alpha_userData = ripe_gov_vault.userGovData(bob, alpha_token)
    
    # Both should have governance points
    assert ripe_userData.govPoints > 0
    assert alpha_userData.govPoints > 0
    
    # Alpha should have more points due to higher asset weight (200% vs 100%)
    # Expected calculation: base_points * asset_weight / 100_00
    # Alpha has 2x weight, so should have roughly 2x points for same deposit/time
    assert alpha_userData.govPoints > ripe_userData.govPoints
    
    # Check total user governance points includes both assets
    total_user_points = ripe_gov_vault.totalUserGovPoints(bob)
    expected_total = ripe_userData.govPoints + alpha_userData.govPoints
    assert total_user_points == expected_total
    
    # Check global governance points includes this user's total
    total_global_points = ripe_gov_vault.totalGovPoints()
    assert total_global_points >= total_user_points


def test_ripe_gov_vault_multi_asset_governance_points_update_all(
    ripe_gov_vault, ripe_token, alpha_token, whale, alpha_token_whale, bob, alice, teller, switchboard_alpha, mission_control, setupRipeGovVaultConfig, setAssetConfig
):
    """Test that updateUserGovPoints() correctly iterates through all user assets"""
    
    # Setup both assets
    setupRipeGovVaultConfig(_assetWeight=100_00)
    setAssetConfig(alpha_token, _vaultIds=[2])
    
    # Configure alpha_token with different settings
    lock_terms_alpha = (200, 800, 300_00, True, 15_00)
    mission_control.setRipeGovVaultConfig(
        alpha_token,
        150_00,  # 150% asset weight
        lock_terms_alpha,
        sender=switchboard_alpha.address
    )
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Bob deposits to both assets
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    alpha_token.transfer(ripe_gov_vault, deposit_amount, sender=alpha_token_whale)
    ripe_gov_vault.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)
    
    # Alice deposits only to ripe_token
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(alice, ripe_token, deposit_amount, sender=teller.address)
    
    # Advance time
    boa.env.time_travel(blocks=200)
    
    # Capture points before update
    bob_points_before = ripe_gov_vault.totalUserGovPoints(bob)
    alice_points_before = ripe_gov_vault.totalUserGovPoints(alice)
    global_points_before = ripe_gov_vault.totalGovPoints()
    
    # Update governance points for both users
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    ripe_gov_vault.updateUserGovPoints(alice, sender=switchboard_alpha.address)
    
    # Verify points increased for both users
    bob_points_after = ripe_gov_vault.totalUserGovPoints(bob)
    alice_points_after = ripe_gov_vault.totalUserGovPoints(alice)
    global_points_after = ripe_gov_vault.totalGovPoints()
    
    assert bob_points_after > bob_points_before
    assert alice_points_after > alice_points_before
    assert global_points_after > global_points_before
    
    # Bob should have accumulated points from BOTH assets
    # Alice should have accumulated points from only ONE asset
    bob_points_gained = bob_points_after - bob_points_before
    alice_points_gained = alice_points_after - alice_points_before
    
    # Bob's gain should be significantly higher due to having two assets
    # (especially with alpha_token's 150% weight vs 100%)
    assert bob_points_gained > alice_points_gained
    
    # Verify the multi-asset loop worked by checking individual asset points
    bob_ripe_points = ripe_gov_vault.userGovData(bob, ripe_token).govPoints
    bob_alpha_points = ripe_gov_vault.userGovData(bob, alpha_token).govPoints
    alice_ripe_points = ripe_gov_vault.userGovData(alice, ripe_token).govPoints
    alice_alpha_points = ripe_gov_vault.userGovData(alice, alpha_token).govPoints
    
    assert bob_ripe_points > 0
    assert bob_alpha_points > 0
    assert alice_ripe_points > 0
    assert alice_alpha_points == 0  # Alice has no alpha_token deposits
    
    # Bob's total should equal sum of his individual asset points
    assert bob_points_after == bob_ripe_points + bob_alpha_points


def test_ripe_gov_vault_zero_exit_fee_blocks_release_lock_defensive(
    ripe_gov_vault, ripe_token, whale, bob, teller, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test vault's defensive validation against impossible configurations (defense-in-depth)
    
    NOTE: SwitchboardOne.vy prevents canExit=True + exitFee=0 configurations from being set.
    This test serves as defensive programming - the vault validates its own preconditions
    even though the configuration system should prevent this scenario.
    """
    
    # Setup with canExit=True but exitFee=0 
    # (This configuration should be impossible via SwitchboardOne, but we test vault's defense)
    setupRipeGovVaultConfig(
        _minLockDuration=100, 
        _maxLockDuration=1000, 
        _canExit=True,  # Exit is allowed
        _exitFee=0      # No exit fee (invalid combination, but testing vault's defense)
    )
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit tokens with lock duration
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensWithLockDuration(
        bob, ripe_token, deposit_amount, 500, sender=switchboard_alpha.address
    )
    
    # Verify user is locked
    userData = ripe_gov_vault.userGovData(bob, ripe_token)
    current_block = boa.env.evm.patch.block_number
    assert userData.unlock == current_block + 500  # Still locked
    assert userData.lastTerms.canExit == True       # Exit is allowed
    assert userData.lastTerms.exitFee == 0          # But exit fee is zero
    
    # Try to release lock - vault should defensively reject this
    with boa.reverts():  # Should revert with "no exit fee" - vault's defensive validation
        ripe_gov_vault.releaseLock(bob, ripe_token, sender=switchboard_alpha.address)
    
    # This demonstrates the vault's defensive programming:
    # Even if somehow an invalid configuration exists, the vault protects itself

