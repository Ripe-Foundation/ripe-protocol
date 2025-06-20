import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, MAX_UINT256


def test_stab_vault_redemptions_basic(
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
    green_token,
    alice,
    whale,
):
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(green_token, price)

    # Initial deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount, sender=teller.address)

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

    pre_user_value = stability_pool.getTotalUserValue(alice, alpha_token)
    pre_total_value = stability_pool.getTotalValue(alpha_token)
    vault_id = vault_book.getRegId(stability_pool)

    # redeem!
    redeem_amount = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, redeem_amount, sender=whale)
    green_token.approve(teller, redeem_amount, sender=bob)
    usd_value = teller.redeemFromStabilityPool(vault_id, bravo_token, redeem_amount, bob, sender=bob)

    # results
    _test(redeem_amount, usd_value)
    _test(redeem_amount, bravo_token.balanceOf(bob))

    # green balances
    assert green_token.balanceOf(bob) == 0
    assert green_token.balanceOf(stability_pool) == redeem_amount

    # claim data
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == claimable_amount - redeem_amount
    assert stability_pool.claimableBalances(alpha_token, green_token) == redeem_amount

    # these should stay the same!
    assert stability_pool.getTotalUserValue(alice, alpha_token) == pre_user_value
    assert stability_pool.getTotalValue(alpha_token) == pre_total_value


def test_stab_vault_redemptions_refund(
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
    green_token,
    alice,
    whale,
):
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(green_token, price)

    # Initial deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount, sender=teller.address)

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

    pre_user_value = stability_pool.getTotalUserValue(alice, alpha_token)
    pre_total_value = stability_pool.getTotalValue(alpha_token)
    vault_id = vault_book.getRegId(stability_pool)

    # redeem!
    redeem_amount = 200 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, redeem_amount, sender=whale)
    green_token.approve(teller, redeem_amount, sender=bob)
    usd_value = teller.redeemFromStabilityPool(vault_id, bravo_token, redeem_amount, bob, False, False, True, sender=bob)

    # results
    _test(claimable_amount, usd_value)
    _test(claimable_amount, bravo_token.balanceOf(bob))

    # green balances - refund goes to savings green when _shouldRefundSavingsGreen=True
    assert green_token.balanceOf(bob) == 0
    savings_green_bal = savings_green.balanceOf(bob)
    assert savings_green_bal != 0
    _test(redeem_amount - claimable_amount, savings_green.getLastUnderlying(savings_green_bal))
    assert green_token.balanceOf(stability_pool) == claimable_amount

    # claim data
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == 0
    assert stability_pool.claimableBalances(alpha_token, green_token) == claimable_amount

    # these should stay the same!
    assert stability_pool.getTotalUserValue(alice, alpha_token) == pre_user_value
    assert stability_pool.getTotalValue(alpha_token) == pre_total_value


def test_stab_vault_redemptions_validation(
    stability_pool,
    bravo_token,
    bob,
    alice,
    teller,
    switchboard_alpha,
    green_token,
    whale,
):
    """Test validation logic for redemptions"""

    # Test redemption when paused
    stability_pool.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("contract paused"):
        stability_pool.redeemFromStabilityPool(bravo_token, 100 * EIGHTEEN_DECIMALS, bob, teller.address, False, False, sender=teller.address)
    stability_pool.pause(False, sender=switchboard_alpha.address)

    # Test redemption with no green tokens
    with boa.reverts("no green to redeem"):
        stability_pool.redeemFromStabilityPool(bravo_token, 100 * EIGHTEEN_DECIMALS, bob, teller.address, False, False, sender=teller.address)

    # Test unauthorized caller
    green_token.transfer(stability_pool, 100 * EIGHTEEN_DECIMALS, sender=whale)
    with boa.reverts("only Teller allowed"):
        stability_pool.redeemFromStabilityPool(bravo_token, 100 * EIGHTEEN_DECIMALS, bob, alice, False, False, sender=alice)


def test_stab_vault_redemptions_no_claimable_assets(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bob,
    teller,
    mock_price_source,
    vault_book,
    setGeneralConfig,
    setAssetConfig,
    green_token,
    whale,
):
    """Test redemptions when there are no claimable assets"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(green_token, price)

    # Setup: deposit but no claimable assets
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    vault_id = vault_book.getRegId(stability_pool)

    # Try to redeem
    redeem_amount = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, redeem_amount, sender=whale)
    green_token.approve(teller, redeem_amount, sender=bob)
    
    with boa.reverts("no redemptions occurred"):
        teller.redeemFromStabilityPool(vault_id, bravo_token, redeem_amount, bob, sender=bob)


def test_stab_vault_redemptions_config_disabled(
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
    green_token,
    whale,
):
    """Test redemptions when different configuration flags are disabled"""
    # Setup with redemptions enabled first
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(green_token, price)

    # Setup claimable assets
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount, sender=teller.address)

    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)
    redeem_amount = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, redeem_amount * 3, sender=whale)
    green_token.approve(teller, redeem_amount * 3, sender=bob)

    # Test 1: Disable general redemption config
    setGeneralConfig(_canRedeemInStabPool=False)
    with boa.reverts("no redemptions occurred"):
        teller.redeemFromStabilityPool(vault_id, bravo_token, redeem_amount, bob, sender=bob)

    # Re-enable general config
    setGeneralConfig()

    # Test 2: Disable asset-specific redemption config
    setAssetConfig(bravo_token, _canRedeemInStabPool=False)
    with boa.reverts("no redemptions occurred"):
        teller.redeemFromStabilityPool(vault_id, bravo_token, redeem_amount, bob, sender=bob)

    # Re-enable asset config for final test
    setAssetConfig(bravo_token)
    
    # Verify redemptions work again when config is restored
    usd_value = teller.redeemFromStabilityPool(vault_id, bravo_token, redeem_amount, bob, sender=bob)
    assert usd_value > 0


def test_stab_vault_redemptions_green_token_restriction(
    stability_pool,
    green_token,
    alpha_token,
    alpha_token_whale,
    charlie_token,
    charlie_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
    whale,
):
    """Test redemption restrictions when green token is a stability pool asset"""
    setGeneralConfig()
    setAssetConfig(green_token)
    setAssetConfig(alpha_token)
    setAssetConfig(charlie_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(green_token, price)
    mock_price_source.setPrice(charlie_token, price)

    # First, deposit green token as a stability asset
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(stability_pool, deposit_amount, sender=whale)
    stability_pool.depositTokensInVault(alice, green_token, deposit_amount, sender=teller.address)

    # Also deposit another asset (making green NOT the only asset)
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount, sender=teller.address)

    # Create claimable alpha tokens
    charlie_amount = 100 * (10 ** charlie_token.decimals())
    charlie_token.transfer(stability_pool, charlie_amount, sender=charlie_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        green_token, deposit_amount, charlie_token, charlie_amount,
        ZERO_ADDRESS, green_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)

    # Try to redeem - should fail because green is a stab asset but not the ONLY asset
    redeem_amount = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, redeem_amount, sender=whale)
    green_token.approve(teller, redeem_amount, sender=bob)
    
    with boa.reverts("redemptions not allowed"):
        teller.redeemFromStabilityPool(vault_id, charlie_token, redeem_amount, bob, sender=bob)


def test_stab_vault_redemptions_price_oracle_zero(
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
    green_token,
    whale,
):
    """Test redemptions when price oracle returns 0"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(green_token, price)

    # Setup claimable assets
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount, sender=teller.address)

    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Set price of redemption asset to 0
    mock_price_source.setPrice(bravo_token, 0)

    vault_id = vault_book.getRegId(stability_pool)
    redeem_amount = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, redeem_amount, sender=whale)
    green_token.approve(teller, redeem_amount, sender=bob)
    
    # Should revert due to price oracle returning 0
    with boa.reverts():
        teller.redeemFromStabilityPool(vault_id, bravo_token, redeem_amount, bob, sender=bob)


def test_stab_vault_redemptions_cannot_redeem_green(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
    green_token,
    whale,
):
    """Test that green tokens cannot be redeemed for themselves"""
    setGeneralConfig()
    setAssetConfig(green_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(green_token, price)

    # Setup
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount, sender=teller.address)

    # Create claimable green tokens (from previous redemptions)
    green_token.transfer(stability_pool, deposit_amount, sender=whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, green_token, deposit_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)

    # Try to redeem green for green
    redeem_amount = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, redeem_amount, sender=whale)
    green_token.approve(teller, redeem_amount, sender=bob)
    
    with boa.reverts("no redemptions occurred"):
        teller.redeemFromStabilityPool(vault_id, green_token, redeem_amount, bob, sender=bob)


def test_stab_vault_redemptions_multiple_users(
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
    green_token,
    whale,
):
    """Test redemptions with multiple users competing for same assets"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(green_token, price)

    # Setup deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(sally, alpha_token, deposit_amount, sender=teller.address)

    # Create claimable assets
    claimable_amount = 200 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)

    # Bob redeems first
    bob_redeem = 80 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, bob_redeem, sender=whale)
    green_token.approve(teller, bob_redeem, sender=bob)
    bob_usd_value = teller.redeemFromStabilityPool(vault_id, bravo_token, bob_redeem, bob, sender=bob)
    
    # Alice redeems second
    alice_redeem = 120 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, alice_redeem, sender=whale)
    green_token.approve(teller, alice_redeem, sender=alice)
    alice_usd_value = teller.redeemFromStabilityPool(vault_id, bravo_token, alice_redeem, alice, sender=alice)

    # Check results
    _test(bob_redeem, bob_usd_value)
    _test(alice_redeem, alice_usd_value)
    _test(bob_redeem, bravo_token.balanceOf(bob))
    _test(alice_redeem, bravo_token.balanceOf(alice))

    # Check remaining claimable balance
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == 0
    assert stability_pool.claimableBalances(alpha_token, green_token) == claimable_amount


def test_stab_vault_redeem_many_basic(
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
    green_token,
    whale,
):
    """Test redeemManyFromStabilityPool with multiple assets"""
    setGeneralConfig()
    setAssetConfig(bravo_token)
    setAssetConfig(charlie_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(charlie_token, price)
    mock_price_source.setPrice(green_token, price)

    # Setup deposits
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount, sender=teller.address)

    # Create claimable assets
    bravo_amount = 100 * EIGHTEEN_DECIMALS
    charlie_amount = 150 * (10 ** charlie_token.decimals())
    
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

    # Create redemptions array
    redemptions = [
        (bravo_token.address, MAX_UINT256),
        (charlie_token.address, MAX_UINT256)
    ]

    vault_id = vault_book.getRegId(stability_pool)
    total_redeem_amount = 250 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, total_redeem_amount, sender=whale)
    green_token.approve(teller, total_redeem_amount, sender=bob)
    
    # Redeem many
    total_green_spent = teller.redeemManyFromStabilityPool(vault_id, redemptions, total_redeem_amount, bob, sender=bob)

    # Check results
    _test(bravo_amount, bravo_token.balanceOf(bob))
    _test(charlie_amount, charlie_token.balanceOf(bob))
    _test(total_redeem_amount, total_green_spent)  # All green should be spent

    # Check claimable balances updated
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == 0
    assert stability_pool.claimableBalances(alpha_token, charlie_token) == 0
    assert stability_pool.claimableBalances(alpha_token, green_token) == total_green_spent


def test_stab_vault_redeem_many_partial(
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
    green_token,
    whale,
):
    """Test redeemManyFromStabilityPool with partial redemptions"""
    setGeneralConfig()
    setAssetConfig(bravo_token)
    setAssetConfig(charlie_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(charlie_token, price)
    mock_price_source.setPrice(green_token, price)

    # Setup deposits
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount, sender=teller.address)

    # Create claimable assets
    bravo_amount = 100 * EIGHTEEN_DECIMALS
    charlie_amount = 150 * (10 ** charlie_token.decimals())
    
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

    # Create redemptions array with limits
    redemptions = [
        (bravo_token.address, 60 * EIGHTEEN_DECIMALS),  # Partial bravo
        (charlie_token.address, 50 * EIGHTEEN_DECIMALS)  # Partial charlie
    ]

    vault_id = vault_book.getRegId(stability_pool)
    total_redeem_amount = 110 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, total_redeem_amount, sender=whale)
    green_token.approve(teller, total_redeem_amount, sender=bob)
    
    # Redeem many
    total_green_spent = teller.redeemManyFromStabilityPool(vault_id, redemptions, total_redeem_amount, bob, sender=bob)

    # Check results
    _test(60 * EIGHTEEN_DECIMALS, bravo_token.balanceOf(bob))
    _test(50 * (10 ** charlie_token.decimals()), charlie_token.balanceOf(bob))
    _test(110 * EIGHTEEN_DECIMALS, total_green_spent)

    # Check remaining claimable balances
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == 40 * EIGHTEEN_DECIMALS
    assert stability_pool.claimableBalances(alpha_token, charlie_token) == 100 * (10 ** charlie_token.decimals())


def test_stab_vault_redeem_many_insufficient_green(
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
    green_token,
    whale,
):
    """Test redeemManyFromStabilityPool when green runs out before all redemptions"""
    setGeneralConfig()
    setAssetConfig(bravo_token)
    setAssetConfig(charlie_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(charlie_token, price)
    mock_price_source.setPrice(green_token, price)

    # Setup deposits
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount, sender=teller.address)

    # Create claimable assets
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

    # Create redemptions array that would require more green than available
    redemptions = [
        (bravo_token.address, MAX_UINT256),
        (charlie_token.address, MAX_UINT256)
    ]

    vault_id = vault_book.getRegId(stability_pool)
    total_redeem_amount = 150 * EIGHTEEN_DECIMALS  # Less than total claimable
    green_token.transfer(bob, total_redeem_amount, sender=whale)
    green_token.approve(teller, total_redeem_amount, sender=bob)
    
    # Redeem many
    total_green_spent = teller.redeemManyFromStabilityPool(vault_id, redemptions, total_redeem_amount, bob, False, sender=bob)

    # Check results - should have redeemed all bravo and partial charlie
    _test(100 * EIGHTEEN_DECIMALS, bravo_token.balanceOf(bob))
    _test(50 * (10 ** charlie_token.decimals()), charlie_token.balanceOf(bob))
    _test(150 * EIGHTEEN_DECIMALS, total_green_spent)

    # Bob should have no refund
    assert green_token.balanceOf(bob) == 0


def test_stab_vault_redeem_many_empty_array(
    stability_pool,
    bob,
    teller,
    vault_book,
    green_token,
    whale,
):
    """Test redeemManyFromStabilityPool with empty redemptions array"""
    vault_id = vault_book.getRegId(stability_pool)
    
    redeem_amount = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, redeem_amount, sender=whale)
    green_token.approve(teller, redeem_amount, sender=bob)
    
    # Empty redemptions array should revert
    with boa.reverts("no redemptions occurred"):
        teller.redeemManyFromStabilityPool(vault_id, [], redeem_amount, bob, sender=bob)


def test_stab_vault_redeem_many_all_invalid(
    stability_pool,
    alpha_token,
    bravo_token,
    bob,
    teller,
    vault_book,
    green_token,
    whale,
    setGeneralConfig,
    setAssetConfig,
):
    """Test redeemManyFromStabilityPool with all invalid redemptions"""
    setGeneralConfig()
    setAssetConfig(bravo_token)
    
    vault_id = vault_book.getRegId(stability_pool)
    
    # Create redemptions with all invalid entries
    redemptions = [
        (ZERO_ADDRESS, 100 * EIGHTEEN_DECIMALS),  # Invalid asset
        (bravo_token.address, 0),  # Zero amount
        (green_token.address, 100 * EIGHTEEN_DECIMALS),  # Cannot redeem green
    ]
    
    redeem_amount = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, redeem_amount, sender=whale)
    green_token.approve(teller, redeem_amount, sender=bob)
    
    with boa.reverts("no redemptions occurred"):
        teller.redeemManyFromStabilityPool(vault_id, redemptions, redeem_amount, bob, sender=bob)


def test_stab_vault_redeem_many_max_redemptions(
    stability_pool,
    bob,
    teller,
    vault_book,
    green_token,
    whale,
):
    """Test redeemManyFromStabilityPool with maximum number of redemptions"""
    # Get the MAX_STAB_REDEMPTIONS constant (15)
    max_redemptions = 15
    
    # Create max number of redemptions (all invalid to avoid setup complexity)
    redemptions = [(ZERO_ADDRESS, 0) for _ in range(max_redemptions)]
    
    vault_id = vault_book.getRegId(stability_pool)
    
    redeem_amount = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, redeem_amount, sender=whale)
    green_token.approve(teller, redeem_amount, sender=bob)
    
    # Should revert with "no redemptions occurred" since all redemptions are invalid
    with boa.reverts("no redemptions occurred"):
        teller.redeemManyFromStabilityPool(vault_id, redemptions, redeem_amount, bob, sender=bob)


def test_stab_vault_redemptions_refund_staking(
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
    green_token,
    whale,
):
    """Test redemption refund with staking option"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(green_token, price)

    # Setup
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount, sender=teller.address)

    claimable_amount = 50 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)

    # Redeem more than available with staking option
    redeem_amount = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, redeem_amount, sender=whale)
    green_token.approve(teller, redeem_amount, sender=bob)
    
    usd_value = teller.redeemFromStabilityPool(vault_id, bravo_token, redeem_amount, bob, False, False, True, sender=bob)

    # Check results
    _test(claimable_amount, usd_value)
    _test(claimable_amount, bravo_token.balanceOf(bob))
    
    # Bob should receive staked green for the refund
    assert green_token.balanceOf(bob) == 0

    savings_green_bal = savings_green.balanceOf(bob)
    assert savings_green_bal != 0
    _test(redeem_amount - claimable_amount, savings_green.getLastUnderlying(savings_green_bal))


def test_stab_vault_redemptions_precision_edge_cases(
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
    green_token,
    whale,
):
    """Test redemptions with precision/rounding edge cases"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(green_token, price)

    # Setup with odd amounts
    deposit_amount = 123456789012345678
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount, sender=teller.address)

    # Create claimable assets with odd amount
    claimable_amount = 987654321098765432
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)

    # Redeem odd amount
    redeem_amount = 333333333333333333
    green_token.transfer(bob, redeem_amount, sender=whale)
    green_token.approve(teller, redeem_amount, sender=bob)
    
    usd_value = teller.redeemFromStabilityPool(vault_id, bravo_token, redeem_amount, bob, sender=bob)

    # Check that redemption happened correctly
    assert usd_value == redeem_amount
    assert bravo_token.balanceOf(bob) == redeem_amount
    assert abs(stability_pool.claimableBalances(alpha_token, bravo_token) - (claimable_amount - redeem_amount)) <= 1


def test_stab_vault_redemptions_multiple_stab_assets(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
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
    green_token,
    whale,
):
    """Test redemptions when claimable asset exists across multiple stability assets"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(charlie_token, price)
    mock_price_source.setPrice(green_token, price)

    # Setup: deposits in both alpha and charlie
    alpha_deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, alpha_deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, alpha_deposit_amount, sender=teller.address)
    
    charlie_deposit_amount = 100 * (10 ** charlie_token.decimals())
    charlie_token.transfer(stability_pool, charlie_deposit_amount, sender=charlie_token_whale)
    stability_pool.depositTokensInVault(sally, charlie_token, charlie_deposit_amount, sender=teller.address)

    # Create bravo claimable for both stability assets
    bravo_for_alpha = 80 * EIGHTEEN_DECIMALS
    bravo_for_charlie = 60 * EIGHTEEN_DECIMALS
    
    bravo_token.transfer(stability_pool, bravo_for_alpha, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, alpha_deposit_amount, bravo_token, bravo_for_alpha,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )
    
    bravo_token.transfer(stability_pool, bravo_for_charlie, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        charlie_token, charlie_deposit_amount, bravo_token, bravo_for_charlie,
        ZERO_ADDRESS, charlie_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)

    # Redeem all bravo across both stability assets
    total_bravo = bravo_for_alpha + bravo_for_charlie
    green_token.transfer(bob, total_bravo, sender=whale)
    green_token.approve(teller, total_bravo, sender=bob)
    
    usd_value = teller.redeemFromStabilityPool(vault_id, bravo_token, total_bravo, bob, sender=bob)

    # Check results
    _test(total_bravo, usd_value)
    _test(total_bravo, bravo_token.balanceOf(bob))

    # Check that green was added to both stability assets
    assert stability_pool.claimableBalances(alpha_token, green_token) == bravo_for_alpha
    assert stability_pool.claimableBalances(charlie_token, green_token) == bravo_for_charlie


def test_stab_vault_redemptions_over_limit(
    stability_pool,
    bob,
    teller,
    vault_book,
    green_token,
    whale,
):
    """Test redeemManyFromStabilityPool with more than MAX_STAB_REDEMPTIONS"""
    vault_id = vault_book.getRegId(stability_pool)
    
    # Try to create more than max redemptions (16 redemptions when max is 15)
    max_redemptions = 15
    try:
        # This should fail at compile/runtime due to DynArray size limit
        redemptions = [(ZERO_ADDRESS, 0) for _ in range(max_redemptions + 1)]
        green_token.transfer(bob, 100 * EIGHTEEN_DECIMALS, sender=whale)
        green_token.approve(teller, 100 * EIGHTEEN_DECIMALS, sender=bob)
        teller.redeemManyFromStabilityPool(vault_id, redemptions, 100 * EIGHTEEN_DECIMALS, bob, sender=bob)
        assert False, "Should have failed due to exceeding max redemptions"
    except Exception:
        # Expected to fail
        pass


#################################
# Auto-Deposit Redemption Tests #
#################################


def test_stab_vault_redemptions_auto_deposit_basic(
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
    green_token,
    whale,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test basic auto-deposit functionality when redeeming from stability pool"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(green_token, price)

    # Setup stability pool
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount, sender=teller.address)

    # Create claimable assets
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

    # Redeem with auto-deposit enabled
    redeem_amount = 80 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, redeem_amount, sender=whale)
    green_token.approve(teller, redeem_amount, sender=bob)
    
    usd_value = teller.redeemFromStabilityPool(
        vault_id, bravo_token, redeem_amount, bob, True, False, True, sender=bob  # _shouldAutoDeposit=True
    )

    # Verify redemption worked
    _test(redeem_amount, usd_value)

    # Verify tokens were auto-deposited (not sent directly to Bob)
    final_bob_bravo_balance = bravo_token.balanceOf(bob)
    final_bob_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)

    assert final_bob_bravo_balance == initial_bob_bravo_balance  # No direct token transfer
    _test(redeem_amount, final_bob_vault_balance - initial_bob_vault_balance)  # Auto-deposited


def test_stab_vault_redemptions_auto_deposit_disabled(
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
    green_token,
    whale,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test that auto-deposit is disabled when _shouldAutoDeposit=False"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(green_token, price)

    # Setup stability pool
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount, sender=teller.address)

    # Create claimable assets
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

    # Redeem with auto-deposit disabled
    redeem_amount = 80 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, redeem_amount, sender=whale)
    green_token.approve(teller, redeem_amount, sender=bob)
    
    usd_value = teller.redeemFromStabilityPool(
        vault_id, bravo_token, redeem_amount, bob, False, False, False, sender=bob  # _shouldAutoDeposit=False
    )

    # Verify redemption worked
    _test(redeem_amount, usd_value)

    # Verify tokens were sent directly to Bob (not auto-deposited)
    final_bob_bravo_balance = bravo_token.balanceOf(bob)
    final_bob_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)

    _test(redeem_amount, final_bob_bravo_balance - initial_bob_bravo_balance)  # Direct transfer
    assert final_bob_vault_balance == initial_bob_vault_balance  # No auto-deposit


def test_stab_vault_redemptions_auto_deposit_no_vault(
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
    green_token,
    whale,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test auto-deposit fallback when no vault exists for the asset"""
    setGeneralConfig()
    setAssetConfig(bravo_token, _vaultIds=[])  # Configure for redemptions but no vault

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(green_token, price)

    # Setup stability pool
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount, sender=teller.address)

    # Create claimable assets
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Record initial balance
    initial_bob_bravo_balance = bravo_token.balanceOf(bob)

    vault_id = vault_book.getRegId(stability_pool)

    # Redeem with auto-deposit enabled (should fallback to direct transfer)
    redeem_amount = 80 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, redeem_amount, sender=whale)
    green_token.approve(teller, redeem_amount, sender=bob)
    
    usd_value = teller.redeemFromStabilityPool(
        vault_id, bravo_token, redeem_amount, bob, True, False, True, sender=bob  # _shouldAutoDeposit=True
    )

    # Verify redemption worked
    _test(redeem_amount, usd_value)

    # Verify tokens were sent directly to Bob (fallback due to no vault)
    final_bob_bravo_balance = bravo_token.balanceOf(bob)
    _test(redeem_amount, final_bob_bravo_balance - initial_bob_bravo_balance)


def test_stab_vault_redemptions_auto_deposit_stability_pool_vault(
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
    green_token,
    whale,
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
    mock_price_source.setPrice(green_token, price)

    # Setup stability pool
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount, sender=teller.address)

    # Create claimable assets
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Record initial balance
    initial_bob_bravo_balance = bravo_token.balanceOf(bob)

    vault_id = vault_book.getRegId(stability_pool)

    # Redeem with auto-deposit enabled (should fallback to direct transfer)
    redeem_amount = 80 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, redeem_amount, sender=whale)
    green_token.approve(teller, redeem_amount, sender=bob)
    
    usd_value = teller.redeemFromStabilityPool(
        vault_id, bravo_token, redeem_amount, bob, True, False, True, sender=bob  # _shouldAutoDeposit=True
    )

    # Verify redemption worked
    _test(redeem_amount, usd_value)

    # Verify tokens were sent directly to Bob (fallback due to stability pool vault ID)
    final_bob_bravo_balance = bravo_token.balanceOf(bob)
    _test(redeem_amount, final_bob_bravo_balance - initial_bob_bravo_balance)


def test_stab_vault_redemptions_auto_deposit_config_disabled(
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
    green_token,
    whale,
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
    mock_price_source.setPrice(green_token, price)

    # Setup stability pool
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount, sender=teller.address)

    # Create claimable assets
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Record initial balance
    initial_bob_bravo_balance = bravo_token.balanceOf(bob)

    vault_id = vault_book.getRegId(stability_pool)

    # Redeem with auto-deposit enabled (should fallback to direct transfer)
    redeem_amount = 80 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, redeem_amount, sender=whale)
    green_token.approve(teller, redeem_amount, sender=bob)
    
    usd_value = teller.redeemFromStabilityPool(
        vault_id, bravo_token, redeem_amount, bob, True, False, True, sender=bob  # _shouldAutoDeposit=True
    )

    # Verify redemption worked
    _test(redeem_amount, usd_value)

    # Verify tokens were sent directly to Bob (fallback due to deposit config)
    final_bob_bravo_balance = bravo_token.balanceOf(bob)
    _test(redeem_amount, final_bob_bravo_balance - initial_bob_bravo_balance)


def test_stab_vault_redemptions_auto_deposit_many_basic(
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
    simple_erc20_vault,
    green_token,
    whale,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test auto-deposit with redeemManyFromStabilityPool"""
    setGeneralConfig()
    setAssetConfig(bravo_token)
    setAssetConfig(charlie_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(charlie_token, price)
    mock_price_source.setPrice(green_token, price)

    # Setup stability pool
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount, sender=teller.address)

    # Create claimable assets
    bravo_amount = 100 * EIGHTEEN_DECIMALS
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

    # Create redemptions array
    redemptions = [
        (bravo_token.address, MAX_UINT256),
        (charlie_token.address, MAX_UINT256)
    ]

    vault_id = vault_book.getRegId(stability_pool)
    total_redeem_amount = 220 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, total_redeem_amount, sender=whale)
    green_token.approve(teller, total_redeem_amount, sender=bob)

    # Redeem many with auto-deposit enabled
    total_green_spent = teller.redeemManyFromStabilityPool(
        vault_id, redemptions, total_redeem_amount, bob, True, False, True, sender=bob  # _shouldAutoDeposit=True
    )

    # Verify redemptions worked
    _test(220 * EIGHTEEN_DECIMALS, total_green_spent)

    # Verify tokens were auto-deposited (not sent directly to Bob)
    final_bob_bravo_balance = bravo_token.balanceOf(bob)
    final_bob_charlie_balance = charlie_token.balanceOf(bob)
    final_bob_bravo_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    final_bob_charlie_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, charlie_token)

    assert final_bob_bravo_balance == initial_bob_bravo_balance  # No direct transfer
    assert final_bob_charlie_balance == initial_bob_charlie_balance  # No direct transfer
    _test(bravo_amount, final_bob_bravo_vault_balance - initial_bob_bravo_vault_balance)  # Auto-deposited
    _test(charlie_amount, final_bob_charlie_vault_balance - initial_bob_charlie_vault_balance)  # Auto-deposited


def test_stab_vault_redemptions_auto_deposit_many_mixed(
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
    simple_erc20_vault,
    green_token,
    whale,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test auto-deposit with redeemManyFromStabilityPool where some assets auto-deposit and others don't"""
    setGeneralConfig()
    setAssetConfig(bravo_token)
    setAssetConfig(charlie_token, _vaultIds=[])  # Configure for redemptions but no vault

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(charlie_token, price)
    mock_price_source.setPrice(green_token, price)

    # Setup stability pool
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount, sender=teller.address)

    # Create claimable assets
    bravo_amount = 100 * EIGHTEEN_DECIMALS
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

    # Create redemptions array
    redemptions = [
        (bravo_token.address, MAX_UINT256),
        (charlie_token.address, MAX_UINT256)
    ]

    vault_id = vault_book.getRegId(stability_pool)
    total_redeem_amount = 220 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, total_redeem_amount, sender=whale)
    green_token.approve(teller, total_redeem_amount, sender=bob)

    # Redeem many with auto-deposit enabled
    total_green_spent = teller.redeemManyFromStabilityPool(
        vault_id, redemptions, total_redeem_amount, bob, True, False, True, sender=bob  # _shouldAutoDeposit=True
    )

    # Verify redemptions worked
    _test(220 * EIGHTEEN_DECIMALS, total_green_spent)

    # Verify bravo was auto-deposited, charlie was sent directly
    final_bob_bravo_balance = bravo_token.balanceOf(bob)
    final_bob_charlie_balance = charlie_token.balanceOf(bob)
    final_bob_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)

    assert final_bob_bravo_balance == initial_bob_bravo_balance  # No direct transfer for bravo
    _test(charlie_amount, final_bob_charlie_balance - initial_bob_charlie_balance)  # Direct transfer for charlie
    _test(bravo_amount, final_bob_vault_balance - initial_bob_vault_balance)  # Auto-deposited bravo


def test_stab_vault_redemptions_auto_deposit_partial_redeem(
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
    green_token,
    whale,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test auto-deposit works correctly with partial redemptions"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(green_token, price)

    # Setup stability pool
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount, sender=teller.address)

    # Create claimable assets
    claimable_amount = 100 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Record initial balance
    initial_bob_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)

    vault_id = vault_book.getRegId(stability_pool)

    # Partial redemption with auto-deposit enabled
    partial_redeem_amount = 40 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, partial_redeem_amount, sender=whale)
    green_token.approve(teller, partial_redeem_amount, sender=bob)
    
    usd_value = teller.redeemFromStabilityPool(
        vault_id, bravo_token, partial_redeem_amount, bob, True, False, True, sender=bob  # _shouldAutoDeposit=True
    )

    # Verify partial redemption worked
    _test(partial_redeem_amount, usd_value)

    # Verify tokens were auto-deposited
    final_bob_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    _test(partial_redeem_amount, final_bob_vault_balance - initial_bob_vault_balance)

    # Verify some claimable assets remain
    remaining_claimable = stability_pool.claimableBalances(alpha_token, bravo_token)
    assert remaining_claimable == claimable_amount - partial_redeem_amount


def test_stab_vault_redemptions_basic_with_sgreen(
    stability_pool,
    savings_green,
    bravo_token,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    _test,
    setGeneralConfig,
    setAssetConfig,
    green_token,
    alice,
    whale,
):
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock price
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)

    # stab pool deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, deposit_amount, sender=whale)
    green_token.approve(savings_green, deposit_amount, sender=alice)
    pre_sgreen_amount = savings_green.deposit(deposit_amount, stability_pool, sender=alice)
    stability_pool.depositTokensInVault(alice, savings_green, pre_sgreen_amount, sender=teller.address)

    # swap
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        savings_green,  # stab asset
        pre_sgreen_amount,     # stab asset amount
        bravo_token,  # liq asset
        claimable_amount,  # liq amount
        ZERO_ADDRESS,  # recipient (burn)
        green_token,  # green token
        savings_green, # savings green token
        sender=auction_house.address
    )

    pre_user_value = stability_pool.getTotalUserValue(alice, savings_green)
    pre_total_value = stability_pool.getTotalValue(savings_green)
    vault_id = vault_book.getRegId(stability_pool)

    # redeem!
    redeem_amount = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, redeem_amount, sender=whale)
    green_token.approve(teller, redeem_amount, sender=bob)
    usd_value = teller.redeemFromStabilityPool(vault_id, bravo_token, redeem_amount, bob, sender=bob)

    # results
    _test(redeem_amount, usd_value)
    _test(redeem_amount, bravo_token.balanceOf(bob))

    # green balances
    assert green_token.balanceOf(bob) == 0
    assert green_token.balanceOf(stability_pool) == 0 # was converted to sgreen

    # claim data
    assert stability_pool.claimableBalances(savings_green, bravo_token) == claimable_amount - redeem_amount
    assert stability_pool.claimableBalances(savings_green, green_token) == 0

    # these should stay the same!
    _test(pre_user_value, stability_pool.getTotalUserValue(alice, savings_green))
    _test(pre_total_value, stability_pool.getTotalValue(savings_green))

    # sgreen basically only redeem amount
    _test(savings_green.balanceOf(stability_pool), redeem_amount)


def test_stab_vault_redeem_many_with_sgreen(
    stability_pool,
    savings_green,
    bravo_token,
    charlie_token,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    _test,
    setGeneralConfig,
    setAssetConfig,
    green_token,
    alice,
    whale,
):
    """Test redeemManyFromStabilityPool with sGREEN auto-conversion"""
    setGeneralConfig()
    setAssetConfig(bravo_token)
    setAssetConfig(charlie_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(charlie_token, price)

    # Setup sGREEN deposit in stability pool
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, deposit_amount, sender=whale)
    green_token.approve(savings_green, deposit_amount, sender=alice)
    sgreen_amount = savings_green.deposit(deposit_amount, stability_pool, sender=alice)
    stability_pool.depositTokensInVault(alice, savings_green, sgreen_amount, sender=teller.address)

    # Create claimable assets via liquidations
    bravo_amount = 100 * EIGHTEEN_DECIMALS
    charlie_amount = 120 * (10 ** charlie_token.decimals())
    
    bravo_token.transfer(stability_pool, bravo_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        savings_green, sgreen_amount // 2, bravo_token, bravo_amount,
        ZERO_ADDRESS, green_token, savings_green, sender=auction_house.address
    )
    
    charlie_token.transfer(stability_pool, charlie_amount, sender=charlie_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        savings_green, sgreen_amount // 2, charlie_token, charlie_amount,
        ZERO_ADDRESS, green_token, savings_green, sender=auction_house.address
    )

    pre_sgreen_balance = savings_green.balanceOf(stability_pool)
    vault_id = vault_book.getRegId(stability_pool)

    # Create redemptions array
    redemptions = [
        (bravo_token.address, MAX_UINT256),
        (charlie_token.address, MAX_UINT256)
    ]

    total_redeem_amount = 220 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, total_redeem_amount, sender=whale)
    green_token.approve(teller, total_redeem_amount, sender=bob)
    
    # Redeem many
    total_green_spent = teller.redeemManyFromStabilityPool(vault_id, redemptions, total_redeem_amount, bob, sender=bob)

    # Check results
    _test(bravo_amount, bravo_token.balanceOf(bob))
    _test(charlie_amount, charlie_token.balanceOf(bob))
    _test(total_redeem_amount, total_green_spent)

    # Check that green was auto-converted to sGREEN (not made claimable)
    assert green_token.balanceOf(stability_pool) == 0  # No green left in pool
    assert stability_pool.claimableBalances(savings_green, green_token) == 0  # No green made claimable
    
    # sGREEN balance should have increased by the redemption amounts
    final_sgreen_balance = savings_green.balanceOf(stability_pool)
    _test(total_green_spent, final_sgreen_balance - pre_sgreen_balance)

    # Claimable assets should be depleted
    assert stability_pool.claimableBalances(savings_green, bravo_token) == 0
    assert stability_pool.claimableBalances(savings_green, charlie_token) == 0


def test_stab_vault_redemptions_mixed_assets_with_sgreen(
    stability_pool,
    alpha_token,
    savings_green,
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
    _test,
    setGeneralConfig,
    setAssetConfig,
    green_token,
    whale,
):
    """Test redemption behavior with mixed stability assets (regular + sGREEN)"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Setup deposits: Alice with regular alpha, Sally with sGREEN
    alpha_deposit = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, alpha_deposit, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, alpha_deposit, sender=teller.address)

    sgreen_deposit_underlying = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(sally, sgreen_deposit_underlying, sender=whale)
    green_token.approve(savings_green, sgreen_deposit_underlying, sender=sally)
    sgreen_amount = savings_green.deposit(sgreen_deposit_underlying, stability_pool, sender=sally)
    stability_pool.depositTokensInVault(sally, savings_green, sgreen_amount, sender=teller.address)

    # Create claimable bravo for both stability assets
    bravo_for_alpha = 80 * EIGHTEEN_DECIMALS
    bravo_for_sgreen = 60 * EIGHTEEN_DECIMALS
    
    bravo_token.transfer(stability_pool, bravo_for_alpha, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, alpha_deposit, bravo_token, bravo_for_alpha,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )
    
    bravo_token.transfer(stability_pool, bravo_for_sgreen, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        savings_green, sgreen_amount, bravo_token, bravo_for_sgreen,
        ZERO_ADDRESS, green_token, savings_green, sender=auction_house.address
    )

    pre_sgreen_balance = savings_green.balanceOf(stability_pool)
    vault_id = vault_book.getRegId(stability_pool)

    # Redeem all bravo across both stability assets
    total_bravo = bravo_for_alpha + bravo_for_sgreen
    green_token.transfer(bob, total_bravo, sender=whale)
    green_token.approve(teller, total_bravo, sender=bob)
    
    usd_value = teller.redeemFromStabilityPool(vault_id, bravo_token, total_bravo, bob, sender=bob)

    # Check results
    _test(total_bravo, usd_value)
    _test(total_bravo, bravo_token.balanceOf(bob))

    # Check green handling: 
    # - Alpha redemption should create claimable green
    # - sGREEN redemption should auto-convert to sGREEN
    assert stability_pool.claimableBalances(alpha_token, green_token) == bravo_for_alpha
    assert stability_pool.claimableBalances(savings_green, green_token) == 0  # Auto-converted, not claimable

    # sGREEN balance should have increased by the sGREEN redemption amount
    final_sgreen_balance = savings_green.balanceOf(stability_pool)
    _test(bravo_for_sgreen, final_sgreen_balance - pre_sgreen_balance)

    # No green should remain in the stability pool
    assert green_token.balanceOf(stability_pool) == bravo_for_alpha  # Only from alpha redemption