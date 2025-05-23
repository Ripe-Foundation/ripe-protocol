import pytest
import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS


def test_stab_vault_deposit_validation(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    control_room,
    bob,
    teller,
    mock_price_source,
):
    """Test deposit validation logic in StabVault"""
    # Set mock price
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)

    # Test deposit with zero address
    with boa.reverts("invalid user or asset"):
        stability_pool.depositTokensInVault(ZERO_ADDRESS, alpha_token, 100, sender=teller.address)
    with boa.reverts("invalid user or asset"):
        stability_pool.depositTokensInVault(bob, ZERO_ADDRESS, 100, sender=teller.address)

    # Test deposit with zero amount
    with boa.reverts("invalid deposit amount"):
        stability_pool.depositTokensInVault(bob, alpha_token, 0, sender=teller.address)

    # Test deposit when paused
    stability_pool.pause(True, sender=control_room.address)
    with boa.reverts("contract paused"):
        stability_pool.depositTokensInVault(bob, alpha_token, 100, sender=teller.address)
    stability_pool.pause(False, sender=control_room.address)

    # Test deposit with amount larger than balance
    large_amount = 1000000 * EIGHTEEN_DECIMALS
    small_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, small_amount, sender=alpha_token_whale)
    deposited = stability_pool.depositTokensInVault(bob, alpha_token, large_amount, sender=teller.address)
    assert deposited == small_amount  # Should only deposit what's available


def test_stab_vault_initial_deposit(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    mock_price_source,
):
    """Test initial deposit and share calculation"""
    # Set mock price
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    deposited = stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)
    assert deposited == deposit_amount

    # Check shares
    shares = stability_pool.userBalances(bob, alpha_token)
    assert shares != 0

    # Check total value
    user_value = stability_pool.getTotalUserValue(bob, alpha_token)
    total_value = stability_pool.getTotalValue(alpha_token)
    assert total_value == deposit_amount == user_value


def test_stab_vault_multiple_deposits(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
    teller,
    mock_price_source,
):
    """Test multiple deposits and share calculations"""
    # Set mock price
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)

    # First deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    deposited = stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)
    assert deposited == deposit_amount

    # Second deposit
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    deposited = stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount, sender=teller.address)
    assert deposited == deposit_amount

    # Check shares
    bob_shares = stability_pool.userBalances(bob, alpha_token)
    alice_shares = stability_pool.userBalances(alice, alpha_token)
    assert bob_shares == alice_shares
    assert bob_shares != 0

    # Check user values
    bob_user_value = stability_pool.getTotalUserValue(bob, alpha_token)
    alice_user_value = stability_pool.getTotalUserValue(alice, alpha_token)
    assert bob_user_value == alice_user_value
    assert bob_user_value == deposit_amount

    # Check total value
    total_value = stability_pool.getTotalValue(alpha_token)
    assert total_value == deposit_amount * 2


def test_stab_vault_withdrawal(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    mock_price_source,
):
    """Test withdrawal functionality"""
    # Set mock price
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    deposited = stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)
    assert deposited == deposit_amount

    # Withdraw half
    withdraw_amount = deposit_amount // 2
    withdrawn, is_depleted = stability_pool.withdrawTokensFromVault(bob, alpha_token, withdraw_amount, bob, sender=teller.address)
    assert withdrawn == withdraw_amount
    assert not is_depleted

    # Check remaining balance
    remaining = stability_pool.getTotalAmountForUser(bob, alpha_token)
    assert remaining == deposit_amount - withdraw_amount


def test_stab_vault_transfer(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
    teller,
    mock_price_source,
    auction_house,
):
    """Test transfer functionality"""
    # Set mock price
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    deposited = stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)
    assert deposited == deposit_amount

    # Transfer half
    transfer_amount = deposit_amount // 2
    transferred, is_depleted = stability_pool.transferBalanceWithinVault(alpha_token, bob, alice, transfer_amount, sender=auction_house.address)
    assert transferred == transfer_amount
    assert not is_depleted

    # Check balances
    bob_balance = stability_pool.getTotalAmountForUser(bob, alpha_token)
    alice_balance = stability_pool.getTotalAmountForUser(alice, alpha_token)
    assert bob_balance == deposit_amount - transfer_amount
    assert alice_balance == transfer_amount


def test_stab_vault_share_calculations(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    mock_price_source,
):
    """Test share calculation utilities"""
    # Set mock price
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    deposited = stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)
    assert deposited == deposit_amount

    # Test valueToShares
    shares = stability_pool.valueToShares(alpha_token, deposit_amount, False)
    assert shares != 0

    # Test sharesToValue
    value = stability_pool.sharesToValue(alpha_token, shares, False)
    assert value == deposit_amount


def test_stab_vault_share_value_with_claimable_assets(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    sally,
    teller,
    auction_house,
    mock_price_source,
):
    """Test share value changes when claimable assets are added/removed"""
    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Initial deposits
    deposit1 = 100 * EIGHTEEN_DECIMALS
    deposit2 = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit1, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit1, sender=teller.address)
    alpha_token.transfer(stability_pool, deposit2, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(sally, alpha_token, deposit2, sender=teller.address)

    # Record initial values
    bob_initial_value = stability_pool.getTotalUserValue(bob, alpha_token)
    sally_initial_value = stability_pool.getTotalUserValue(sally, alpha_token)
    total_initial_value = stability_pool.getTotalValue(alpha_token)

    # Add claimable asset (simulating liquidation)
    claimable_amount = 110 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,  # stab asset
        deposit1,     # stab asset amount
        bravo_token,   # liq asset
        claimable_amount,  # liq amount
        ZERO_ADDRESS,  # recipient (burn)
        alpha_token,  # green token
        sender=auction_house.address
    )

    # Check new values after adding claimable asset
    bob_new_value = stability_pool.getTotalUserValue(bob, alpha_token)
    sally_new_value = stability_pool.getTotalUserValue(sally, alpha_token)
    total_new_value = stability_pool.getTotalValue(alpha_token)

    # Values should increase for both users after liquidation
    assert bob_new_value > bob_initial_value
    assert sally_new_value > sally_initial_value
    assert total_new_value > total_initial_value  # Total value increases due to claimable asset


def test_stab_vault_share_calculation_edge_cases(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    price_desk,
    mock_price_source,
    _test,
):
    """Test share calculation edge cases"""
    # Set mock price
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)

    # Test with very small amounts
    tiny_amount = 1  # 1 wei
    alpha_token.transfer(stability_pool, tiny_amount, sender=alpha_token_whale)
    tiny_value = price_desk.getUsdValue(alpha_token, tiny_amount)
    shares = stability_pool.valueToShares(alpha_token, tiny_value, False)
    value = stability_pool.sharesToValue(alpha_token, shares, False)
    _test(tiny_value, value)

    # Test with very large amounts
    large_amount = 1000000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, large_amount, sender=alpha_token_whale)
    large_value = price_desk.getUsdValue(alpha_token, large_amount)
    shares = stability_pool.valueToShares(alpha_token, large_value, False)
    value = stability_pool.sharesToValue(alpha_token, shares, False)
    _test(large_value, value)

    # Test rounding behavior
    odd_amount = 123456789
    alpha_token.transfer(stability_pool, odd_amount, sender=alpha_token_whale)
    odd_value = price_desk.getUsdValue(alpha_token, odd_amount)
    shares_down = stability_pool.valueToShares(alpha_token, odd_value, False)
    shares_up = stability_pool.valueToShares(alpha_token, odd_value, True)
    assert shares_up >= shares_down
    assert shares_up - shares_down <= 1  # Should only differ by at most 1


def test_stab_vault_withdrawal_edge_cases(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    teller,
    mock_price_source,
    _test,
):
    """Test withdrawal edge cases"""
    # Set mock price
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)

    # Setup very different share amounts
    deposit1 = 1000000 * EIGHTEEN_DECIMALS  # Large amount
    deposit2 = 2  # Tiny amount, but more than 1 wei
    alpha_token.transfer(stability_pool, deposit1, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit1, sender=teller.address)
    alpha_token.transfer(stability_pool, deposit2, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(sally, alpha_token, deposit2, sender=teller.address)

    # Test withdrawal of very small amount
    tiny_withdraw = 1
    withdrawn, is_depleted = stability_pool.withdrawTokensFromVault(
        sally, alpha_token, tiny_withdraw, sally, sender=teller.address
    )
    assert not is_depleted  # Should not be depleted since we only withdrew half
    _test(tiny_withdraw, withdrawn)

    # Test withdrawal when total balance is very small
    # First reduce total balance
    current_balance = alpha_token.balanceOf(stability_pool)
    alpha_token.transfer(alpha_token_whale, current_balance - 2, sender=stability_pool.address)
    
    # Try to withdraw a small amount
    small_withdraw = 1
    withdrawn, is_depleted = stability_pool.withdrawTokensFromVault(
        bob, alpha_token, small_withdraw, bob, sender=teller.address
    )
    assert not is_depleted  # Should not be depleted since we're only withdrawing 1 wei
    assert withdrawn != 0


def test_stab_vault_zero_balance_scenarios(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    mock_price_source,
):
    """Test scenarios with zero or near-zero balances"""
    # Set mock price
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)

    # Setup initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Test share calculations with zero balance
    alpha_token.transfer(alpha_token_whale, deposit_amount, sender=stability_pool.address)
    
    # Should still be able to get user data
    vault_data = stability_pool.getVaultDataOnDeposit(bob, alpha_token)
    assert vault_data.hasPosition
    assert vault_data.numAssets == 1
    assert vault_data.userBalance == 0
    assert vault_data.totalBalance == 0

    # Should still be able to get user shares
    shares = stability_pool.getUserLootBoxShare(bob, alpha_token)
    assert shares != 0  # Shares should remain even if balance is zero

    # cannot borrow against stability pool positions
    asset, amount = stability_pool.getUserAssetAndAmountAtIndex(bob, 1)
    assert asset == ZERO_ADDRESS
    assert amount == 0

    # Should still show has balance (because shares exist)
    asset, has_balance = stability_pool.getUserAssetAtIndexAndHasBalance(bob, 1)
    assert asset == alpha_token.address
    assert has_balance


def test_stab_vault_multiple_assets(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    sally,
    teller,
    price_desk,
    mock_price_source,
    _test,
):
    """Test scenarios with multiple assets in the vault"""
    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Setup deposits for both assets
    alpha_deposit = 100 * EIGHTEEN_DECIMALS
    bravo_deposit = 200 * EIGHTEEN_DECIMALS
    
    # Deposit alpha token
    alpha_token.transfer(stability_pool, alpha_deposit, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, alpha_deposit, sender=teller.address)
    
    # Deposit bravo token
    bravo_token.transfer(stability_pool, bravo_deposit, sender=bravo_token_whale)
    stability_pool.depositTokensInVault(sally, bravo_token, bravo_deposit, sender=teller.address)

    # Get USD values
    alpha_value = price_desk.getUsdValue(alpha_token, alpha_deposit)
    bravo_value = price_desk.getUsdValue(bravo_token, bravo_deposit)

    # Check total values for each asset
    alpha_total = stability_pool.getTotalValue(alpha_token)
    bravo_total = stability_pool.getTotalValue(bravo_token)
    _test(alpha_value, alpha_total)
    _test(bravo_value, bravo_total)

    # Check user values
    bob_alpha_value = stability_pool.getTotalUserValue(bob, alpha_token)
    sally_bravo_value = stability_pool.getTotalUserValue(sally, bravo_token)
    _test(alpha_value, bob_alpha_value)
    _test(bravo_value, sally_bravo_value)

    # Test withdrawals for each asset
    alpha_withdraw = alpha_deposit // 2
    bravo_withdraw = bravo_deposit // 2

    # Withdraw alpha
    withdrawn_alpha, is_depleted_alpha = stability_pool.withdrawTokensFromVault(
        bob, alpha_token, alpha_withdraw, bob, sender=teller.address
    )
    assert not is_depleted_alpha
    _test(alpha_withdraw, withdrawn_alpha)

    # Withdraw bravo
    withdrawn_bravo, is_depleted_bravo = stability_pool.withdrawTokensFromVault(
        sally, bravo_token, bravo_withdraw, sally, sender=teller.address
    )
    assert not is_depleted_bravo
    _test(bravo_withdraw, withdrawn_bravo)

    # Check remaining values
    bob_alpha_remaining = stability_pool.getTotalUserValue(bob, alpha_token)
    sally_bravo_remaining = stability_pool.getTotalUserValue(sally, bravo_token)
    _test(alpha_value // 2, bob_alpha_remaining)
    _test(bravo_value // 2, sally_bravo_remaining)


def test_stab_vault_liquidation_profit(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    sally,
    teller,
    auction_house,
    mock_price_source,
):
    """Test liquidation when claimable asset is worth more than stability pool asset"""
    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Initial deposits
    deposit1 = 100 * EIGHTEEN_DECIMALS
    deposit2 = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit1, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit1, sender=teller.address)
    alpha_token.transfer(stability_pool, deposit2, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(sally, alpha_token, deposit2, sender=teller.address)

    # Record initial values
    bob_initial_value = stability_pool.getTotalUserValue(bob, alpha_token)
    sally_initial_value = stability_pool.getTotalUserValue(sally, alpha_token)
    total_initial_value = stability_pool.getTotalValue(alpha_token)

    # Claimable asset worth 50% more than stability pool asset
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,  # stab asset
        deposit1,     # stab asset amount
        bravo_token,  # liq asset
        claimable_amount,  # liq amount
        ZERO_ADDRESS,  # recipient (burn)
        alpha_token,  # green token
        sender=auction_house.address
    )

    # Check values after profitable liquidation
    bob_new_value = stability_pool.getTotalUserValue(bob, alpha_token)
    sally_new_value = stability_pool.getTotalUserValue(sally, alpha_token)
    total_new_value = stability_pool.getTotalValue(alpha_token)

    assert bob_new_value > bob_initial_value  # Bob should gain more since he provided the stability pool asset
    assert sally_new_value > sally_initial_value  # Sally should also gain, but less than Bob
    assert total_new_value > total_initial_value  # Total value should increase


def test_stab_vault_liquidation_loss(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    sally,
    teller,
    auction_house,
    mock_price_source,
):
    """Test liquidation when claimable asset is worth less than stability pool asset"""
    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Initial deposits
    deposit1 = 100 * EIGHTEEN_DECIMALS
    deposit2 = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit1, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit1, sender=teller.address)
    alpha_token.transfer(stability_pool, deposit2, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(sally, alpha_token, deposit2, sender=teller.address)

    # Record initial values
    bob_initial_value = stability_pool.getTotalUserValue(bob, alpha_token)
    sally_initial_value = stability_pool.getTotalUserValue(sally, alpha_token)
    total_initial_value = stability_pool.getTotalValue(alpha_token)

    # Claimable asset worth 50% less than stability pool asset
    claimable_amount = 50 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,  # stab asset
        deposit1,     # stab asset amount
        bravo_token,  # liq asset
        claimable_amount,  # liq amount
        ZERO_ADDRESS,  # recipient (burn)
        alpha_token,  # green token
        sender=auction_house.address
    )

    # Check values after loss
    bob_new_value = stability_pool.getTotalUserValue(bob, alpha_token)
    sally_new_value = stability_pool.getTotalUserValue(sally, alpha_token)
    total_new_value = stability_pool.getTotalValue(alpha_token)

    assert bob_new_value < bob_initial_value  # Bob should lose more since he provided the stability pool asset
    assert sally_new_value < sally_initial_value  # Sally should also lose, but less than Bob
    assert total_new_value < total_initial_value  # Total value should decrease


def test_stab_vault_liquidation_sequence(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    sally,
    teller,
    auction_house,
    mock_price_source,
):
    """Test that multiple liquidations accumulate correctly"""
    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Initial deposits
    deposit1 = 100 * EIGHTEEN_DECIMALS
    deposit2 = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit1, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit1, sender=teller.address)
    alpha_token.transfer(stability_pool, deposit2, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(sally, alpha_token, deposit2, sender=teller.address)

    # Record initial values
    bob_initial_value = stability_pool.getTotalUserValue(bob, alpha_token)
    sally_initial_value = stability_pool.getTotalUserValue(sally, alpha_token)
    total_initial_value = stability_pool.getTotalValue(alpha_token)

    # First liquidation - profitable
    claimable_amount1 = 120 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount1, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,  # stab asset
        deposit1 // 2,  # stab asset amount
        bravo_token,  # liq asset
        claimable_amount1,  # liq amount
        ZERO_ADDRESS,  # recipient (burn)
        alpha_token,  # green token
        sender=auction_house.address
    )

    # Record values after first liquidation
    bob_value_after_first = stability_pool.getTotalUserValue(bob, alpha_token)
    sally_value_after_first = stability_pool.getTotalUserValue(sally, alpha_token)
    total_value_after_first = stability_pool.getTotalValue(alpha_token)

    # Second liquidation - loss
    claimable_amount2 = 30 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount2, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,  # stab asset
        deposit1 // 2,  # stab asset amount
        bravo_token,  # liq asset
        claimable_amount2,  # liq amount
        ZERO_ADDRESS,  # recipient (burn)
        alpha_token,  # green token
        sender=auction_house.address
    )

    # Check final values
    bob_final_value = stability_pool.getTotalUserValue(bob, alpha_token)
    sally_final_value = stability_pool.getTotalUserValue(sally, alpha_token)
    total_final_value = stability_pool.getTotalValue(alpha_token)

    # Values should be between initial and first liquidation values
    assert bob_final_value > bob_initial_value
    assert bob_final_value < bob_value_after_first
    assert sally_final_value > sally_initial_value
    assert sally_final_value < sally_value_after_first
    assert total_final_value > total_initial_value
    assert total_final_value < total_value_after_first


def test_stab_vault_liquidation_tiny_amount(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    sally,
    teller,
    auction_house,
    mock_price_source,
):
    """Test liquidation with a very small amount (1 wei)"""
    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Initial deposits
    deposit1 = 100 * EIGHTEEN_DECIMALS
    deposit2 = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit1, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit1, sender=teller.address)
    alpha_token.transfer(stability_pool, deposit2, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(sally, alpha_token, deposit2, sender=teller.address)

    # Very small liquidation
    tiny_amount = 1  # 1 wei
    bravo_token.transfer(stability_pool, tiny_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,  # stab asset
        tiny_amount,  # stab asset amount
        bravo_token,  # liq asset
        tiny_amount,  # liq amount
        ZERO_ADDRESS,  # recipient (burn)
        alpha_token,  # green token
        sender=auction_house.address
    )

    # Check values after tiny liquidation
    bob_value_after_tiny = stability_pool.getTotalUserValue(bob, alpha_token)
    sally_value_after_tiny = stability_pool.getTotalUserValue(sally, alpha_token)
    total_value_after_tiny = stability_pool.getTotalValue(alpha_token)

    # Values should be very close to initial values
    assert abs(bob_value_after_tiny - deposit1) < 2  # Allow for 1 wei difference
    assert abs(sally_value_after_tiny - deposit2) < 2
    assert abs(total_value_after_tiny - (deposit1 + deposit2)) < 2


def test_stab_vault_swap_validation(
    stability_pool,
    alpha_token,
    bravo_token,
    bravo_token_whale,
    alpha_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
):
    """Test validation checks in swapForLiquidatedCollateral"""
    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Initial deposit
    deposit = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit, sender=teller.address)

    # Test invalid stability pool asset
    with boa.reverts("stab asset not supported"):
        stability_pool.swapForLiquidatedCollateral(
            ZERO_ADDRESS,  # invalid stab asset
            deposit,
            bravo_token,
            deposit,
            ZERO_ADDRESS,
            alpha_token,
            sender=auction_house.address
        )

    # Test invalid liquidated asset
    with boa.reverts("invalid liq asset"):
        stability_pool.swapForLiquidatedCollateral(
            alpha_token,
            deposit,
            ZERO_ADDRESS,  # invalid liq asset
            deposit,
            ZERO_ADDRESS,
            alpha_token,
            sender=auction_house.address
        )

    bravo_token.transfer(stability_pool, deposit, sender=bravo_token_whale)

    # Test invalid green token
    with boa.reverts("must be green token"):
        stability_pool.swapForLiquidatedCollateral(
            alpha_token,
            deposit,
            bravo_token,
            deposit,
            ZERO_ADDRESS,
            ZERO_ADDRESS, # invalid green token
            sender=auction_house.address
        )

    # Test unauthorized caller
    with boa.reverts("only AuctionHouse allowed"):
        stability_pool.swapForLiquidatedCollateral(
            alpha_token,
            deposit,
            bravo_token,
            deposit,
            ZERO_ADDRESS,
            alpha_token,
            sender=bob  # unauthorized sender
        )


def test_stab_vault_swap_claimable_balance(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    sally,
    teller,
    auction_house,
    mock_price_source,
):
    """Test that claimable balances are properly registered"""
    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Initial deposits
    deposit1 = 100 * EIGHTEEN_DECIMALS
    deposit2 = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit1, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit1, sender=teller.address)
    alpha_token.transfer(stability_pool, deposit2, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(sally, alpha_token, deposit2, sender=teller.address)

    # Record initial claimable balances
    initial_claimable = stability_pool.claimableBalances(alpha_token, bravo_token)

    # Add claimable asset
    claimable_amount = 110 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,  # stab asset
        deposit1,     # stab asset amount
        bravo_token,  # liq asset
        claimable_amount,  # liq amount
        ZERO_ADDRESS,  # recipient (burn)
        alpha_token,  # green token
        sender=auction_house.address
    )

    # Check claimable balances
    next_claimable = stability_pool.claimableBalances(alpha_token, bravo_token)
    assert next_claimable == claimable_amount

    # Only Bob should have claimable balance
    assert next_claimable > initial_claimable
    assert stability_pool.totalClaimableBalances(bravo_token) == next_claimable


def test_stab_vault_swap_burn(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
):
    """Test burn behavior in swapForLiquidatedCollateral when recipient is ZERO_ADDRESS"""
    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Initial deposits
    deposit = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit, sender=teller.address)
  
    # Test burn (ZERO_ADDRESS recipient)
    claimable_amount = 110 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)    

    stability_pool.swapForLiquidatedCollateral(
        alpha_token,  # stab asset
        deposit,      # stab asset amount
        bravo_token,  # liq asset
        claimable_amount,  # liq amount
        ZERO_ADDRESS,  # recipient (burn)
        alpha_token,  # green token
        sender=auction_house.address
    )

    # Check balances after burn
    assert alpha_token.balanceOf(stability_pool) == 0  # Stability pool asset should be burned
    assert bravo_token.balanceOf(stability_pool) == claimable_amount  # claimable added


def test_stab_vault_swap_transfer(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    sally,
    teller,
    auction_house,
    mock_price_source,
):
    """Test transfer behavior in swapForLiquidatedCollateral when recipient is non-zero"""
    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Initial deposits
    deposit = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit, sender=teller.address)
    
    # Test transfer (non-zero recipient)
    claimable_amount = 110 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,  # stab asset
        deposit,      # stab asset amount
        bravo_token,  # liq asset
        claimable_amount,  # liq amount
        sally,        # recipient (transfer)
        alpha_token,  # green token
        sender=auction_house.address
    )

    # Check balances after transfer
    assert alpha_token.balanceOf(stability_pool) == 0
    assert bravo_token.balanceOf(stability_pool) == claimable_amount
    assert alpha_token.balanceOf(sally) == deposit # Recipient should receive stability pool asset


def test_stab_vault_swap_share_calculation(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    sally,
    teller,
    auction_house,
    mock_price_source,
):
    """Test share calculations during swapForLiquidatedCollateral"""
    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Initial deposits with different amounts
    deposit1 = 100 * EIGHTEEN_DECIMALS
    deposit2 = 50 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit1, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit1, sender=teller.address)
    alpha_token.transfer(stability_pool, deposit2, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(sally, alpha_token, deposit2, sender=teller.address)

    # Record initial shares
    bob_initial_shares = stability_pool.userBalances(bob, alpha_token)
    sally_initial_shares = stability_pool.userBalances(sally, alpha_token)
    total_initial_shares = stability_pool.totalBalances(alpha_token)

    # Add claimable asset
    claimable_amount = 110 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,  # stab asset
        deposit1,     # stab asset amount
        bravo_token,  # liq asset
        claimable_amount,  # liq amount
        ZERO_ADDRESS,  # recipient (burn)
        alpha_token,  # green token
        sender=auction_house.address
    )

    # Check shares after swap
    bob_shares = stability_pool.userBalances(bob, alpha_token)
    sally_shares = stability_pool.userBalances(sally, alpha_token)
    total_shares = stability_pool.totalBalances(alpha_token)

    # Bob's share ratio should remain the same (2/3)
    assert abs(bob_shares / total_shares - bob_initial_shares / total_initial_shares) < 1e-10
    # Sally's share ratio should remain the same (1/3)
    assert abs(sally_shares / total_shares - sally_initial_shares / total_initial_shares) < 1e-10
    # Total shares should increase
    assert total_shares >= total_initial_shares  # Allow for equal in case of rounding


def test_stab_vault_claimable_asset_data(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    sally,
    teller,
    auction_house,
    mock_price_source,
):
    """Test that claimable asset data structures are properly updated"""
    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(charlie_token, price)

    # Initial deposits
    deposit1 = 100 * EIGHTEEN_DECIMALS
    deposit2 = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit1, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit1, sender=teller.address)
    alpha_token.transfer(stability_pool, deposit2, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(sally, alpha_token, deposit2, sender=teller.address)

    # Check initial state
    assert stability_pool.numClaimableAssets(alpha_token) == 0
    assert stability_pool.indexOfClaimableAsset(alpha_token, bravo_token) == 0

    # Add first claimable asset
    claimable_amount1 = 110 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount1, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,  # stab asset
        deposit1,     # stab asset amount
        bravo_token,  # liq asset
        claimable_amount1,  # liq amount
        ZERO_ADDRESS,  # recipient (burn)
        alpha_token,  # green token
        sender=auction_house.address
    )

    # Check state after first claimable asset
    assert stability_pool.indexOfClaimableAsset(alpha_token, bravo_token) == 1
    assert stability_pool.claimableAssets(alpha_token, 1) == bravo_token.address
    assert stability_pool.numClaimableAssets(alpha_token) == 2

    # Add second claimable asset (charlie token)
    claimable_amount2 = 120 * (10 ** charlie_token.decimals())
    charlie_token.transfer(stability_pool, claimable_amount2, sender=charlie_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,  # stab asset
        deposit2,     # stab asset amount
        charlie_token,  # liq asset
        claimable_amount2,  # liq amount
        ZERO_ADDRESS,  # recipient (burn)
        alpha_token,  # green token
        sender=auction_house.address
    )

    # Check state after second claimable asset
    assert stability_pool.indexOfClaimableAsset(alpha_token, charlie_token) == 2
    assert stability_pool.claimableAssets(alpha_token, 2) == charlie_token.address
    assert stability_pool.numClaimableAssets(alpha_token) == 3

    # Verify claimable balances for both assets
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == claimable_amount1
    assert stability_pool.claimableBalances(alpha_token, charlie_token) == claimable_amount2
    assert stability_pool.totalClaimableBalances(bravo_token) == claimable_amount1
    assert stability_pool.totalClaimableBalances(charlie_token) == claimable_amount2

    # Test invalid index access
    assert stability_pool.claimableAssets(alpha_token, 0) == ZERO_ADDRESS
    assert stability_pool.claimableAssets(alpha_token, 3) == ZERO_ADDRESS

    # Test non-existent claimable asset
    assert stability_pool.indexOfClaimableAsset(alpha_token, ZERO_ADDRESS) == 0  # Should return 0 for non-existent asset
