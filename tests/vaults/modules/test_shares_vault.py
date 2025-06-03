import pytest
import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS


def test_shares_vault_deposit_validation(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    switchboard_one,
    bob,
    teller,
):
    """Test deposit validation logic in SharesVault"""
    # Test deposit with zero address
    with boa.reverts("invalid user or asset"):
        rebase_erc20_vault.depositTokensInVault(ZERO_ADDRESS, alpha_token, 100, sender=teller.address)
    with boa.reverts("invalid user or asset"):
        rebase_erc20_vault.depositTokensInVault(bob, ZERO_ADDRESS, 100, sender=teller.address)

    # Test deposit with zero amount
    with boa.reverts("invalid deposit amount"):
        rebase_erc20_vault.depositTokensInVault(bob, alpha_token, 0, sender=teller.address)

    # Test deposit when paused
    rebase_erc20_vault.pause(True, sender=switchboard_one.address)
    with boa.reverts("contract paused"):
        rebase_erc20_vault.depositTokensInVault(bob, alpha_token, 100, sender=teller.address)
    rebase_erc20_vault.pause(False, sender=switchboard_one.address)

    # Test deposit with amount larger than balance
    large_amount = 1000000 * EIGHTEEN_DECIMALS
    small_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, small_amount, sender=alpha_token_whale)
    deposited = rebase_erc20_vault.depositTokensInVault(bob, alpha_token, large_amount, sender=teller.address)
    assert deposited == small_amount  # Should only deposit what's available


def test_shares_vault_initial_deposit(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    _test,
):
    """Test initial deposit and share calculation"""
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, deposit_amount, sender=alpha_token_whale)
    
    # First deposit should create 1:1 shares
    deposited = rebase_erc20_vault.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)
    assert deposited == deposit_amount

    # Check shares and amounts
    amount = rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    _test(deposit_amount, amount)  # Amount should be close to deposit_amount


def test_shares_vault_multiple_deposits(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    teller,
    _test,
):
    """Test multiple deposits and share calculations"""
    # First deposit
    deposit1 = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, deposit1, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(bob, alpha_token, deposit1, sender=teller.address)
    
    # Second deposit
    deposit2 = 200 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, deposit2, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(sally, alpha_token, deposit2, sender=teller.address)

    # Check shares and amounts
    bob_amount = rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    sally_amount = rebase_erc20_vault.getTotalAmountForUser(sally, alpha_token)

    # Bob should have ~1/3 of total shares
    _test(deposit1, bob_amount)
    
    # Sally should have ~2/3 of total shares
    _test(deposit2, sally_amount)


def test_shares_vault_withdrawal(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    _test,
):
    """Test withdrawal and share calculations"""
    # Setup initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, deposit_amount, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Withdraw half
    withdraw_amount = deposit_amount // 2
    withdrawn, is_depleted = rebase_erc20_vault.withdrawTokensFromVault(
        bob, alpha_token, withdraw_amount, bob, sender=teller.address
    )
    assert not is_depleted
    _test(withdraw_amount, withdrawn)

    # Check remaining shares and amount
    remaining_amount = rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    _test(deposit_amount - withdraw_amount, remaining_amount)

    # Withdraw remaining
    withdrawn, is_depleted = rebase_erc20_vault.withdrawTokensFromVault(
        bob, alpha_token, remaining_amount, bob, sender=teller.address
    )
    assert is_depleted
    _test(remaining_amount, withdrawn)


def test_shares_vault_transfer(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    teller,
    auction_house,
    _test,
):
    """Test transfer and share calculations"""
    # Setup initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, deposit_amount, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Transfer half
    transfer_amount = deposit_amount // 2
    transferred, is_depleted = rebase_erc20_vault.transferBalanceWithinVault(
        alpha_token, bob, sally, transfer_amount, sender=auction_house.address
    )
    assert not is_depleted
    _test(transfer_amount, transferred)

    # Check shares and amounts after transfer
    bob_amount = rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    sally_amount = rebase_erc20_vault.getTotalAmountForUser(sally, alpha_token)

    _test(deposit_amount - transfer_amount, bob_amount)
    _test(transfer_amount, sally_amount)


def test_shares_vault_share_calculations(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    _test,
):
    """Test share calculation utilities"""
    # Setup initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, deposit_amount, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Test amountToShares
    test_amount = 50 * EIGHTEEN_DECIMALS
    shares = rebase_erc20_vault.amountToShares(alpha_token, test_amount, False)
    user_shares = rebase_erc20_vault.getUserLootBoxShare(bob, alpha_token)
    _test((user_shares // 2) * (10 ** 8), shares)

    # Test sharesToAmount
    amount = rebase_erc20_vault.sharesToAmount(alpha_token, shares, False)
    _test(test_amount, amount)  # Should convert back to original amount

    # Test with rounding up
    shares_up = rebase_erc20_vault.amountToShares(alpha_token, test_amount, True)
    amount_up = rebase_erc20_vault.sharesToAmount(alpha_token, shares_up, True)
    assert shares_up >= shares  # Rounding up should give more shares
    assert amount_up >= amount  # Rounding up should give more amount


def test_shares_vault_utility_functions(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    _test,
):
    """Test utility functions in SharesVault"""
    # Setup initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, deposit_amount, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Test getVaultDataOnDeposit
    vault_data = rebase_erc20_vault.getVaultDataOnDeposit(bob, alpha_token)
    assert vault_data.hasPosition
    assert vault_data.numAssets == 1
    _test(deposit_amount, vault_data.userBalance)
    _test(deposit_amount, vault_data.totalBalance)

    # Test getUserAssetAndAmountAtIndex
    asset, amount = rebase_erc20_vault.getUserAssetAndAmountAtIndex(bob, 1)
    assert asset == alpha_token.address
    _test(deposit_amount, amount)

    # Test getUserAssetAtIndexAndHasBalance
    asset, has_balance = rebase_erc20_vault.getUserAssetAtIndexAndHasBalance(bob, 1)
    assert asset == alpha_token.address
    assert has_balance 

def test_shares_vault_share_value_increase(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    teller,
    _test,
):
    """Test share value increase when vault balance increases without deposits"""
    # Initial deposits
    deposit1 = 100 * EIGHTEEN_DECIMALS
    deposit2 = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, deposit1, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(bob, alpha_token, deposit1, sender=teller.address)
    alpha_token.transfer(rebase_erc20_vault, deposit2, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(sally, alpha_token, deposit2, sender=teller.address)

    # Record initial share values
    bob_initial_shares = rebase_erc20_vault.getUserLootBoxShare(bob, alpha_token)
    sally_initial_shares = rebase_erc20_vault.getUserLootBoxShare(sally, alpha_token)
    bob_initial_amount = rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    sally_initial_amount = rebase_erc20_vault.getTotalAmountForUser(sally, alpha_token)

    # Transfer additional tokens to vault (simulating value increase)
    additional_tokens = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, additional_tokens, sender=alpha_token_whale)

    # Check new share values
    bob_new_amount = rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    sally_new_amount = rebase_erc20_vault.getTotalAmountForUser(sally, alpha_token)
    bob_new_shares = rebase_erc20_vault.getUserLootBoxShare(bob, alpha_token)
    sally_new_shares = rebase_erc20_vault.getUserLootBoxShare(sally, alpha_token)

    # Shares should remain the same
    assert bob_new_shares == bob_initial_shares
    assert sally_new_shares == sally_initial_shares

    # But amounts should increase proportionally
    _test(bob_initial_amount * 3 // 2, bob_new_amount)  # Should be ~1.5x original
    _test(sally_initial_amount * 3 // 2, sally_new_amount)  # Should be ~1.5x original

    # Test withdrawal with increased share value
    withdraw_amount = bob_new_amount // 2
    withdrawn, is_depleted = rebase_erc20_vault.withdrawTokensFromVault(
        bob, alpha_token, withdraw_amount, bob, sender=teller.address
    )
    assert not is_depleted
    _test(withdraw_amount, withdrawn)


def test_shares_vault_share_value_decrease(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    teller,
    _test,
):
    """Test share value decrease when vault balance decreases without withdrawals"""
    # Initial deposits
    deposit1 = 100 * EIGHTEEN_DECIMALS
    deposit2 = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, deposit1, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(bob, alpha_token, deposit1, sender=teller.address)
    alpha_token.transfer(rebase_erc20_vault, deposit2, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(sally, alpha_token, deposit2, sender=teller.address)

    # Record initial share values
    bob_initial_shares = rebase_erc20_vault.getUserLootBoxShare(bob, alpha_token)
    sally_initial_shares = rebase_erc20_vault.getUserLootBoxShare(sally, alpha_token)
    bob_initial_amount = rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    sally_initial_amount = rebase_erc20_vault.getTotalAmountForUser(sally, alpha_token)

    # Simulate value decrease by transferring tokens out
    tokens_to_recover = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(alpha_token_whale, tokens_to_recover, sender=rebase_erc20_vault.address)

    # Check new share values
    bob_new_amount = rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    sally_new_amount = rebase_erc20_vault.getTotalAmountForUser(sally, alpha_token)
    bob_new_shares = rebase_erc20_vault.getUserLootBoxShare(bob, alpha_token)
    sally_new_shares = rebase_erc20_vault.getUserLootBoxShare(sally, alpha_token)

    # Shares should remain the same
    assert bob_new_shares == bob_initial_shares
    assert sally_new_shares == sally_initial_shares

    # But amounts should decrease proportionally
    _test(bob_initial_amount // 2, bob_new_amount)  # Should be ~0.5x original
    _test(sally_initial_amount // 2, sally_new_amount)  # Should be ~0.5x original

    # Test withdrawal with decreased share value
    withdraw_amount = bob_new_amount // 2
    withdrawn, is_depleted = rebase_erc20_vault.withdrawTokensFromVault(
        bob, alpha_token, withdraw_amount, bob, sender=teller.address
    )
    assert not is_depleted
    _test(withdraw_amount, withdrawn)


def test_shares_vault_share_value_multiple_changes(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    teller,
    _test,
):
    """Test share value changes with multiple balance changes"""
    # Initial deposits
    deposit1 = 100 * EIGHTEEN_DECIMALS
    deposit2 = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, deposit1, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(bob, alpha_token, deposit1, sender=teller.address)
    alpha_token.transfer(rebase_erc20_vault, deposit2, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(sally, alpha_token, deposit2, sender=teller.address)

    # Record initial values
    bob_initial_shares = rebase_erc20_vault.getUserLootBoxShare(bob, alpha_token)
    sally_initial_shares = rebase_erc20_vault.getUserLootBoxShare(sally, alpha_token)
    bob_initial_amount = rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    sally_initial_amount = rebase_erc20_vault.getTotalAmountForUser(sally, alpha_token)

    # First change: Increase value
    additional_tokens = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, additional_tokens, sender=alpha_token_whale)

    # Second change: Decrease value
    tokens_to_recover = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(alpha_token_whale, tokens_to_recover, sender=rebase_erc20_vault.address)

    # Third change: Increase value again
    additional_tokens2 = 200 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, additional_tokens2, sender=alpha_token_whale)

    # Check final values
    bob_final_amount = rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    sally_final_amount = rebase_erc20_vault.getTotalAmountForUser(sally, alpha_token)
    bob_final_shares = rebase_erc20_vault.getUserLootBoxShare(bob, alpha_token)
    sally_final_shares = rebase_erc20_vault.getUserLootBoxShare(sally, alpha_token)

    # Shares should remain the same
    assert bob_final_shares == bob_initial_shares
    assert sally_final_shares == sally_initial_shares

    # But amounts should reflect all changes
    # Initial: 200 tokens
    # After +100: 300 tokens (1.5x)
    # After -100: 200 tokens (1x)
    # After +200: 400 tokens (2x)
    _test(bob_initial_amount * 2, bob_final_amount)  # Should be 2x original
    _test(sally_initial_amount * 2, sally_final_amount)  # Should be 2x original

    # Test withdrawals with final share value
    bob_withdraw = bob_final_amount // 2
    sally_withdraw = sally_final_amount // 2
    
    withdrawn_bob, is_depleted_bob = rebase_erc20_vault.withdrawTokensFromVault(
        bob, alpha_token, bob_withdraw, bob, sender=teller.address
    )
    withdrawn_sally, is_depleted_sally = rebase_erc20_vault.withdrawTokensFromVault(
        sally, alpha_token, sally_withdraw, sally, sender=teller.address
    )
    
    assert not is_depleted_bob
    assert not is_depleted_sally
    _test(bob_withdraw, withdrawn_bob)
    _test(sally_withdraw, withdrawn_sally)


def test_shares_vault_share_calculation_edge_cases(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    _test,
):
    """Test share calculation edge cases"""
    # Test with very small amounts
    tiny_amount = 1  # 1 wei
    alpha_token.transfer(rebase_erc20_vault, tiny_amount, sender=alpha_token_whale)
    shares = rebase_erc20_vault.amountToShares(alpha_token, tiny_amount, False)
    amount = rebase_erc20_vault.sharesToAmount(alpha_token, shares, False)
    _test(tiny_amount, amount)

    # Test with very large amounts
    large_amount = 1000000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, large_amount, sender=alpha_token_whale)
    shares = rebase_erc20_vault.amountToShares(alpha_token, large_amount, False)
    amount = rebase_erc20_vault.sharesToAmount(alpha_token, shares, False)
    _test(large_amount, amount)

    # Test rounding behavior
    odd_amount = 123456789
    alpha_token.transfer(rebase_erc20_vault, odd_amount, sender=alpha_token_whale)
    shares_down = rebase_erc20_vault.amountToShares(alpha_token, odd_amount, False)
    shares_up = rebase_erc20_vault.amountToShares(alpha_token, odd_amount, True)
    assert shares_up >= shares_down
    assert shares_up - shares_down <= 1  # Should only differ by at most 1


def test_shares_vault_withdrawal_edge_cases(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    teller,
    _test,
):
    """Test withdrawal edge cases"""
    # Setup initial deposits
    deposit1 = 100 * EIGHTEEN_DECIMALS
    deposit2 = 2  # Very small deposit, but more than 1 wei
    alpha_token.transfer(rebase_erc20_vault, deposit1, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(bob, alpha_token, deposit1, sender=teller.address)
    alpha_token.transfer(rebase_erc20_vault, deposit2, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(sally, alpha_token, deposit2, sender=teller.address)

    # Test withdrawal of very small amount
    tiny_withdraw = 1
    withdrawn, is_depleted = rebase_erc20_vault.withdrawTokensFromVault(
        sally, alpha_token, tiny_withdraw, sally, sender=teller.address
    )
    assert not is_depleted  # Should not be depleted since we only withdrew half
    _test(tiny_withdraw, withdrawn)

    # Test withdrawal when total balance is very small
    # First reduce total balance
    current_balance = alpha_token.balanceOf(rebase_erc20_vault)
    alpha_token.transfer(alpha_token_whale, current_balance - 2, sender=rebase_erc20_vault.address)
    
    # Try to withdraw a small amount
    small_withdraw = 1
    withdrawn, is_depleted = rebase_erc20_vault.withdrawTokensFromVault(
        bob, alpha_token, small_withdraw, bob, sender=teller.address
    )
    assert not is_depleted  # Should not be depleted since we're only withdrawing 1 wei
    assert withdrawn > 0


def test_shares_vault_transfer_edge_cases(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    teller,
    auction_house,
    _test,
):
    """Test transfer edge cases"""
    # Setup very different share amounts
    deposit1 = 1000000 * EIGHTEEN_DECIMALS  # Large amount
    deposit2 = 2  # Tiny amount, but more than 1 wei
    alpha_token.transfer(rebase_erc20_vault, deposit1, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(bob, alpha_token, deposit1, sender=teller.address)
    alpha_token.transfer(rebase_erc20_vault, deposit2, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(sally, alpha_token, deposit2, sender=teller.address)

    # Test transfer of tiny amount
    tiny_transfer = 1
    transferred, is_depleted = rebase_erc20_vault.transferBalanceWithinVault(
        alpha_token, bob, sally, tiny_transfer, sender=auction_house.address
    )
    assert not is_depleted
    _test(tiny_transfer, transferred)

    # Test transfer when total balance is very small
    # First reduce total balance
    current_balance = alpha_token.balanceOf(rebase_erc20_vault)
    alpha_token.transfer(alpha_token_whale, current_balance - 2, sender=rebase_erc20_vault.address)
    
    # Try to transfer a small amount
    small_transfer = 1
    transferred, is_depleted = rebase_erc20_vault.transferBalanceWithinVault(
        alpha_token, bob, sally, small_transfer, sender=auction_house.address
    )
    assert not is_depleted  # Should not be depleted since we're only transferring 1 wei
    assert transferred > 0


def test_shares_vault_zero_balance_scenarios(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    _test,
):
    """Test scenarios with zero or near-zero balances"""
    # Setup initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, deposit_amount, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Test share calculations with zero balance
    alpha_token.transfer(alpha_token_whale, deposit_amount, sender=rebase_erc20_vault.address)
    
    # Should still be able to get user data
    vault_data = rebase_erc20_vault.getVaultDataOnDeposit(bob, alpha_token)
    assert vault_data.hasPosition
    assert vault_data.numAssets == 1
    assert vault_data.userBalance == 0
    assert vault_data.totalBalance == 0

    # Should still be able to get user shares
    shares = rebase_erc20_vault.getUserLootBoxShare(bob, alpha_token)
    assert shares > 0  # Shares should remain even if balance is zero

    # Should be able to get asset at index
    asset, amount = rebase_erc20_vault.getUserAssetAndAmountAtIndex(bob, 1)
    assert asset == alpha_token.address
    assert amount == 0  # Amount should be zero

    # Should still show has balance (because shares exist)
    asset, has_balance = rebase_erc20_vault.getUserAssetAtIndexAndHasBalance(bob, 1)
    assert asset == alpha_token.address
    assert has_balance  # Should be true because shares exist 