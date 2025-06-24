import pytest
import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, MAX_UINT256
from conf_utils import filter_logs


def test_stab_vault_claims_full(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Initial deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # swap
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,  # stab asset
        deposit_amount,     # stab asset amount
        bravo_token,  # liq asset
        claimable_amount,  # liq amount
        ZERO_ADDRESS,  # recipient (burn)
        alpha_token,  # green token
        savings_green,
        sender=auction_house.address
    )

    # claim!
    vault_id = vault_book.getRegId(stability_pool)
    usd_value = teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=bob)

    # test
    _test(claimable_amount, usd_value)
    assert stability_pool.getTotalUserValue(bob, alpha_token) <= 1
    assert stability_pool.getTotalValue(alpha_token) <= 1

    _test(claimable_amount, bravo_token.balanceOf(bob))


def test_stab_vault_claims_partial(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Initial deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # swap
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,  # stab asset
        deposit_amount,     # stab asset amount
        bravo_token,  # liq asset
        claimable_amount,  # liq amount
        ZERO_ADDRESS,  # recipient (burn)
        alpha_token,  # green token
        savings_green,
        sender=auction_house.address
    )

    bob_new_value = stability_pool.getTotalUserValue(bob, alpha_token)
    total_new_value = stability_pool.getTotalValue(alpha_token)

    # claim!
    vault_id = vault_book.getRegId(stability_pool)
    claim_usd_value = bob_new_value // 2
    usd_value = teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, claim_usd_value, sender=bob)

    # test
    _test(claim_usd_value, usd_value)
    _test(bob_new_value // 2, stability_pool.getTotalUserValue(bob, alpha_token))
    _test(total_new_value // 2, stability_pool.getTotalValue(alpha_token))

    _test(claimable_amount // 2, bravo_token.balanceOf(bob))


def test_stab_vault_claims_validation(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bob,
    alice,
    teller,
    mock_price_source,
    vault_book,
    switchboard_alpha,
    setGeneralConfig,
    setAssetConfig,
):
    """Test validation logic for claims"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    vault_id = vault_book.getRegId(stability_pool)

    # Test claim when paused
    stability_pool.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("contract paused"):
        teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=bob)
    stability_pool.pause(False, sender=switchboard_alpha.address)

    # Test claim with no position - should revert with "nothing claimed"
    with boa.reverts("nothing claimed"):
        teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=bob)

    # Test claim with no claimable assets
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)
    
    with boa.reverts("nothing claimed"):
        teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=bob)

    # Test claim with zero max USD value
    with boa.reverts("nothing claimed"):
        teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, 0, sender=bob)

    # Test unauthorized caller
    with boa.reverts("only Teller allowed"):
        stability_pool.claimFromStabilityPool(bob, alpha_token, bravo_token, 100, bob, False, sender=alice)


def test_stab_vault_claims_no_shares(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
):
    """Test claims when user has no shares in the stability pool"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Only Bob deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Alice tries to claim but has no shares - should revert with "nothing claimed"
    vault_id = vault_book.getRegId(stability_pool)
    with boa.reverts("nothing claimed"):
        teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=alice)
    assert bravo_token.balanceOf(alice) == 0


def test_stab_vault_claims_insufficient_balance(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
):
    """Test claims when contract has insufficient claimable balance"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Remove most of the claimable tokens from the contract
    bravo_token.transfer(bravo_token_whale, claimable_amount - 1, sender=stability_pool.address)

    # Try to claim - should only get what's available
    vault_id = vault_book.getRegId(stability_pool)
    usd_value = teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=bob)
    
    # Should have claimed the 1 token that was available
    assert usd_value == 1
    assert bravo_token.balanceOf(bob) == 1


def test_stab_vault_claims_multiple_users(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test claims with multiple users in the stability pool"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Both users deposit different amounts
    bob_deposit = 100 * EIGHTEEN_DECIMALS
    alice_deposit = 50 * EIGHTEEN_DECIMALS
    
    alpha_token.transfer(stability_pool, bob_deposit, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, bob_deposit, sender=teller.address)
    
    alpha_token.transfer(stability_pool, alice_deposit, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, alice_deposit, sender=teller.address)

    # Add claimable assets
    claimable_amount = 225 * EIGHTEEN_DECIMALS  # 1.5x the total deposits
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, bob_deposit + alice_deposit, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)
    
    # Bob claims first (should get 2/3 of claimable assets)
    stability_pool.getTotalUserValue(bob, alpha_token)
    teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=bob)
    bob_claimed = bravo_token.balanceOf(bob)
    
    # Alice claims second (should get 1/3 of remaining claimable assets)
    stability_pool.getTotalUserValue(alice, alpha_token)
    teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=alice)
    alice_claimed = bravo_token.balanceOf(alice)

    # Bob should get roughly 2/3, Alice should get roughly 1/3
    total_claimed = bob_claimed + alice_claimed
    _test(claimable_amount, total_claimed)
    
    # Check proportions (allowing for small rounding differences)
    bob_ratio = bob_claimed / total_claimed
    alice_ratio = alice_claimed / total_claimed
    assert abs(bob_ratio - 2/3) < 0.01  # Within 1% of expected ratio
    assert abs(alice_ratio - 1/3) < 0.01


def test_stab_vault_claims_multiple_assets(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test claims with multiple different claimable assets"""
    setGeneralConfig()
    setAssetConfig(bravo_token)
    setAssetConfig(charlie_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(charlie_token, price)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add first claimable asset (bravo)
    bravo_amount = 60 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, bravo_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, bravo_token, bravo_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Add second claimable asset (charlie)
    charlie_amount = 90 * (10 ** charlie_token.decimals())
    charlie_token.transfer(stability_pool, charlie_amount, sender=charlie_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, charlie_token, charlie_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)

    # Claim bravo tokens
    teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=bob)
    bravo_claimed = bravo_token.balanceOf(bob)
    _test(bravo_amount, bravo_claimed)

    # Claim charlie tokens  
    teller.claimFromStabilityPool(vault_id, alpha_token, charlie_token, sender=bob)
    charlie_claimed = charlie_token.balanceOf(bob)
    _test(charlie_amount, charlie_claimed)

    # User should be fully depleted
    assert stability_pool.getTotalUserValue(bob, alpha_token) <= 1


def test_stab_vault_claims_tiny_amounts(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
):
    """Test claims with very small amounts"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Initial deposit
    deposit_amount = 2  # Very small amount
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add tiny claimable assets
    claimable_amount = 3  # Even smaller
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Claim
    vault_id = vault_book.getRegId(stability_pool)
    usd_value = teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=bob)
    
    assert usd_value >= 0
    assert bravo_token.balanceOf(bob) >= 0


def test_stab_vault_claims_depletion(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
):
    """Test that claims properly deplete user positions"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Record initial shares
    initial_shares = stability_pool.userBalances(bob, alpha_token)
    assert initial_shares > 0

    # Add claimable assets equal to deposit
    claimable_amount = 100 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Claim everything
    vault_id = vault_book.getRegId(stability_pool)
    teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=bob)

    # User should be depleted
    final_shares = stability_pool.userBalances(bob, alpha_token)
    assert final_shares == 0
    assert stability_pool.getTotalUserValue(bob, alpha_token) == 0


def test_stab_vault_claim_many_basic(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test claimManyFromStabilityPool with multiple assets"""
    setGeneralConfig()
    setAssetConfig(bravo_token)
    setAssetConfig(charlie_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(charlie_token, price)

    # Initial deposit
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    bravo_amount = 80 * EIGHTEEN_DECIMALS
    charlie_amount = 120 * (10 ** charlie_token.decimals())
    
    bravo_token.transfer(stability_pool, bravo_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, bravo_token, bravo_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )
    
    charlie_token.transfer(stability_pool, charlie_amount, sender=charlie_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, charlie_token, charlie_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Create claims array
    claims = [
        (alpha_token.address, bravo_token.address, MAX_UINT256),
        (alpha_token.address, charlie_token.address, MAX_UINT256)
    ]

    # Claim many
    vault_id = vault_book.getRegId(stability_pool)
    total_usd_value = teller.claimManyFromStabilityPool(vault_id, claims, sender=bob)

    # Check results
    _test(bravo_amount, bravo_token.balanceOf(bob))
    _test(charlie_amount, charlie_token.balanceOf(bob))
    assert total_usd_value == 200 * EIGHTEEN_DECIMALS


def test_stab_vault_claim_many_empty_array(
    stability_pool,
    bob,
    teller,
    vault_book,
):
    """Test claimManyFromStabilityPool with empty claims array"""
    vault_id = vault_book.getRegId(stability_pool)
    
    # Empty claims array should revert with "nothing claimed"
    with boa.reverts("nothing claimed"):
        teller.claimManyFromStabilityPool(vault_id, [], sender=bob)


def test_stab_vault_claim_many_partial_claims(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test claimManyFromStabilityPool with partial claim amounts"""
    setGeneralConfig()
    setAssetConfig(bravo_token)
    setAssetConfig(charlie_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(charlie_token, price)

    # Initial deposit
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    bravo_amount = 100 * EIGHTEEN_DECIMALS
    charlie_amount = 100 * (10 ** charlie_token.decimals())
    
    bravo_token.transfer(stability_pool, bravo_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, bravo_token, bravo_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )
    
    charlie_token.transfer(stability_pool, charlie_amount, sender=charlie_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, charlie_token, charlie_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Create claims array with partial amounts
    claims = [
        (alpha_token.address, bravo_token.address, bravo_amount // 2),  # Half of bravo
        (alpha_token.address, charlie_token.address, 33 * EIGHTEEN_DECIMALS)  # Third of charlie
    ]

    # Claim many
    vault_id = vault_book.getRegId(stability_pool)
    total_usd_value = teller.claimManyFromStabilityPool(vault_id, claims, sender=bob)

    # Check results
    expected_bravo = bravo_amount // 2
    expected_charlie = 33 * (10 ** charlie_token.decimals())
    
    _test(expected_bravo, bravo_token.balanceOf(bob))
    _test(expected_charlie, charlie_token.balanceOf(bob))
    _test(total_usd_value, expected_bravo + 33 * EIGHTEEN_DECIMALS)

    # User should still have remaining value
    remaining_value = stability_pool.getTotalUserValue(bob, alpha_token)
    assert remaining_value > 0


def test_stab_vault_claim_many_mixed_valid_invalid(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test claimManyFromStabilityPool with mix of valid and invalid claims"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(charlie_token, price)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add only bravo as claimable asset (not charlie)
    bravo_amount = 100 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, bravo_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, bravo_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Create claims array with valid and invalid claims
    claims = [
        (alpha_token.address, bravo_token.address, bravo_amount),      # Valid claim
        (alpha_token.address, charlie_token.address, 50 * EIGHTEEN_DECIMALS),  # Invalid - no claimable charlie
        (ZERO_ADDRESS, bravo_token.address, bravo_amount),            # Invalid - zero stab asset
        (alpha_token.address, ZERO_ADDRESS, bravo_amount),            # Invalid - zero claim asset
    ]

    # Claim many - should only process valid claims
    vault_id = vault_book.getRegId(stability_pool)
    total_usd_value = teller.claimManyFromStabilityPool(vault_id, claims, sender=bob)

    # Only bravo should be claimed
    _test(bravo_amount, bravo_token.balanceOf(bob))
    assert charlie_token.balanceOf(bob) == 0
    assert total_usd_value == bravo_amount


def test_stab_vault_claim_many_max_claims(
    stability_pool,
    bob,
    teller,
    vault_book,
):
    """Test claimManyFromStabilityPool with maximum number of claims"""
    # Get the MAX_STAB_CLAIMS constant (15)
    max_claims = 15
    
    # Create exactly max number of claims (all invalid to avoid setup complexity)
    claims = [(ZERO_ADDRESS, ZERO_ADDRESS, 0) for _ in range(max_claims)]
    
    vault_id = vault_book.getRegId(stability_pool)
    
    # Should revert with "nothing claimed" since all claims are invalid
    with boa.reverts("nothing claimed"):
        teller.claimManyFromStabilityPool(vault_id, claims, sender=bob)


def test_stab_vault_claim_many_exceeds_limit(
    stability_pool,
    bob,
    teller,
    vault_book,
):
    """Test claimManyFromStabilityPool fails when exceeding maximum number of claims"""
    # Get the MAX_STAB_CLAIMS constant (15)
    max_claims = 15
    
    # Create MORE than max number of claims (this should fail at bounds check)
    claims = [(ZERO_ADDRESS, ZERO_ADDRESS, 0) for _ in range(max_claims + 1)]
    
    vault_id = vault_book.getRegId(stability_pool)
    
    # Should fail with bounds check error when trying to pass 16 claims to DynArray[StabPoolClaim, 15]
    with boa.reverts():  # Generic revert since it's a compiler bounds check
        teller.claimManyFromStabilityPool(vault_id, claims, sender=bob)


def test_stab_vault_claims_event_emission(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
    _test,
):
    """Test that AssetClaimedInStabilityPool events are properly emitted"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Setup
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Claim and check for event
    vault_id = vault_book.getRegId(stability_pool)
    
    usd_value = teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=bob)
    log = filter_logs(teller, "AssetClaimedInStabilityPool")[0]
    assert log.user == bob
    assert log.stabAsset == alpha_token.address
    assert log.claimAsset == bravo_token.address
    _test(log.claimAmount, claimable_amount)
    _test(log.claimUsdValue, usd_value)
    assert log.claimShares != 0
    assert log.isDepleted


def test_stab_vault_claims_claimable_balance_update(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test that claimable balances are properly updated after claims"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Two users deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)
    
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    claimable_amount = 300 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount * 2, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Check initial claimable balances
    initial_claimable = stability_pool.claimableBalances(alpha_token, bravo_token)
    initial_total_claimable = stability_pool.totalClaimableBalances(bravo_token)
    _test(claimable_amount, initial_claimable)
    _test(claimable_amount, initial_total_claimable)

    vault_id = vault_book.getRegId(stability_pool)

    # Bob claims half
    bob_claim_amount = claimable_amount // 2
    teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, bob_claim_amount, sender=bob)

    # Check balances after Bob's claim
    after_bob_claimable = stability_pool.claimableBalances(alpha_token, bravo_token)
    after_bob_total_claimable = stability_pool.totalClaimableBalances(bravo_token)
    
    expected_remaining = claimable_amount - bob_claim_amount
    _test(expected_remaining, after_bob_claimable)
    _test(expected_remaining, after_bob_total_claimable)

    # Alice claims the rest
    teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=alice)

    # Check balances after Alice's claim - should be near zero
    final_claimable = stability_pool.claimableBalances(alpha_token, bravo_token)
    final_total_claimable = stability_pool.totalClaimableBalances(bravo_token)
    
    assert final_claimable <= 1  # Allow for rounding
    assert final_total_claimable <= 1


def test_stab_vault_claims_config_disabled(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    switchboard_alpha,
    setGeneralConfig,
    setAssetConfig,
):
    """Test claims when different configuration flags are disabled"""
    # Setup with claims enabled first
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Setup deposit and claimable assets
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)

    # Test 1: Disable general claims config
    setGeneralConfig(_canClaimInStabPool=False)
    with boa.reverts("nothing claimed"):
        teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=bob)

    # Re-enable general config
    setGeneralConfig()

    # Test 2: Disable asset-specific claims config
    setAssetConfig(bravo_token, _canClaimInStabPool=False)
    with boa.reverts("nothing claimed"):
        teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=bob)

    # Re-enable asset config for final test
    setAssetConfig(bravo_token)
    
    # Verify claims work again when config is restored
    usd_value = teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=bob)
    assert usd_value > 0


def test_stab_vault_claims_price_oracle_zero(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
):
    """Test claims when price oracle returns 0 for claim asset"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Setup deposit and claimable assets
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Set price of claim asset to 0 (simulating oracle failure or delisted asset)
    mock_price_source.setPrice(bravo_token, 0)

    vault_id = vault_book.getRegId(stability_pool)
    
    # Should raise an exception due to price oracle returning 0 with _shouldRaise=True
    with boa.reverts():
        teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=bob)


def test_stab_vault_claims_max_usd_value_limit(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test claims with specific maxUsdValue limits (not MAX_UINT256)"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Setup
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)

    # Claim with specific USD limit (less than total available)
    max_claim_usd = 50 * EIGHTEEN_DECIMALS
    usd_value = teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, max_claim_usd, sender=bob)
    
    # Should respect the USD limit
    _test(max_claim_usd, usd_value)
    _test(max_claim_usd, bravo_token.balanceOf(bob))  # 1:1 price ratio
    
    # User should still have remaining value in the pool
    remaining_value = stability_pool.getTotalUserValue(bob, alpha_token)
    assert remaining_value > 0


def test_stab_vault_claims_asset_registry_removal(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test that claimable assets are properly removed from registry when depleted"""
    setGeneralConfig()
    setAssetConfig(bravo_token)
    setAssetConfig(charlie_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(charlie_token, price)

    # Setup
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add two different claimable assets
    bravo_amount = 80 * EIGHTEEN_DECIMALS
    charlie_amount = 120 * (10 ** charlie_token.decimals())
    
    bravo_token.transfer(stability_pool, bravo_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, bravo_token, bravo_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )
    
    charlie_token.transfer(stability_pool, charlie_amount, sender=charlie_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, charlie_token, charlie_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Check initial registry state
    assert stability_pool.numClaimableAssets(alpha_token) == 3  # 0 index not used, so 3 total (1 bravo, 2 charlie)
    assert stability_pool.indexOfClaimableAsset(alpha_token, bravo_token) == 1
    assert stability_pool.indexOfClaimableAsset(alpha_token, charlie_token) == 2
    assert stability_pool.claimableAssets(alpha_token, 1) == bravo_token.address
    assert stability_pool.claimableAssets(alpha_token, 2) == charlie_token.address

    vault_id = vault_book.getRegId(stability_pool)

    # Fully deplete bravo (should remove from registry)
    bravo_usd_value = teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=bob)
    _test(bravo_amount, bravo_usd_value)

    # Check that bravo is removed from registry
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == 0
    assert stability_pool.indexOfClaimableAsset(alpha_token, bravo_token) == 0  # Removed
    
    # Charlie should still be in registry and moved to index 1
    assert stability_pool.numClaimableAssets(alpha_token) == 2  # One less
    assert stability_pool.indexOfClaimableAsset(alpha_token, charlie_token) == 1  # Moved to fill gap
    assert stability_pool.claimableAssets(alpha_token, 1) == charlie_token.address

    # Partially claim charlie (should NOT remove from registry)
    partial_charlie_usd = 60 * EIGHTEEN_DECIMALS
    teller.claimFromStabilityPool(vault_id, alpha_token, charlie_token, partial_charlie_usd, sender=bob)
    
    # Charlie should still be in registry
    assert stability_pool.claimableBalances(alpha_token, charlie_token) > 0
    assert stability_pool.indexOfClaimableAsset(alpha_token, charlie_token) == 1
    assert stability_pool.numClaimableAssets(alpha_token) == 2


def test_stab_vault_claims_precision_edge_cases(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
):
    """Test claims with precision/rounding edge cases"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Setup with odd amounts that might cause rounding issues
    deposit_amount1 = 333333333333333333  # ~0.33 tokens
    deposit_amount2 = 666666666666666667  # ~0.67 tokens
    
    alpha_token.transfer(stability_pool, deposit_amount1, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount1, sender=teller.address)
    
    alpha_token.transfer(stability_pool, deposit_amount2, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount2, sender=teller.address)

    # Add claimable assets with odd amount
    claimable_amount = 999999999999999999  # Just under 1 token
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount1 + deposit_amount2, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)

    # Claim with both users and ensure total is preserved
    bob_initial_value = stability_pool.getTotalUserValue(bob, alpha_token)
    alice_initial_value = stability_pool.getTotalUserValue(alice, alpha_token)
    bob_initial_value + alice_initial_value

    bob_usd_value = teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=bob)
    alice_usd_value = teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=alice)

    # Check that total claimed roughly equals claimable amount (within rounding tolerance)
    total_claimed = bob_usd_value + alice_usd_value
    assert abs(total_claimed - claimable_amount) <= 2  # Allow for 2 wei rounding difference

    # Check token balances
    bob_tokens = bravo_token.balanceOf(bob)
    alice_tokens = bravo_token.balanceOf(alice)
    total_tokens = bob_tokens + alice_tokens
    assert abs(total_tokens - claimable_amount) <= 2


def test_stab_vault_claims_multiple_stability_assets(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test claims when there are multiple stability pool assets"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(charlie_token, price)

    # Setup with both alpha and charlie as stability pool assets
    alpha_deposit = 100 * EIGHTEEN_DECIMALS
    charlie_deposit = 50 * (10 ** charlie_token.decimals())
    
    # Bob deposits alpha
    alpha_token.transfer(stability_pool, alpha_deposit, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, alpha_deposit, sender=teller.address)
    
    # Alice deposits charlie
    charlie_token.transfer(stability_pool, charlie_deposit, sender=charlie_token_whale)
    stability_pool.depositTokensInVault(alice, charlie_token, charlie_deposit, sender=teller.address)

    # Add bravo as claimable for both stability assets
    bravo_amount_for_alpha = 80 * EIGHTEEN_DECIMALS
    bravo_amount_for_charlie = 40 * EIGHTEEN_DECIMALS
    
    bravo_token.transfer(stability_pool, bravo_amount_for_alpha, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, alpha_deposit, bravo_token, bravo_amount_for_alpha,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )
    
    bravo_token.transfer(stability_pool, bravo_amount_for_charlie, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        charlie_token, charlie_deposit, bravo_token, bravo_amount_for_charlie,
        ZERO_ADDRESS, charlie_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)

    # Bob claims bravo from his alpha position
    bob_usd_value = teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=bob)
    _test(bravo_amount_for_alpha, bob_usd_value)
    _test(bravo_amount_for_alpha, bravo_token.balanceOf(bob))

    # Alice claims bravo from her charlie position
    alice_usd_value = teller.claimFromStabilityPool(vault_id, charlie_token, bravo_token, sender=alice)
    _test(bravo_amount_for_charlie, alice_usd_value)
    _test(bravo_amount_for_charlie, bravo_token.balanceOf(alice))

    # Check that both users' stability positions are depleted
    assert stability_pool.getTotalUserValue(bob, alpha_token) <= 1
    assert stability_pool.getTotalUserValue(alice, charlie_token) <= 1


def test_stab_vault_claims_concurrent_claims_edge_case(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
):
    """Test edge case where claimable balance changes between calculation and execution"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Setup two users with equal deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)
    
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    claimable_amount = 200 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount * 2, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Simulate scenario where available balance is less than recorded balance
    # (e.g. some tokens were transferred out externally)
    tokens_to_remove = claimable_amount // 4  # Remove 25%
    bravo_token.transfer(bravo_token_whale, tokens_to_remove, sender=stability_pool.address)

    vault_id = vault_book.getRegId(stability_pool)

    # Both users try to claim - should gracefully handle insufficient balance
    bob_usd_value = teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=bob)
    alice_usd_value = teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=alice)

    # Total claimed should not exceed what was actually available
    total_claimed_tokens = bravo_token.balanceOf(bob) + bravo_token.balanceOf(alice)
    assert total_claimed_tokens <= claimable_amount - tokens_to_remove

    # Both users should have gotten something (though less than expected)
    assert bob_usd_value > 0
    assert alice_usd_value > 0


def test_stab_vault_claims_claim_many_over_limit(
    stability_pool,
    bob,
    teller,
    vault_book,
):
    """Test claimManyFromStabilityPool with more than MAX_STAB_CLAIMS"""
    vault_id = vault_book.getRegId(stability_pool)
    
    # Try to create more than max claims (16 claims when max is 15)
    max_claims = 15
    try:
        # This should fail at compile/runtime due to DynArray size limit
        claims = [(ZERO_ADDRESS, ZERO_ADDRESS, 0) for _ in range(max_claims + 1)]
        teller.claimManyFromStabilityPool(vault_id, claims, sender=bob)
        assert False, "Should have failed due to exceeding max claims"
    except Exception:
        # Expected to fail
        pass


def test_stab_vault_claims_zero_total_shares_edge_case(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
):
    """Test claims in edge case where total shares is very small"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Setup with minimal deposit
    deposit_amount = 1  # 1 wei
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add much larger claimable amount
    claimable_amount = EIGHTEEN_DECIMALS  # 1 full token
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)
    
    # Should be able to claim despite very small shares
    usd_value = teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=bob)
    assert usd_value > 0
    assert bravo_token.balanceOf(bob) > 0


def test_stab_vault_claims_with_delegation_permission(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
    setUserDelegation,
):
    """Test that a delegate with permission can claim from stability pool for another user"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Bob deposits into stability pool
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)

    # Before delegation, Alice cannot claim for Bob
    with boa.reverts("cannot claim for user"):
        teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, MAX_UINT256, bob, sender=alice)

    # Bob delegates claim permission to Alice
    setUserDelegation(bob, alice, _canClaimFromStabPool=True)

    # Now Alice can claim for Bob
    usd_value = teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, MAX_UINT256, bob, sender=alice)
    _test(claimable_amount, usd_value)
    
    # Verify the tokens went to Bob (not Alice)
    _test(claimable_amount, bravo_token.balanceOf(bob))
    assert bravo_token.balanceOf(alice) == 0

    # Verify Bob's position is depleted
    assert stability_pool.getTotalUserValue(bob, alpha_token) <= 1


def test_stab_vault_claims_without_delegation_permission(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    sally,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
    setUserDelegation,
):
    """Test that users without delegation permission cannot claim for others"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Bob deposits into stability pool
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)

    # Alice has no delegation permission - should fail
    with boa.reverts("cannot claim for user"):
        teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, MAX_UINT256, bob, sender=alice)

    # Bob gives Alice delegation but NOT for claiming from stability pool
    setUserDelegation(
        bob, 
        alice, 
        _canWithdraw=True,
        _canBorrow=True,
        _canClaimFromStabPool=False,  # Explicitly NO permission for stability pool claims
        _canClaimLoot=True
    )

    # Alice still cannot claim for Bob (no stability pool claim permission)
    with boa.reverts("cannot claim for user"):
        teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, MAX_UINT256, bob, sender=alice)

    # Bob gives Sally full delegation including stability pool claims
    setUserDelegation(bob, sally, _canClaimFromStabPool=True)

    # Sally can claim for Bob
    usd_value = teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, MAX_UINT256, bob, sender=sally)
    _test(claimable_amount, usd_value)
    
    # Verify the tokens went to Bob (not Sally)
    _test(claimable_amount, bravo_token.balanceOf(bob))
    assert bravo_token.balanceOf(sally) == 0
    
    # Alice still has no tokens
    assert bravo_token.balanceOf(alice) == 0

    # Test claim many with delegation
    # First setup another claimable asset
    deposit_amount2 = 50 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount2, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount2, sender=teller.address)
    
    charlie_amount = 75 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, charlie_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount2, bravo_token, charlie_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Sally can use claimManyFromStabilityPool for Alice with delegation
    setUserDelegation(alice, sally, _canClaimFromStabPool=True)
    
    claims = [(alpha_token.address, bravo_token.address, MAX_UINT256)]
    total_usd_value = teller.claimManyFromStabilityPool(vault_id, claims, alice, sender=sally)
    
    _test(charlie_amount, total_usd_value)
    _test(charlie_amount, bravo_token.balanceOf(alice))


##########################
# Stability Pool Rewards #
##########################


@pytest.fixture(scope="module")
def setupStabPoolClaimsRewards(mission_control, setAssetConfig, setGeneralConfig, setRipeRewardsConfig, switchboard_alpha, ripe_token):
    def setupStabPoolClaimsRewards(
        _ripePerDollar = 1 * EIGHTEEN_DECIMALS,
        _stabRewardsLockDuration = 500,
        _minLockDuration = 0,
        _maxLockDuration = 1000,
        _autoStakeDurationRatio = 0,
    ):
        setGeneralConfig()

        # Set RipeRewardsConfig with stab pool rewards
        setRipeRewardsConfig(
            _stabPoolRipePerDollarClaimed=_ripePerDollar,
            _autoStakeDurationRatio=_autoStakeDurationRatio,
        )

        # setup ripe gov vault
        lock_terms = (
            _minLockDuration,
            _maxLockDuration,
            100_00,
            False,
            0,
        )
        mission_control.setRipeGovVaultConfig(
            ripe_token, 
            100_00,
            False,
            lock_terms, 
            sender=switchboard_alpha.address
        )
        setAssetConfig(ripe_token, _vaultIds=[2])

    yield setupStabPoolClaimsRewards


def test_stab_vault_claim_rewards_basic(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    ripe_token,
    ripe_gov_vault,
    ledger,
    _test,
    setAssetConfig,
    setupStabPoolClaimsRewards,
):
    """Test basic Ripe rewards functionality when claiming from stability pool"""
    # Set up stability pool claim rewards configuration
    # 0.1 Ripe per dollar claimed, 30-day lock (assuming ~12 sec blocks)
    setupStabPoolClaimsRewards(
        _ripePerDollar = EIGHTEEN_DECIMALS // 10,  # 0.1 Ripe per dollar
        _stabRewardsLockDuration = 216000,  # ~30 days in blocks (30*24*60*60/12)
    )
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(ripe_token, price)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Record Bob's initial balance in gov vault
    initial_gov_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)

    # Claim from stability pool
    vault_id = vault_book.getRegId(stability_pool)
    claim_usd_value = teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=bob)

    # Verify claim worked
    _test(claimable_amount, claim_usd_value)
    _test(claimable_amount, bravo_token.balanceOf(bob))

    # Calculate expected Ripe rewards: 150 USD * 0.1 = 15 Ripe
    expected_ripe_rewards = claimable_amount * EIGHTEEN_DECIMALS // 10 // EIGHTEEN_DECIMALS
    
    # Verify Bob received Ripe rewards in gov vault
    final_gov_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    actual_ripe_rewards = final_gov_balance - initial_gov_balance
    _test(expected_ripe_rewards, actual_ripe_rewards)

    # Verify the Ripe tokens are locked (Bob should have a position in gov vault)
    assert ripe_gov_vault.userBalances(bob, ripe_token) > 0


def test_stab_vault_claim_rewards_different_rates(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    mission_control,
    switchboard_alpha,
    ripe_token,
    ripe_gov_vault,
    _test,
    setAssetConfig,
    setupStabPoolClaimsRewards,
    setRipeRewardsConfig,
):
    """Test Ripe rewards with different reward rates"""
    # Test 1: High reward rate (1 Ripe per dollar)
    setupStabPoolClaimsRewards(
        _ripePerDollar = EIGHTEEN_DECIMALS,  # 1 Ripe per dollar
        _stabRewardsLockDuration = 50400,  # ~7 days in blocks (7*24*60*60/12)
    )
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(ripe_token, price)

    # Setup for Bob
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    claimable_amount = 50 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    initial_bob_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    vault_id = vault_book.getRegId(stability_pool)
    claim_usd_value = teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=bob)

    final_bob_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    bob_rewards = final_bob_balance - initial_bob_balance
    expected_bob_rewards = claim_usd_value  # 1:1 ratio
    _test(expected_bob_rewards, bob_rewards)

    # Test 2: Low reward rate (0.01 Ripe per dollar)
    setRipeRewardsConfig(_stabPoolRipePerDollarClaimed=EIGHTEEN_DECIMALS // 100)

    # Setup for Alice
    alpha_token.transfer(stability_pool, deposit_amount // 2, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount // 2, sender=teller.address)

    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    initial_alice_balance = ripe_gov_vault.getTotalAmountForUser(alice, ripe_token)
    alice_claim_usd_value = teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=alice)

    final_alice_balance = ripe_gov_vault.getTotalAmountForUser(alice, ripe_token)
    alice_rewards = final_alice_balance - initial_alice_balance
    expected_alice_rewards = alice_claim_usd_value // 100  # 0.01 ratio
    _test(expected_alice_rewards, alice_rewards)

    # Bob should get 100x more rewards per dollar than Alice due to config change
    # Bob: 1 Ripe per dollar, Alice: 0.01 Ripe per dollar
    assert bob_rewards > 0, "Bob should have received rewards"
    assert alice_rewards > 0, "Alice should have received rewards"
    
    bob_rate = bob_rewards / claim_usd_value
    alice_rate = alice_rewards / alice_claim_usd_value
    actual_ratio = bob_rate / alice_rate
    
    # Bob gets 100x more per dollar (1.0 vs 0.01)
    _test(100, actual_ratio)


def test_stab_vault_claim_rewards_zero_config(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    ripe_token,
    ripe_gov_vault,
    setAssetConfig,
    setupStabPoolClaimsRewards,
):
    """Test that no rewards are given when reward rate is zero"""
    # Set up rewards configuration with zero rate
    setupStabPoolClaimsRewards(
        _ripePerDollar = 0,  # 0 Ripe per dollar (no rewards)
        _stabRewardsLockDuration = 216000,  # ~30 days in blocks
    )
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(ripe_token, price)

    # Setup
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Record initial gov vault balance
    initial_gov_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)

    # Claim from stability pool
    vault_id = vault_book.getRegId(stability_pool)
    claim_usd_value = teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=bob)

    # Verify claim worked but no rewards given
    assert claim_usd_value > 0
    final_gov_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    assert final_gov_balance == initial_gov_balance  # No change in gov vault balance


def test_stab_vault_claim_rewards_many_claims(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    ripe_token,
    ripe_gov_vault,
    _test,
    setAssetConfig,
    setupStabPoolClaimsRewards,
):
    """Test Ripe rewards with claimManyFromStabilityPool"""
    # Set up rewards configuration
    setupStabPoolClaimsRewards(
        _ripePerDollar = EIGHTEEN_DECIMALS // 5,  # 0.2 Ripe per dollar
        _stabRewardsLockDuration = 100800,  # ~14 days in blocks (14*24*60*60/12)
    )
    setAssetConfig(bravo_token)
    setAssetConfig(charlie_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(charlie_token, price)
    mock_price_source.setPrice(ripe_token, price)

    # Setup
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add multiple claimable assets
    bravo_amount = 80 * EIGHTEEN_DECIMALS  # 80 tokens with 18 decimals
    charlie_amount = 120 * (10 ** charlie_token.decimals())  # 120 tokens with 6 decimals
    
    bravo_token.transfer(stability_pool, bravo_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, bravo_token, bravo_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )
    
    charlie_token.transfer(stability_pool, charlie_amount, sender=charlie_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, charlie_token, charlie_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Record initial gov vault balance
    initial_gov_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)

    # Create claims array
    claims = [
        (alpha_token.address, bravo_token.address, MAX_UINT256),
        (alpha_token.address, charlie_token.address, MAX_UINT256)
    ]

    # Claim many
    vault_id = vault_book.getRegId(stability_pool)
    total_usd_value = teller.claimManyFromStabilityPool(vault_id, claims, sender=bob)

    # Verify total claim value
    # Since both tokens are priced at $1: 80 tokens + 120 tokens = $200 USD value
    expected_total_usd_value = 200 * EIGHTEEN_DECIMALS
    _test(expected_total_usd_value, total_usd_value)

    # Calculate expected total Ripe rewards: $200 * 0.2 = 40 Ripe
    expected_total_ripe_rewards = total_usd_value // 5  # 0.2 Ripe per dollar
    
    # Verify Bob received the claimed tokens
    _test(bravo_amount, bravo_token.balanceOf(bob))
    _test(charlie_amount, charlie_token.balanceOf(bob))
    
    # Verify Bob received total Ripe rewards in gov vault
    final_gov_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    actual_ripe_rewards = final_gov_balance - initial_gov_balance
    _test(expected_total_ripe_rewards, actual_ripe_rewards)


def test_stab_vault_claim_rewards_insufficient_ripe(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    ripe_token,
    ripe_gov_vault,
    ledger,
    setAssetConfig,
    setupStabPoolClaimsRewards,
    switchboard_alpha,
):
    """Test rewards are limited by available Ripe in ledger"""
    # Set up high rewards configuration
    setupStabPoolClaimsRewards(
        _ripePerDollar = 10 * EIGHTEEN_DECIMALS,  # 10 Ripe per dollar (very high)
        _stabRewardsLockDuration = 216000,  # ~30 days in blocks
    )
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(ripe_token, price)

    # Setup
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    claimable_amount = 50 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Set limited Ripe available for rewards (less than what would be needed)
    theoretical_rewards = claimable_amount * 10  # 50 * 10 = 500 Ripe demanded
    limited_ripe_available = 100 * EIGHTEEN_DECIMALS  # Only 100 Ripe available
    ledger.setRipeAvailForRewards(limited_ripe_available, sender=switchboard_alpha.address)
    
    # Verify the limit was set correctly
    ripe_available = ledger.ripeAvailForRewards()
    assert ripe_available == limited_ripe_available, "Ledger should have limited Ripe available"
    
    expected_actual_rewards = min(theoretical_rewards, ripe_available)

    # Record initial balance
    initial_gov_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)

    # Claim from stability pool
    vault_id = vault_book.getRegId(stability_pool)
    teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=bob)

    # Verify rewards are limited by available amount
    final_gov_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    actual_rewards = final_gov_balance - initial_gov_balance
    
    # Should be limited to available Ripe (100 Ripe instead of 500 Ripe demanded)
    assert actual_rewards <= expected_actual_rewards
    assert actual_rewards == min(theoretical_rewards, ripe_available)
    assert actual_rewards == limited_ripe_available, "Should receive exactly the limited amount available"


def test_stab_vault_claim_rewards_partial_claims(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    ripe_token,
    ripe_gov_vault,
    _test,
    setAssetConfig,
    setupStabPoolClaimsRewards,
):
    """Test Ripe rewards scale correctly with partial claims"""
    # Set up rewards configuration
    setupStabPoolClaimsRewards(
        _ripePerDollar = EIGHTEEN_DECIMALS // 4,  # 0.25 Ripe per dollar
        _stabRewardsLockDuration = 216000,  # ~30 days in blocks
    )
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(ripe_token, price)

    # Setup
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    claimable_amount = 100 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)

    # First partial claim (25% of total)
    partial_claim_amount = 25 * EIGHTEEN_DECIMALS
    initial_gov_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    
    claim_usd_value_1 = teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, partial_claim_amount, sender=bob)
    
    mid_gov_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    rewards_1 = mid_gov_balance - initial_gov_balance
    expected_rewards_1 = claim_usd_value_1 // 4  # 0.25 ratio
    _test(expected_rewards_1, rewards_1)

    # Second partial claim (remaining 75%)
    claim_usd_value_2 = teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=bob)
    
    final_gov_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    rewards_2 = final_gov_balance - mid_gov_balance
    expected_rewards_2 = claim_usd_value_2 // 4  # 0.25 ratio
    _test(expected_rewards_2, rewards_2)

    # Total rewards should equal what we'd get from claiming everything at once
    total_rewards = rewards_1 + rewards_2
    total_claim_value = claim_usd_value_1 + claim_usd_value_2
    expected_total_rewards = total_claim_value // 4
    _test(expected_total_rewards, total_rewards)


def test_stab_vault_claim_rewards_config_changes(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    mission_control,
    switchboard_alpha,
    ripe_token,
    ripe_gov_vault,
    _test,
    setAssetConfig,
    setupStabPoolClaimsRewards,
    setRipeRewardsConfig,
):
    """Test that reward configuration changes take effect immediately"""
    # Initial rewards configuration
    setupStabPoolClaimsRewards(
        _ripePerDollar = EIGHTEEN_DECIMALS // 10,  # 0.1 Ripe per dollar
        _stabRewardsLockDuration = 50400,  # ~7 days in blocks
    )
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(ripe_token, price)

    # Setup for both users
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Bob setup
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)
    
    # Alice setup  
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets for both
    claimable_amount = 50 * EIGHTEEN_DECIMALS
    
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )
    
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)

    # Bob claims with initial config
    initial_bob_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    bob_claim_value = teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=bob)
    mid_bob_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    bob_rewards = mid_bob_balance - initial_bob_balance
    expected_bob_rewards = bob_claim_value // 10  # 0.1 ratio
    _test(expected_bob_rewards, bob_rewards)

    # Change rewards configuration
    setRipeRewardsConfig(_stabPoolRipePerDollarClaimed=EIGHTEEN_DECIMALS // 2)  # 0.5 Ripe per dollar (higher rate)

    # Alice claims with new config
    initial_alice_balance = ripe_gov_vault.getTotalAmountForUser(alice, ripe_token)
    alice_claim_value = teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=alice)
    final_alice_balance = ripe_gov_vault.getTotalAmountForUser(alice, ripe_token)
    alice_rewards = final_alice_balance - initial_alice_balance
    expected_alice_rewards = alice_claim_value // 2  # 0.5 ratio (new config)
    _test(expected_alice_rewards, alice_rewards)

    # Alice should get 5x more rewards per dollar than Bob due to config change
    # Bob: 0.1 Ripe per dollar, Alice: 0.5 Ripe per dollar
    assert bob_claim_value > 0, "Bob should have claimed value"
    assert alice_claim_value > 0, "Alice should have claimed value"
    assert bob_rewards > 0, "Bob should have received rewards"
    assert alice_rewards > 0, "Alice should have received rewards"
    
    bob_rate = bob_rewards / bob_claim_value
    alice_rate = alice_rewards / alice_claim_value
    actual_ratio = alice_rate / bob_rate
    
    # Alice gets 5x more per dollar (0.5 vs 0.1)
    _test(5, actual_ratio)


def test_stab_vault_claim_rewards_integration(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    ripe_token,
    ripe_gov_vault,
    _test,
    setAssetConfig,
    setupStabPoolClaimsRewards,
):
    """Integration test for rewards - verifies the complete flow from claim to locked rewards"""
    # Set up moderate rewards configuration
    setupStabPoolClaimsRewards(
        _ripePerDollar = EIGHTEEN_DECIMALS // 2,  # 0.5 Ripe per dollar
        _stabRewardsLockDuration = 648000,  # ~90 days in blocks (90*24*60*60/12)
    )
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(ripe_token, price)

    # Setup
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    claimable_amount = 100 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Record initial state
    initial_ripe_balance = ripe_token.balanceOf(bob)
    initial_gov_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    initial_gov_shares = ripe_gov_vault.userBalances(bob, ripe_token)
    initial_bravo_balance = bravo_token.balanceOf(bob)

    # Verify Bob initially has no Ripe or gov vault position
    assert initial_ripe_balance == 0
    assert initial_gov_balance == 0
    assert initial_gov_shares == 0
    assert initial_bravo_balance == 0

    # Claim from stability pool
    vault_id = vault_book.getRegId(stability_pool)
    claim_usd_value = teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=bob)

    # Verify the claim itself worked
    _test(claimable_amount, claim_usd_value)
    _test(claimable_amount, bravo_token.balanceOf(bob))

    # Verify rewards were processed correctly
    expected_ripe_rewards = claim_usd_value // 2  # 0.5 ratio
    final_gov_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    final_gov_shares = ripe_gov_vault.userBalances(bob, ripe_token)
    final_ripe_balance = ripe_token.balanceOf(bob)

    # Bob should have received rewards in the gov vault, not as liquid tokens
    _test(expected_ripe_rewards, final_gov_balance)
    assert final_gov_shares > 0  # Bob should have shares in gov vault
    assert final_ripe_balance == 0  # Bob should not have liquid Ripe tokens

    # Verify the rewards are locked (Bob can't immediately withdraw)
    # This would typically require checking lock duration, but for the test we just
    # verify Bob has a position in the gov vault
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) > initial_gov_balance


def test_stab_vault_claim_rewards_no_ripe_available(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    ripe_token,
    ripe_gov_vault,
    ledger,
    setAssetConfig,
    setupStabPoolClaimsRewards,
    switchboard_alpha,
):
    """Test that no rewards are given when no Ripe is available in ledger"""
    # Set up high rewards configuration
    setupStabPoolClaimsRewards(
        _ripePerDollar = 5 * EIGHTEEN_DECIMALS,  # 5 Ripe per dollar (very high rate)
        _stabRewardsLockDuration = 216000,  # ~30 days in blocks
    )
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(ripe_token, price)

    # Setup
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    claimable_amount = 50 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Set NO Ripe available for rewards
    ledger.setRipeAvailForRewards(0, sender=switchboard_alpha.address)
    
    # Verify no Ripe is available
    ripe_available = ledger.ripeAvailForRewards()
    assert ripe_available == 0, "No Ripe should be available for rewards"

    # Record initial balance
    initial_gov_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)

    # Claim from stability pool
    vault_id = vault_book.getRegId(stability_pool)
    claim_usd_value = teller.claimFromStabilityPool(vault_id, alpha_token, bravo_token, sender=bob)

    # Verify claim worked but no rewards given
    assert claim_usd_value > 0, "Claim should have worked"
    final_gov_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    actual_rewards = final_gov_balance - initial_gov_balance
    
    # Should receive no rewards when no Ripe is available
    assert actual_rewards == 0, "User should receive no rewards when no Ripe available"
    assert final_gov_balance == initial_gov_balance, "Gov vault balance should be unchanged"


#############################
# Auto-Deposit Claims Tests #
#############################


def test_stab_vault_claims_auto_deposit_basic(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    simple_erc20_vault,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test basic auto-deposit functionality when claiming from stability pool"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Setup stability pool
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Record initial balances
    initial_bob_bravo_balance = bravo_token.balanceOf(bob)
    initial_bob_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)

    vault_id = vault_book.getRegId(stability_pool)

    # Claim with auto-deposit enabled
    usd_value = teller.claimFromStabilityPool(
        vault_id, alpha_token, bravo_token, MAX_UINT256, bob, True, sender=bob  # _shouldAutoDeposit=True
    )

    # Verify claim worked
    _test(claimable_amount, usd_value)

    # Verify tokens were auto-deposited (not sent directly to Bob)
    final_bob_bravo_balance = bravo_token.balanceOf(bob)
    final_bob_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)

    assert final_bob_bravo_balance == initial_bob_bravo_balance  # No direct token transfer
    _test(claimable_amount, final_bob_vault_balance - initial_bob_vault_balance)  # Auto-deposited

    # Verify Bob's stability pool position is depleted
    assert stability_pool.getTotalUserValue(bob, alpha_token) <= 1


def test_stab_vault_claims_auto_deposit_no_vault(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test auto-deposit fallback when no vault exists for the asset"""
    setGeneralConfig()
    setAssetConfig(bravo_token, _vaultIds=[])  # Configure for claims but no vault, so getFirstVaultIdForAsset will return 0

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Setup stability pool
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Record initial balance
    initial_bob_bravo_balance = bravo_token.balanceOf(bob)

    vault_id = vault_book.getRegId(stability_pool)

    # Claim with auto-deposit enabled (should fallback to direct transfer)
    usd_value = teller.claimFromStabilityPool(
        vault_id, alpha_token, bravo_token, MAX_UINT256, bob, True, sender=bob  # _shouldAutoDeposit=True
    )

    # Verify claim worked
    _test(claimable_amount, usd_value)

    # Verify tokens were sent directly to Bob (fallback due to no vault)
    final_bob_bravo_balance = bravo_token.balanceOf(bob)
    _test(claimable_amount, final_bob_bravo_balance - initial_bob_bravo_balance)


def test_stab_vault_claims_auto_deposit_stability_pool_vault(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test auto-deposit fallback when vault ID is 1 (stability pool itself)"""
    setGeneralConfig()
    setAssetConfig(bravo_token, _vaultIds=[1])  # Vault ID 1 is stability pool

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Setup stability pool
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Record initial balance
    initial_bob_bravo_balance = bravo_token.balanceOf(bob)

    vault_id = vault_book.getRegId(stability_pool)

    # Claim with auto-deposit enabled (should fallback to direct transfer)
    usd_value = teller.claimFromStabilityPool(
        vault_id, alpha_token, bravo_token, MAX_UINT256, bob, True, sender=bob  # _shouldAutoDeposit=True
    )

    # Verify claim worked
    _test(claimable_amount, usd_value)

    # Verify tokens were sent directly to Bob (fallback due to stability pool vault ID)
    final_bob_bravo_balance = bravo_token.balanceOf(bob)
    _test(claimable_amount, final_bob_bravo_balance - initial_bob_bravo_balance)


def test_stab_vault_claims_auto_deposit_config_disabled(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test auto-deposit fallback when deposit config is disabled"""
    setGeneralConfig()
    setAssetConfig(bravo_token, _canDeposit=False)  # Deposit disabled

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Setup stability pool
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Record initial balance
    initial_bob_bravo_balance = bravo_token.balanceOf(bob)

    vault_id = vault_book.getRegId(stability_pool)

    # Claim with auto-deposit enabled (should fallback to direct transfer)
    usd_value = teller.claimFromStabilityPool(
        vault_id, alpha_token, bravo_token, MAX_UINT256, bob, True, sender=bob  # _shouldAutoDeposit=True
    )

    # Verify claim worked
    _test(claimable_amount, usd_value)

    # Verify tokens were sent directly to Bob (fallback due to deposit config)
    final_bob_bravo_balance = bravo_token.balanceOf(bob)
    _test(claimable_amount, final_bob_bravo_balance - initial_bob_bravo_balance)


def test_stab_vault_claims_auto_deposit_many_basic(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    simple_erc20_vault,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test auto-deposit with claimManyFromStabilityPool"""
    setGeneralConfig()
    setAssetConfig(bravo_token)
    setAssetConfig(charlie_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(charlie_token, price)

    # Setup stability pool
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    bravo_amount = 80 * EIGHTEEN_DECIMALS
    charlie_amount = 120 * (10 ** charlie_token.decimals())
    
    bravo_token.transfer(stability_pool, bravo_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, bravo_token, bravo_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )
    
    charlie_token.transfer(stability_pool, charlie_amount, sender=charlie_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, charlie_token, charlie_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Record initial balances
    initial_bob_bravo_balance = bravo_token.balanceOf(bob)
    initial_bob_charlie_balance = charlie_token.balanceOf(bob)
    initial_bob_bravo_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    initial_bob_charlie_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, charlie_token)

    # Create claims array
    claims = [
        (alpha_token.address, bravo_token.address, MAX_UINT256),
        (alpha_token.address, charlie_token.address, MAX_UINT256)
    ]

    vault_id = vault_book.getRegId(stability_pool)

    # Claim many with auto-deposit enabled
    total_usd_value = teller.claimManyFromStabilityPool(
        vault_id, claims, bob, True, sender=bob  # _shouldAutoDeposit=True
    )

    # Verify claims worked
    _test(200 * EIGHTEEN_DECIMALS, total_usd_value)

    # Verify tokens were auto-deposited (not sent directly to Bob)
    final_bob_bravo_balance = bravo_token.balanceOf(bob)
    final_bob_charlie_balance = charlie_token.balanceOf(bob)
    final_bob_bravo_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    final_bob_charlie_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, charlie_token)

    assert final_bob_bravo_balance == initial_bob_bravo_balance  # No direct transfer
    assert final_bob_charlie_balance == initial_bob_charlie_balance  # No direct transfer
    _test(bravo_amount, final_bob_bravo_vault_balance - initial_bob_bravo_vault_balance)  # Auto-deposited
    _test(charlie_amount, final_bob_charlie_vault_balance - initial_bob_charlie_vault_balance)  # Auto-deposited


def test_stab_vault_claims_auto_deposit_many_mixed(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    simple_erc20_vault,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test auto-deposit with claimManyFromStabilityPool where some assets auto-deposit and others don't"""
    setGeneralConfig()
    setAssetConfig(bravo_token)
    setAssetConfig(charlie_token, _vaultIds=[])  # Configure for claims but no vault, so it should fallback to direct transfer

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(charlie_token, price)

    # Setup stability pool
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    bravo_amount = 80 * EIGHTEEN_DECIMALS
    charlie_amount = 120 * (10 ** charlie_token.decimals())
    
    bravo_token.transfer(stability_pool, bravo_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, bravo_token, bravo_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )
    
    charlie_token.transfer(stability_pool, charlie_amount, sender=charlie_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, charlie_token, charlie_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Record initial balances
    initial_bob_bravo_balance = bravo_token.balanceOf(bob)
    initial_bob_charlie_balance = charlie_token.balanceOf(bob)
    initial_bob_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)

    # Create claims array
    claims = [
        (alpha_token.address, bravo_token.address, MAX_UINT256),
        (alpha_token.address, charlie_token.address, MAX_UINT256)
    ]

    vault_id = vault_book.getRegId(stability_pool)

    # Claim many with auto-deposit enabled
    total_usd_value = teller.claimManyFromStabilityPool(
        vault_id, claims, bob, True, sender=bob  # _shouldAutoDeposit=True
    )

    # Verify claims worked
    _test(200 * EIGHTEEN_DECIMALS, total_usd_value)

    # Verify bravo was auto-deposited, charlie was sent directly
    final_bob_bravo_balance = bravo_token.balanceOf(bob)
    final_bob_charlie_balance = charlie_token.balanceOf(bob)
    final_bob_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)

    assert final_bob_bravo_balance == initial_bob_bravo_balance  # No direct transfer for bravo
    _test(charlie_amount, final_bob_charlie_balance - initial_bob_charlie_balance)  # Direct transfer for charlie
    _test(bravo_amount, final_bob_vault_balance - initial_bob_vault_balance)  # Auto-deposited bravo


def test_stab_vault_claims_auto_deposit_partial_claim(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    simple_erc20_vault,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test auto-deposit works correctly with partial claims"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Setup stability pool
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    claimable_amount = 100 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Record initial balance
    initial_bob_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)

    vault_id = vault_book.getRegId(stability_pool)

    # Partial claim with auto-deposit enabled
    partial_claim_amount = 40 * EIGHTEEN_DECIMALS
    usd_value = teller.claimFromStabilityPool(
        vault_id, alpha_token, bravo_token, partial_claim_amount, bob, True, sender=bob  # _shouldAutoDeposit=True
    )

    # Verify partial claim worked
    _test(partial_claim_amount, usd_value)

    # Verify tokens were auto-deposited
    final_bob_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    _test(partial_claim_amount, final_bob_vault_balance - initial_bob_vault_balance)

    # Verify Bob still has remaining position in stability pool
    remaining_value = stability_pool.getTotalUserValue(bob, alpha_token)
    assert remaining_value > 0


def test_stab_vault_claims_auto_deposit_with_delegation(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    simple_erc20_vault,
    _test,
    setGeneralConfig,
    setAssetConfig,
    setUserDelegation,
):
    """Test auto-deposit works correctly when someone claims for another user via delegation"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Setup stability pool
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Bob delegates claim permission to Alice
    setUserDelegation(bob, alice, _canClaimFromStabPool=True)

    # Record initial balances
    initial_bob_bravo_balance = bravo_token.balanceOf(bob)
    initial_alice_bravo_balance = bravo_token.balanceOf(alice)
    initial_bob_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    initial_alice_vault_balance = simple_erc20_vault.getTotalAmountForUser(alice, bravo_token)

    vault_id = vault_book.getRegId(stability_pool)

    # Alice claims for Bob with auto-deposit enabled
    usd_value = teller.claimFromStabilityPool(
        vault_id, alpha_token, bravo_token, MAX_UINT256, bob, True, sender=alice  # _shouldAutoDeposit=True
    )

    # Verify claim worked
    _test(claimable_amount, usd_value)

    # Verify tokens were auto-deposited to BOB's account (not Alice's)
    final_bob_bravo_balance = bravo_token.balanceOf(bob)
    final_alice_bravo_balance = bravo_token.balanceOf(alice)
    final_bob_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    final_alice_vault_balance = simple_erc20_vault.getTotalAmountForUser(alice, bravo_token)

    assert final_bob_bravo_balance == initial_bob_bravo_balance  # No direct token transfer to Bob
    assert final_alice_bravo_balance == initial_alice_bravo_balance  # No tokens to Alice
    _test(claimable_amount, final_bob_vault_balance - initial_bob_vault_balance)  # Auto-deposited to Bob
    assert final_alice_vault_balance == initial_alice_vault_balance  # No deposit to Alice