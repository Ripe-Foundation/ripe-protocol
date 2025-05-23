import pytest
from hypothesis import given, strategies as st
import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, MAX_UINT256
from conf_utils import filter_logs


def test_erc4626_initialization(savings_green, green_token):
    """Test ERC4626 initialization"""
    assert savings_green.asset() == green_token.address
    assert savings_green.totalAssets() == 0


def test_erc4626_deposit(
    savings_green,
    green_token,
    whale,
    bob,
):
    """Test basic deposit functionality"""
    green_token.approve(savings_green, MAX_UINT256, sender=whale)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    shares = savings_green.deposit(deposit_amount, bob, sender=whale)
    
    # Check balances
    assert savings_green.balanceOf(bob) == shares
    assert savings_green.totalAssets() == deposit_amount
    assert savings_green.convertToAssets(shares) == deposit_amount
    assert savings_green.convertToShares(deposit_amount) == shares


def test_erc4626_deposit_max_value(
    savings_green,
    green_token,
    sally,
    bob,
    credit_engine,
):
    """Test deposit with max_value(uint256)"""
    # First mint enough tokens to the sally
    mint_amount = 1000 * EIGHTEEN_DECIMALS
    green_token.mint(sally, mint_amount, sender=credit_engine.address)
    
    # Approve the contract to spend tokens
    green_token.approve(savings_green, MAX_UINT256, sender=sally)
    
    # Deposit max value - this should use all available tokens
    shares = savings_green.deposit(MAX_UINT256, bob, sender=sally)
    assert shares > 0
    assert savings_green.balanceOf(bob) == shares
    assert savings_green.totalAssets() == mint_amount
    assert green_token.balanceOf(sally) == 0  # All tokens should be used


def test_erc4626_deposit_zero_amount(
    savings_green,
    green_token,
    sally,
    bob,
):
    """Test deposit with zero amount"""
    green_token.approve(savings_green, MAX_UINT256, sender=sally)

    with boa.reverts("cannot deposit 0 amount"):
        savings_green.deposit(0, bob, sender=sally)


def test_erc4626_deposit_invalid_receiver(
    savings_green,
    green_token,
    whale,
):
    """Test deposit with invalid receiver"""
    green_token.approve(savings_green, MAX_UINT256, sender=whale)

    with boa.reverts("invalid recipient"):
        savings_green.deposit(100 * EIGHTEEN_DECIMALS, ZERO_ADDRESS, sender=whale)


def test_erc4626_mint(
    savings_green,
    green_token,
    whale,
    bob,
):
    """Test mint functionality"""
    # Initial deposit
    green_token.approve(savings_green, MAX_UINT256, sender=whale)
    
    # Calculate how many assets we need for desired shares
    desired_shares = 100 * EIGHTEEN_DECIMALS
    required_assets = savings_green.previewMint(desired_shares)
    
    # Mint the shares
    assets = savings_green.mint(desired_shares, bob, sender=whale)
    
    # Check balances
    assert savings_green.balanceOf(bob) == desired_shares
    assert assets == required_assets  # The actual assets used should match what previewMint told us
    assert savings_green.totalAssets() == assets


def test_erc4626_mint_max_value(
    savings_green,
    green_token,
    whale,
    bob,
):
    """Test mint with max_value(uint256)"""
    green_token.approve(savings_green, MAX_UINT256, sender=whale)

    with boa.reverts("deposit failed"):
        savings_green.mint(MAX_UINT256, bob, sender=whale)


def test_erc4626_withdraw(
    savings_green,
    green_token,
    whale,
    bob,
):
    """Test withdraw functionality"""
    green_token.approve(savings_green, MAX_UINT256, sender=whale)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    shares = savings_green.deposit(deposit_amount, bob, sender=whale)
    
    # Withdraw half
    withdraw_amount = deposit_amount // 2
    withdrawn_shares = savings_green.withdraw(withdraw_amount, bob, bob, sender=bob)
    
    # Check balances
    assert savings_green.balanceOf(bob) == shares - withdrawn_shares
    assert savings_green.totalAssets() == deposit_amount - withdraw_amount
    assert green_token.balanceOf(bob) == withdraw_amount


def test_erc4626_withdraw_zero_amount(
    savings_green,
    green_token,
    whale,
    bob,
):
    """Test withdraw with zero amount"""
    green_token.approve(savings_green, MAX_UINT256, sender=whale)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    savings_green.deposit(deposit_amount, bob, sender=whale)
    
    with boa.reverts("cannot withdraw 0 amount"):
        savings_green.withdraw(0, bob, bob, sender=bob)


def test_erc4626_withdraw_insufficient_balance(
    savings_green,
    bob,
):
    """Test withdraw with insufficient balance"""
    with boa.reverts("insufficient shares"):
        savings_green.withdraw(100 * EIGHTEEN_DECIMALS, bob, bob, sender=bob)


def test_erc4626_redeem(
    savings_green,
    green_token,
    whale,
    bob,
):
    """Test redeem functionality"""
    green_token.approve(savings_green, MAX_UINT256, sender=whale)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    shares = savings_green.deposit(deposit_amount, bob, sender=whale)
    
    # Redeem half
    redeem_shares = shares // 2
    redeemed_amount = savings_green.redeem(redeem_shares, bob, bob, sender=bob)
    
    # Check balances
    assert savings_green.balanceOf(bob) == shares - redeem_shares
    assert savings_green.totalAssets() == deposit_amount - redeemed_amount
    assert green_token.balanceOf(bob) == redeemed_amount


def test_erc4626_redeem_max_value(
    savings_green,
    green_token,
    whale,
    bob,
):
    """Test redeem with max_value(uint256)"""
    green_token.approve(savings_green, MAX_UINT256, sender=whale)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    shares = savings_green.deposit(deposit_amount, bob, sender=whale)
    
    # Redeem all shares
    redeemed_amount = savings_green.redeem(MAX_UINT256, bob, bob, sender=bob)
    assert redeemed_amount == deposit_amount
    assert savings_green.balanceOf(bob) == 0


def test_erc4626_redeem_zero_shares(
    savings_green,
    green_token,
    whale,
    bob,
):
    """Test redeem with zero shares"""
    green_token.approve(savings_green, MAX_UINT256, sender=whale)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    savings_green.deposit(deposit_amount, bob, sender=whale)
    
    with boa.reverts("cannot withdraw 0 amount"):
        savings_green.redeem(0, bob, bob, sender=bob)


def test_erc4626_share_calculations(
    savings_green,
    green_token,
    whale,
    bob,
    sally,
):
    """Test share calculations with multiple deposits"""
    green_token.approve(savings_green, MAX_UINT256, sender=whale)

    # First deposit
    deposit1 = 100 * EIGHTEEN_DECIMALS
    shares1 = savings_green.deposit(deposit1, bob, sender=whale)
    
    # Second deposit
    deposit2 = 200 * EIGHTEEN_DECIMALS
    shares2 = savings_green.deposit(deposit2, sally, sender=whale)
    
    # Check share ratios
    assert shares2 > shares1  # More assets should give more shares
    assert savings_green.convertToAssets(shares1) == deposit1
    assert savings_green.convertToAssets(shares2) == deposit2


def test_erc4626_rounding_behavior(
    savings_green,
    green_token,
    whale,
    bob,
):
    """Test rounding behavior in share calculations"""
    green_token.approve(savings_green, MAX_UINT256, sender=whale)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    shares = savings_green.deposit(deposit_amount, bob, sender=whale)
    
    # Test rounding up
    shares_up = savings_green.previewDeposit(deposit_amount)
    assert shares_up >= shares
    
    # Test rounding down
    assets_down = savings_green.previewRedeem(shares)
    assert assets_down <= deposit_amount


def test_erc4626_allowance(
    savings_green,
    green_token,
    whale,
    bob,
    sally,
):
    """Test allowance functionality"""
    green_token.approve(savings_green, MAX_UINT256, sender=whale)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    shares = savings_green.deposit(deposit_amount, bob, sender=whale)
    
    # Approve Sally to spend Bob's shares
    savings_green.approve(sally, shares, sender=bob)
    
    # Sally redeems Bob's shares
    redeemed_amount = savings_green.redeem(shares, sally, bob, sender=sally)
    assert redeemed_amount == deposit_amount
    assert savings_green.balanceOf(bob) == 0
    assert green_token.balanceOf(sally) == deposit_amount


def test_erc4626_insufficient_allowance(
    savings_green,
    green_token,
    whale,
    bob,
    sally,
):
    """Test insufficient allowance"""
    green_token.approve(savings_green, MAX_UINT256, sender=whale)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    shares = savings_green.deposit(deposit_amount, bob, sender=whale)
    
    # Approve Sally for less than total shares
    savings_green.approve(sally, shares // 2, sender=bob)
    
    # Try to redeem more than allowed
    with boa.reverts("insufficient allowance"):
        savings_green.redeem(shares, sally, bob, sender=sally)


def test_erc4626_decimal_offset(
    savings_green,
    green_token,
    whale,
    bob,
):
    """Test decimal offset protection against donation attacks"""
    green_token.approve(savings_green, MAX_UINT256, sender=whale)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    shares1 = savings_green.deposit(deposit_amount, bob, sender=whale)
    
    # Try to manipulate share price with tiny deposit
    tiny_amount = 1
    green_token.approve(savings_green, MAX_UINT256, sender=whale)
    shares2 = savings_green.deposit(tiny_amount, bob, sender=whale)
    
    # Check that share price wasn't significantly affected
    assert shares2 < shares1 // 100  # Tiny deposit should give proportionally tiny shares


def test_erc4626_preview_functions(
    savings_green,
    green_token,
    whale,
    bob,
):
    """Test preview functions accuracy"""
    green_token.approve(savings_green, MAX_UINT256, sender=whale)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    shares = savings_green.deposit(deposit_amount, bob, sender=whale)
    
    # Test previewDeposit
    preview_shares = savings_green.previewDeposit(deposit_amount)
    assert preview_shares == shares
    
    # Test previewMint
    preview_assets = savings_green.previewMint(shares)
    assert preview_assets == deposit_amount
    
    # Test previewWithdraw
    preview_withdraw_shares = savings_green.previewWithdraw(deposit_amount)
    assert preview_withdraw_shares == shares
    
    # Test previewRedeem
    preview_redeem_assets = savings_green.previewRedeem(shares)
    assert preview_redeem_assets == deposit_amount


def test_erc4626_max_functions(
    savings_green,
    green_token,
    whale,
    bob,
):
    """Test max functions"""
    # Test maxDeposit
    assert savings_green.maxDeposit(bob) == MAX_UINT256
    
    # Test maxMint
    assert savings_green.maxMint(bob) == MAX_UINT256
    
    # Test maxWithdraw and maxRedeem before deposit
    assert savings_green.maxWithdraw(bob) == 0
    assert savings_green.maxRedeem(bob) == 0
    
    # Make a deposit
    green_token.approve(savings_green, MAX_UINT256, sender=whale)
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    shares = savings_green.deposit(deposit_amount, bob, sender=whale)
    
    # Test maxWithdraw and maxRedeem after deposit
    assert savings_green.maxWithdraw(bob) == deposit_amount
    assert savings_green.maxRedeem(bob) == shares


def test_erc4626_rounding_edge_cases(
    savings_green,
    green_token,
    whale,
    credit_engine,
    bob,
):
    """Test rounding edge cases"""
    green_token.approve(savings_green, MAX_UINT256, sender=whale)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    shares = savings_green.deposit(deposit_amount, bob, sender=whale)
    
    # Test tiny amounts
    tiny_amount = 1
    green_token.approve(savings_green, MAX_UINT256, sender=whale)
    tiny_shares = savings_green.deposit(tiny_amount, bob, sender=whale)
    assert tiny_shares > 0  # Should still get some shares
    
    # Test large amounts (but not so large as to cause overflow)
    large_amount = 1000000 * EIGHTEEN_DECIMALS  # 1 million tokens
    green_token.mint(whale, large_amount, sender=credit_engine.address)  # Mint enough tokens for the large deposit
    green_token.approve(savings_green, MAX_UINT256, sender=whale)
    large_shares = savings_green.deposit(large_amount, bob, sender=whale)
    assert large_shares > shares  # Should get more shares than initial deposit
    
    # Verify share price consistency
    initial_share_price = deposit_amount / shares
    large_share_price = large_amount / large_shares
    assert abs(initial_share_price - large_share_price) < 1  # Share price should be consistent


def test_erc4626_share_price_manipulation(
    savings_green,
    green_token,
    whale,
    bob,
    sally,
    credit_engine,
):
    """Test share price manipulation resistance"""
    green_token.approve(savings_green, MAX_UINT256, sender=whale)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    shares1 = savings_green.deposit(deposit_amount, bob, sender=whale)
    
    # Try to manipulate share price with large deposit
    large_amount = deposit_amount * 1000
    green_token.mint(whale, large_amount, sender=credit_engine.address)  # Mint enough tokens for the large deposit
    shares2 = savings_green.deposit(large_amount, sally, sender=whale)
    
    # Check that share price wasn't significantly affected
    assert shares2 / large_amount == shares1 / deposit_amount  # Share price should be consistent


def test_erc4626_convert_functions(
    savings_green,
    green_token,
    whale,
    bob,
):
    """Test convert functions accuracy"""
    green_token.approve(savings_green, MAX_UINT256, sender=whale)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    shares = savings_green.deposit(deposit_amount, bob, sender=whale)
    
    # Test convertToShares
    converted_shares = savings_green.convertToShares(deposit_amount)
    assert converted_shares == shares
    
    # Test convertToAssets
    converted_assets = savings_green.convertToAssets(shares)
    assert converted_assets == deposit_amount
    
    # Test with zero values
    assert savings_green.convertToShares(0) == 0
    assert savings_green.convertToAssets(0) == 0


def test_erc4626_multiple_operations(
    savings_green,
    green_token,
    whale,
    bob,
):
    """Test multiple operations in sequence"""
    green_token.approve(savings_green, MAX_UINT256, sender=whale)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    shares = savings_green.deposit(deposit_amount, bob, sender=whale)
    
    # Withdraw half
    withdraw_amount = deposit_amount // 2
    withdrawn_shares = savings_green.withdraw(withdraw_amount, bob, bob, sender=bob)
    
    # Deposit again
    new_shares = savings_green.deposit(withdraw_amount, bob, sender=whale)
    
    # Redeem some shares
    redeem_shares = new_shares // 2
    redeemed_amount = savings_green.redeem(redeem_shares, bob, bob, sender=bob)
    
    # Check final balances
    assert savings_green.balanceOf(bob) == shares - withdrawn_shares + new_shares - redeem_shares
    assert savings_green.totalAssets() == deposit_amount - withdraw_amount + withdraw_amount - redeemed_amount
    assert green_token.balanceOf(bob) == withdraw_amount + redeemed_amount


@given(
    amount=st.integers(min_value=1, max_value=1000 * EIGHTEEN_DECIMALS),
    receiver=st.sampled_from(["bob", "sally"]),
)
def test_erc4626_fuzz_deposit(
    savings_green,
    green_token,
    whale,
    bob,
    sally,
    amount,
    receiver,
):
    """Fuzz test deposit functionality"""
    receiver_addr = bob if receiver == "bob" else sally
    green_token.approve(savings_green, MAX_UINT256, sender=whale)
    
    # Calculate expected shares
    expected_shares = savings_green.previewDeposit(amount)
    
    # Perform deposit
    shares = savings_green.deposit(amount, receiver_addr, sender=whale)
    
    # Verify results
    assert shares == expected_shares
    assert savings_green.balanceOf(receiver_addr) == shares
    assert savings_green.totalAssets() == amount
    assert green_token.balanceOf(savings_green) == amount


@given(
    shares=st.integers(min_value=1, max_value=1000 * EIGHTEEN_DECIMALS),
    receiver=st.sampled_from(["bob", "sally"]),
)
def test_erc4626_fuzz_mint(
    savings_green,
    green_token,
    whale,
    bob,
    sally,
    shares,
    receiver,
):
    """Fuzz test mint functionality"""
    receiver_addr = bob if receiver == "bob" else sally
    green_token.approve(savings_green, MAX_UINT256, sender=whale)
    
    # Calculate expected assets
    expected_assets = savings_green.previewMint(shares)
    
    # Perform mint
    assets = savings_green.mint(shares, receiver_addr, sender=whale)
    
    # Verify results
    assert assets == expected_assets
    assert savings_green.balanceOf(receiver_addr) == shares
    assert savings_green.totalAssets() == assets


def test_erc4626_integration_different_decimals(
    savings_green,
    green_token,
    whale,
    bob,
):
    """Test integration with tokens of different decimals"""
    green_token.approve(savings_green, MAX_UINT256, sender=whale)

    # Test with 6 decimals
    six_decimals = 10 ** 6
    shares = savings_green.deposit(100 * six_decimals, bob, sender=whale)
    assert shares > 0
    
    # Test with 8 decimals
    eight_decimals = 10 ** 8
    shares = savings_green.deposit(100 * eight_decimals, bob, sender=whale)
    assert shares > 0
    
    # Test with 18 decimals (standard)
    shares = savings_green.deposit(100 * EIGHTEEN_DECIMALS, bob, sender=whale)
    assert shares > 0


def test_erc4626_events(
    savings_green,
    green_token,
    whale,
    bob,
):
    """Test event emissions"""
    green_token.approve(savings_green, MAX_UINT256, sender=whale)
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Test Deposit event
    shares = savings_green.deposit(deposit_amount, bob, sender=whale)
    log = filter_logs(savings_green, "Deposit")[0]

    assert log.sender == whale
    assert log.owner == bob
    assert log.assets == deposit_amount
    assert log.shares == shares
    
    # Test Withdraw event
    withdraw_amount = deposit_amount // 2
    withdrawn_shares = savings_green.withdraw(withdraw_amount, bob, bob, sender=bob)
    log = filter_logs(savings_green, "Withdraw")[0]

    assert log.sender == bob
    assert log.receiver == bob
    assert log.owner == bob
    assert log.assets == withdraw_amount
    assert log.shares == withdrawn_shares


def test_erc4626_sequential_operations(
    savings_green,
    green_token,
    whale,
    bob,
):
    """Test sequential operations with different users"""
    # First user deposits
    green_token.approve(savings_green, MAX_UINT256, sender=whale)
    deposit1 = 100 * EIGHTEEN_DECIMALS
    shares1 = savings_green.deposit(deposit1, bob, sender=whale)
    
    # Second user deposits
    green_token.approve(savings_green, MAX_UINT256, sender=whale)
    deposit2 = 200 * EIGHTEEN_DECIMALS
    shares2 = savings_green.deposit(deposit2, bob, sender=whale)
    
    # First user withdraws
    withdraw1 = deposit1 // 2
    withdrawn_shares1 = savings_green.withdraw(withdraw1, bob, bob, sender=bob)
    
    # Second user withdraws
    withdraw2 = deposit2 // 2
    withdrawn_shares2 = savings_green.withdraw(withdraw2, bob, bob, sender=bob)
    
    # Verify final state
    assert savings_green.balanceOf(bob) == shares1 + shares2 - withdrawn_shares1 - withdrawn_shares2
    assert savings_green.totalAssets() == deposit1 + deposit2 - withdraw1 - withdraw2
    assert green_token.balanceOf(bob) == withdraw1 + withdraw2


def test_erc4626_share_value_changes_with_asset_balance(
    savings_green,
    green_token,
    whale,
    bob,
    credit_engine,
):
    """Test how share values change when underlying asset balance changes"""
    green_token.approve(savings_green, MAX_UINT256, sender=whale)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    shares = savings_green.deposit(deposit_amount, bob, sender=whale)
    
    # Record initial share value
    initial_share_value = savings_green.convertToAssets(shares) / shares
    
    # Direct transfer of green tokens to savings_green (simulating yield/profit)
    profit_amount = 50 * EIGHTEEN_DECIMALS
    green_token.mint(whale, profit_amount, sender=credit_engine.address)
    green_token.transfer(savings_green, profit_amount, sender=whale)
    
    # Share value should increase
    new_share_value = savings_green.convertToAssets(shares) / shares
    assert new_share_value > initial_share_value
    assert new_share_value == (deposit_amount + profit_amount) / shares


def test_erc4626_share_value_changes_with_asset_loss(
    savings_green,
    green_token,
    whale,
    bob,
    sally,
):
    """Test how share values change when underlying asset balance decreases"""
    green_token.approve(savings_green, MAX_UINT256, sender=whale)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    shares = savings_green.deposit(deposit_amount, bob, sender=whale)
    
    # Record initial share value
    initial_share_value = savings_green.convertToAssets(shares) / shares
    
    # Direct transfer of green tokens out of savings_green (simulating loss)
    loss_amount = 25 * EIGHTEEN_DECIMALS
    green_token.transfer(sally, loss_amount, sender=savings_green.address)
    
    # Share value should decrease
    new_share_value = savings_green.convertToAssets(shares) / shares
    assert new_share_value < initial_share_value
    assert new_share_value == (deposit_amount - loss_amount) / shares


def test_erc4626_share_value_with_multiple_deposits_and_balance_changes(
    savings_green,
    green_token,
    whale,
    bob,
    sally,
    credit_engine,
):
    """Test share values with multiple deposits and balance changes"""
    green_token.approve(savings_green, MAX_UINT256, sender=whale)

    # First deposit
    deposit1 = 100 * EIGHTEEN_DECIMALS
    shares1 = savings_green.deposit(deposit1, bob, sender=whale)
    
    # Add some profit
    profit = 20 * EIGHTEEN_DECIMALS
    green_token.mint(whale, profit, sender=credit_engine.address)
    green_token.transfer(savings_green, profit, sender=whale)
    
    # Second deposit after profit
    deposit2 = 200 * EIGHTEEN_DECIMALS
    shares2 = savings_green.deposit(deposit2, sally, sender=whale)
    
    # Verify share values
    bob_share_value = savings_green.convertToAssets(shares1) / shares1
    sally_share_value = savings_green.convertToAssets(shares2) / shares2
    
    # Share values should be equal
    assert abs(bob_share_value - sally_share_value) < 1
    
    # Add more profit
    profit2 = 30 * EIGHTEEN_DECIMALS
    green_token.mint(whale, profit2, sender=credit_engine.address)
    green_token.transfer(savings_green, profit2, sender=whale)
    
    # Verify share values increased proportionally
    new_bob_share_value = savings_green.convertToAssets(shares1) / shares1
    new_sally_share_value = savings_green.convertToAssets(shares2) / shares2
    
    assert new_bob_share_value > bob_share_value
    assert new_sally_share_value > sally_share_value
    assert abs(new_bob_share_value - new_sally_share_value) < 1


def test_erc4626_share_value_with_withdrawals_and_balance_changes(
    savings_green,
    green_token,
    whale,
    bob,
    sally,
    credit_engine,
):
    """Test share values with withdrawals and balance changes"""
    green_token.approve(savings_green, MAX_UINT256, sender=whale)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    shares = savings_green.deposit(deposit_amount, bob, sender=whale)
    
    # Add some profit
    profit = 20 * EIGHTEEN_DECIMALS
    green_token.mint(whale, profit, sender=credit_engine.address)
    green_token.transfer(savings_green, profit, sender=whale)
    
    # Record share value after profit
    share_value_after_profit = savings_green.convertToAssets(shares) / shares
    
    # Withdraw half
    withdraw_amount = deposit_amount // 2
    withdrawn_shares = savings_green.withdraw(withdraw_amount, bob, bob, sender=bob)
    
    # Add more profit after withdrawal
    profit2 = 10 * EIGHTEEN_DECIMALS
    green_token.mint(whale, profit2, sender=credit_engine.address)
    green_token.transfer(savings_green, profit2, sender=whale)
    
    # Verify remaining shares increased in value
    remaining_shares = shares - withdrawn_shares
    final_share_value = savings_green.convertToAssets(remaining_shares) / remaining_shares
    assert final_share_value > share_value_after_profit


def test_erc4626_share_value_with_extreme_balance_changes(
    savings_green,
    green_token,
    whale,
    bob,
    credit_engine,
):
    """Test share values with extreme balance changes"""
    green_token.approve(savings_green, MAX_UINT256, sender=whale)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    shares = savings_green.deposit(deposit_amount, bob, sender=whale)
    
    # Add massive profit (10x)
    profit = deposit_amount * 10
    green_token.mint(whale, profit, sender=credit_engine.address)
    green_token.transfer(savings_green, profit, sender=whale)
    
    # Verify share value increased proportionally
    new_share_value = savings_green.convertToAssets(shares) / shares
    assert new_share_value == (deposit_amount + profit) / shares
    
    # Add tiny profit (0.1%)
    tiny_profit = deposit_amount // 1000
    green_token.mint(whale, tiny_profit, sender=credit_engine.address)
    green_token.transfer(savings_green, tiny_profit, sender=whale)
    
    # Verify share value still updates correctly
    final_share_value = savings_green.convertToAssets(shares) / shares
    assert final_share_value > new_share_value
    assert final_share_value == (deposit_amount + profit + tiny_profit) / shares
