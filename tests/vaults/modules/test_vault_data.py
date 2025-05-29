import pytest
import boa

from constants import EIGHTEEN_DECIMALS


def test_vault_data_initialization(simple_erc20_vault):
    """Test that vault data is properly initialized"""
    assert not simple_erc20_vault.isPaused()
    assert simple_erc20_vault.numAssets() == 0
    assert simple_erc20_vault.getNumVaultAssets() == 0


def test_vault_data_deposit_and_balance_management(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
):
    """Test deposit and balance management functionality"""
    # Setup initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(simple_erc20_vault, deposit_amount, sender=alpha_token_whale)
    
    # Perform deposit
    deposited = simple_erc20_vault.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)
    assert deposited == deposit_amount

    # Check balances
    assert simple_erc20_vault.userBalances(bob, alpha_token) == deposit_amount
    assert simple_erc20_vault.totalBalances(alpha_token) == deposit_amount

    # Check user asset registration
    assert simple_erc20_vault.isUserInVaultAsset(bob, alpha_token)
    assert simple_erc20_vault.userAssets(bob, 1) == alpha_token.address
    assert simple_erc20_vault.indexOfUserAsset(bob, alpha_token) == 1
    assert simple_erc20_vault.numUserAssets(bob) == 2
    assert simple_erc20_vault.getNumUserAssets(bob) == 1

    # Check vault asset registration
    assert simple_erc20_vault.isSupportedVaultAsset(alpha_token)
    assert simple_erc20_vault.vaultAssets(1) == alpha_token.address
    assert simple_erc20_vault.indexOfAsset(alpha_token) == 1
    assert simple_erc20_vault.numAssets() == 2
    assert simple_erc20_vault.getNumVaultAssets() == 1


def test_vault_data_withdrawal(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
):
    """Test withdrawal functionality"""
    # Setup initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(simple_erc20_vault, deposit_amount, sender=alpha_token_whale)
    simple_erc20_vault.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Perform withdrawal
    withdraw_amount = 50 * EIGHTEEN_DECIMALS
    withdrawn, is_depleted = simple_erc20_vault.withdrawTokensFromVault(
        bob, alpha_token, withdraw_amount, bob, sender=teller.address
    )
    assert withdrawn == withdraw_amount
    assert not is_depleted

    # Check balances after withdrawal
    assert simple_erc20_vault.userBalances(bob, alpha_token) == deposit_amount - withdraw_amount
    assert simple_erc20_vault.totalBalances(alpha_token) == deposit_amount - withdraw_amount

    # Withdraw remaining amount
    remaining = deposit_amount - withdraw_amount
    withdrawn, is_depleted = simple_erc20_vault.withdrawTokensFromVault(
        bob, alpha_token, remaining, bob, sender=teller.address
    )
    assert withdrawn == remaining
    assert is_depleted

    # Check balances after full withdrawal
    assert simple_erc20_vault.userBalances(bob, alpha_token) == 0
    assert simple_erc20_vault.totalBalances(alpha_token) == 0


def test_vault_data_transfer(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    teller,
    auction_house,
):
    """Test balance transfer functionality"""
    # Setup initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(simple_erc20_vault, deposit_amount, sender=alpha_token_whale)
    simple_erc20_vault.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Transfer balance
    transfer_amount = 50 * EIGHTEEN_DECIMALS
    transferred, is_depleted = simple_erc20_vault.transferBalanceWithinVault(
        alpha_token, bob, sally, transfer_amount, sender=auction_house.address
    )
    assert transferred == transfer_amount
    assert not is_depleted

    # Check balances after transfer
    assert simple_erc20_vault.userBalances(bob, alpha_token) == deposit_amount - transfer_amount
    assert simple_erc20_vault.userBalances(sally, alpha_token) == transfer_amount
    assert simple_erc20_vault.totalBalances(alpha_token) == deposit_amount


def test_vault_data_pause(
    simple_erc20_vault,
    mission_control,
    sally,
):
    """Test pause functionality"""
    # Pause vault
    simple_erc20_vault.pause(True, sender=mission_control.address)
    assert simple_erc20_vault.isPaused()

    # Unpause vault
    simple_erc20_vault.pause(False, sender=mission_control.address)
    assert not simple_erc20_vault.isPaused()

    # Test unauthorized pause
    with boa.reverts("only MissionControl allowed"):
        simple_erc20_vault.pause(True, sender=sally)


def test_vault_data_recover_funds(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    mission_control,
    bob,
    sally,
    teller,
):
    """Test fund recovery functionality"""
    # Transfer tokens directly to vault (not through deposit)
    recover_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(simple_erc20_vault, recover_amount, sender=alpha_token_whale)

    # Recover funds
    simple_erc20_vault.recoverFunds(bob, alpha_token, sender=mission_control.address)
    assert alpha_token.balanceOf(bob) == recover_amount

    # Test unauthorized recovery
    with boa.reverts("only MissionControl allowed"):
        simple_erc20_vault.recoverFunds(bob, alpha_token, sender=sally)

    # Test recovery of registered asset
    # First register the asset through a deposit
    alpha_token.transfer(simple_erc20_vault, recover_amount, sender=alpha_token_whale)
    simple_erc20_vault.depositTokensInVault(bob, alpha_token, recover_amount, sender=teller.address)
    
    # Now try to recover - should fail since asset is registered
    alpha_token.transfer(simple_erc20_vault, recover_amount, sender=alpha_token_whale)
    with boa.reverts("invalid recovery"):
        simple_erc20_vault.recoverFunds(bob, alpha_token, sender=mission_control.address)


def test_vault_data_asset_registration(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    mission_control,
    bob,
    alpha_token_whale,
    teller,
):
    """Test asset registration and deregistration"""
    # Register assets through deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(simple_erc20_vault, deposit_amount, sender=alpha_token_whale)
    simple_erc20_vault.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Try deregistering with balance
    assert not simple_erc20_vault.deregisterVaultAsset(alpha_token, sender=mission_control.address)
    assert simple_erc20_vault.isSupportedVaultAsset(alpha_token)

    # Withdraw all funds
    simple_erc20_vault.withdrawTokensFromVault(bob, alpha_token, deposit_amount, bob, sender=teller.address)

    # Now deregister should work
    assert simple_erc20_vault.deregisterVaultAsset(alpha_token, sender=mission_control.address)
    assert not simple_erc20_vault.isSupportedVaultAsset(alpha_token)

    # Test unauthorized deregistration
    with boa.reverts("only MissionControl allowed"):
        simple_erc20_vault.deregisterVaultAsset(bravo_token, sender=bob)


def test_vault_data_user_asset_registration(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    lootbox,
    sally,
):
    """Test user asset registration and deregistration"""
    # Register user asset through deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(simple_erc20_vault, deposit_amount, sender=alpha_token_whale)
    simple_erc20_vault.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Try deregistering with balance
    simple_erc20_vault.deregisterUserAsset(bob, alpha_token, sender=lootbox.address)
    assert simple_erc20_vault.isUserInVaultAsset(bob, alpha_token)

    # Withdraw all funds
    simple_erc20_vault.withdrawTokensFromVault(
        bob, alpha_token, deposit_amount, bob, sender=teller.address
    )

    # Now deregister should work
    simple_erc20_vault.deregisterUserAsset(bob, alpha_token, sender=lootbox.address)
    assert not simple_erc20_vault.isUserInVaultAsset(bob, alpha_token)

    # Test unauthorized deregistration
    with boa.reverts("only Lootbox allowed"):
        simple_erc20_vault.deregisterUserAsset(bob, alpha_token, sender=sally)


def test_vault_data_utility_functions(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
):
    """Test utility functions"""
    # Test doesVaultHaveAnyFunds
    assert not simple_erc20_vault.doesVaultHaveAnyFunds()

    # Setup deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(simple_erc20_vault, deposit_amount, sender=alpha_token_whale)
    simple_erc20_vault.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Test doesVaultHaveAnyFunds after deposit
    assert simple_erc20_vault.doesVaultHaveAnyFunds()

    # Test getVaultDataOnDeposit
    vault_data = simple_erc20_vault.getVaultDataOnDeposit(bob, alpha_token)
    assert vault_data.hasPosition
    assert vault_data.numAssets == 1
    assert vault_data.userBalance == deposit_amount
    assert vault_data.totalBalance == deposit_amount

    # Test getUserLootBoxShare
    assert simple_erc20_vault.getUserLootBoxShare(bob, alpha_token) == deposit_amount

    # Test getUserAssetAndAmountAtIndex
    asset, amount = simple_erc20_vault.getUserAssetAndAmountAtIndex(bob, 1)
    assert asset == alpha_token.address
    assert amount == deposit_amount

    # Test getUserAssetAtIndexAndHasBalance
    asset, has_balance = simple_erc20_vault.getUserAssetAtIndexAndHasBalance(bob, 1)
    assert asset == alpha_token.address
    assert has_balance 

def test_vault_data_multiple_assets_single_user(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    teller,
):
    """Test vault data management with multiple assets for a single user"""
    # Setup initial deposits
    alpha_amount = 100 * EIGHTEEN_DECIMALS
    bravo_amount = 200 * EIGHTEEN_DECIMALS
    charlie_amount = 300 * (10 ** charlie_token.decimals())

    # Transfer tokens to vault
    alpha_token.transfer(simple_erc20_vault, alpha_amount, sender=alpha_token_whale)
    bravo_token.transfer(simple_erc20_vault, bravo_amount, sender=bravo_token_whale)
    charlie_token.transfer(simple_erc20_vault, charlie_amount, sender=charlie_token_whale)

    # Bob deposits all three assets
    simple_erc20_vault.depositTokensInVault(bob, alpha_token, alpha_amount, sender=teller.address)
    simple_erc20_vault.depositTokensInVault(bob, bravo_token, bravo_amount, sender=teller.address)
    simple_erc20_vault.depositTokensInVault(bob, charlie_token, charlie_amount, sender=teller.address)

    # Verify Bob's data
    assert simple_erc20_vault.getNumUserAssets(bob) == 3
    assert simple_erc20_vault.userAssets(bob, 1) == alpha_token.address
    assert simple_erc20_vault.userAssets(bob, 2) == bravo_token.address
    assert simple_erc20_vault.userAssets(bob, 3) == charlie_token.address
    assert simple_erc20_vault.indexOfUserAsset(bob, alpha_token) == 1
    assert simple_erc20_vault.indexOfUserAsset(bob, bravo_token) == 2
    assert simple_erc20_vault.indexOfUserAsset(bob, charlie_token) == 3
    assert simple_erc20_vault.userBalances(bob, alpha_token) == alpha_amount
    assert simple_erc20_vault.userBalances(bob, bravo_token) == bravo_amount
    assert simple_erc20_vault.userBalances(bob, charlie_token) == charlie_amount

    # Verify vault data
    assert simple_erc20_vault.getNumVaultAssets() == 3
    assert simple_erc20_vault.vaultAssets(1) == alpha_token.address
    assert simple_erc20_vault.vaultAssets(2) == bravo_token.address
    assert simple_erc20_vault.vaultAssets(3) == charlie_token.address
    assert simple_erc20_vault.indexOfAsset(alpha_token) == 1
    assert simple_erc20_vault.indexOfAsset(bravo_token) == 2
    assert simple_erc20_vault.indexOfAsset(charlie_token) == 3
    assert simple_erc20_vault.totalBalances(alpha_token) == alpha_amount
    assert simple_erc20_vault.totalBalances(bravo_token) == bravo_amount
    assert simple_erc20_vault.totalBalances(charlie_token) == charlie_amount


def test_vault_data_multiple_users_single_asset(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    teller,
):
    """Test vault data management with multiple users for a single asset"""
    # Setup initial deposits
    bob_amount = 100 * EIGHTEEN_DECIMALS
    sally_amount = 50 * EIGHTEEN_DECIMALS

    # Transfer tokens to vault
    alpha_token.transfer(simple_erc20_vault, bob_amount, sender=alpha_token_whale)
    alpha_token.transfer(simple_erc20_vault, sally_amount, sender=alpha_token_whale)

    # Both users deposit
    simple_erc20_vault.depositTokensInVault(bob, alpha_token, bob_amount, sender=teller.address)
    simple_erc20_vault.depositTokensInVault(sally, alpha_token, sally_amount, sender=teller.address)

    # Verify user data
    assert simple_erc20_vault.getNumUserAssets(bob) == 1
    assert simple_erc20_vault.getNumUserAssets(sally) == 1
    assert simple_erc20_vault.userBalances(bob, alpha_token) == bob_amount
    assert simple_erc20_vault.userBalances(sally, alpha_token) == sally_amount

    # Verify vault totals
    assert simple_erc20_vault.totalBalances(alpha_token) == bob_amount + sally_amount


def test_vault_data_utility_functions_multiple_assets(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    teller,
):
    """Test utility functions with multiple assets"""
    # Setup deposits
    alpha_amount = 100 * EIGHTEEN_DECIMALS
    bravo_amount = 200 * EIGHTEEN_DECIMALS
    charlie_amount = 300 * (10 ** charlie_token.decimals())

    # Transfer and deposit tokens
    alpha_token.transfer(simple_erc20_vault, alpha_amount, sender=alpha_token_whale)
    bravo_token.transfer(simple_erc20_vault, bravo_amount, sender=bravo_token_whale)
    charlie_token.transfer(simple_erc20_vault, charlie_amount, sender=charlie_token_whale)
    simple_erc20_vault.depositTokensInVault(bob, alpha_token, alpha_amount, sender=teller.address)
    simple_erc20_vault.depositTokensInVault(bob, bravo_token, bravo_amount, sender=teller.address)
    simple_erc20_vault.depositTokensInVault(bob, charlie_token, charlie_amount, sender=teller.address)

    # Test getVaultDataOnDeposit
    vault_data = simple_erc20_vault.getVaultDataOnDeposit(bob, alpha_token)
    assert vault_data.hasPosition
    assert vault_data.numAssets == 3
    assert vault_data.userBalance == alpha_amount
    assert vault_data.totalBalance == alpha_amount

    # Test getUserAssetAndAmountAtIndex
    for i in range(1, 4):
        asset, amount = simple_erc20_vault.getUserAssetAndAmountAtIndex(bob, i)
        if asset == alpha_token.address:
            assert amount == alpha_amount
        elif asset == bravo_token.address:
            assert amount == bravo_amount
        elif asset == charlie_token.address:
            assert amount == charlie_amount

    # Test getUserAssetAtIndexAndHasBalance
    for i in range(1, 4):
        asset, has_balance = simple_erc20_vault.getUserAssetAtIndexAndHasBalance(bob, i)
        assert has_balance
        if asset == alpha_token.address:
            assert simple_erc20_vault.userBalances(bob, asset) == alpha_amount
        elif asset == bravo_token.address:
            assert simple_erc20_vault.userBalances(bob, asset) == bravo_amount
        elif asset == charlie_token.address:
            assert simple_erc20_vault.userBalances(bob, asset) == charlie_amount

    # Test doesVaultHaveAnyFunds
    assert simple_erc20_vault.doesVaultHaveAnyFunds()


def test_vault_data_withdrawal_multiple_assets(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    sally,
    teller,
):
    """Test withdrawals with multiple assets and users"""
    # Setup initial deposits
    bob_alpha = 100 * EIGHTEEN_DECIMALS
    bob_bravo = 200 * EIGHTEEN_DECIMALS
    sally_alpha = 50 * EIGHTEEN_DECIMALS
    sally_bravo = 75 * EIGHTEEN_DECIMALS

    # Transfer and deposit tokens
    alpha_token.transfer(simple_erc20_vault, bob_alpha + sally_alpha, sender=alpha_token_whale)
    bravo_token.transfer(simple_erc20_vault, bob_bravo + sally_bravo, sender=bravo_token_whale)
    simple_erc20_vault.depositTokensInVault(bob, alpha_token, bob_alpha, sender=teller.address)
    simple_erc20_vault.depositTokensInVault(bob, bravo_token, bob_bravo, sender=teller.address)
    simple_erc20_vault.depositTokensInVault(sally, alpha_token, sally_alpha, sender=teller.address)
    simple_erc20_vault.depositTokensInVault(sally, bravo_token, sally_bravo, sender=teller.address)

    # Withdraw all of Bob's assets
    simple_erc20_vault.withdrawTokensFromVault(bob, alpha_token, bob_alpha, bob, sender=teller.address)
    simple_erc20_vault.withdrawTokensFromVault(bob, bravo_token, bob_bravo, bob, sender=teller.address)

    # Verify Bob's balances are zero but Sally's remain
    assert simple_erc20_vault.userBalances(bob, alpha_token) == 0
    assert simple_erc20_vault.userBalances(bob, bravo_token) == 0
    assert simple_erc20_vault.userBalances(sally, alpha_token) == sally_alpha
    assert simple_erc20_vault.userBalances(sally, bravo_token) == sally_bravo

    # Verify vault totals are updated
    assert simple_erc20_vault.totalBalances(alpha_token) == sally_alpha
    assert simple_erc20_vault.totalBalances(bravo_token) == sally_bravo

    # Verify asset registrations are maintained
    assert simple_erc20_vault.getNumUserAssets(bob) == 2
    assert simple_erc20_vault.isUserInVaultAsset(bob, alpha_token)
    assert simple_erc20_vault.isUserInVaultAsset(bob, bravo_token)
    assert simple_erc20_vault.getNumVaultAssets() == 2
    assert simple_erc20_vault.isSupportedVaultAsset(alpha_token)
    assert simple_erc20_vault.isSupportedVaultAsset(bravo_token)

def test_vault_data_asset_deregistration_with_multiple_assets(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    teller,
    lootbox,
):
    """Test asset deregistration behavior when a user has multiple assets"""
    # Setup initial deposits
    alpha_amount = 100 * EIGHTEEN_DECIMALS
    bravo_amount = 200 * EIGHTEEN_DECIMALS
    charlie_amount = 300 * (10 ** charlie_token.decimals())

    # Transfer tokens to vault
    alpha_token.transfer(simple_erc20_vault, alpha_amount, sender=alpha_token_whale)
    bravo_token.transfer(simple_erc20_vault, bravo_amount, sender=bravo_token_whale)
    charlie_token.transfer(simple_erc20_vault, charlie_amount, sender=charlie_token_whale)

    # Bob deposits all three assets
    simple_erc20_vault.depositTokensInVault(bob, alpha_token, alpha_amount, sender=teller.address)
    simple_erc20_vault.depositTokensInVault(bob, bravo_token, bravo_amount, sender=teller.address)
    simple_erc20_vault.depositTokensInVault(bob, charlie_token, charlie_amount, sender=teller.address)

    # Verify initial state
    assert simple_erc20_vault.getNumUserAssets(bob) == 3
    assert simple_erc20_vault.userAssets(bob, 1) == alpha_token.address
    assert simple_erc20_vault.userAssets(bob, 2) == bravo_token.address
    assert simple_erc20_vault.userAssets(bob, 3) == charlie_token.address
    assert simple_erc20_vault.indexOfUserAsset(bob, alpha_token) == 1
    assert simple_erc20_vault.indexOfUserAsset(bob, bravo_token) == 2
    assert simple_erc20_vault.indexOfUserAsset(bob, charlie_token) == 3

    # Withdraw bravo token to allow deregistration
    simple_erc20_vault.withdrawTokensFromVault(bob, bravo_token, bravo_amount, bob, sender=teller.address)

    # Deregister bravo token
    simple_erc20_vault.deregisterUserAsset(bob, bravo_token, sender=lootbox.address)

    # Verify updated state after deregistration
    assert simple_erc20_vault.getNumUserAssets(bob) == 2
    assert not simple_erc20_vault.isUserInVaultAsset(bob, bravo_token)
    assert simple_erc20_vault.indexOfUserAsset(bob, bravo_token) == 0

    # Verify remaining assets are still properly indexed
    assert simple_erc20_vault.userAssets(bob, 1) == alpha_token.address
    assert simple_erc20_vault.userAssets(bob, 2) == charlie_token.address
    assert simple_erc20_vault.indexOfUserAsset(bob, alpha_token) == 1
    assert simple_erc20_vault.indexOfUserAsset(bob, charlie_token) == 2

    # Verify balances are maintained for remaining assets
    assert simple_erc20_vault.userBalances(bob, alpha_token) == alpha_amount
    assert simple_erc20_vault.userBalances(bob, charlie_token) == charlie_amount
    assert simple_erc20_vault.userBalances(bob, bravo_token) == 0

    # Verify utility functions still work correctly
    vault_data = simple_erc20_vault.getVaultDataOnDeposit(bob, alpha_token)
    assert vault_data.hasPosition
    assert vault_data.numAssets == 2
    assert vault_data.userBalance == alpha_amount

    # Test asset and amount retrieval for remaining assets
    for i in range(1, 3):
        asset, amount = simple_erc20_vault.getUserAssetAndAmountAtIndex(bob, i)
        if asset == alpha_token.address:
            assert amount == alpha_amount
        elif asset == charlie_token.address:
            assert amount == charlie_amount 