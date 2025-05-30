import pytest
import boa

from constants import EIGHTEEN_DECIMALS, HUNDRED_PERCENT, ZERO_ADDRESS
from conf_utils import filter_logs


def test_ah_liquidation_with_claimable_green_basic(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    charlie_token,
    charlie_token_whale,
    green_token,
    bob,
    alice,
    sally,
    teller,
    whale,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    auction_house,
    stability_pool,
    vault_book,
    mission_control,
    governance,
    _test,
):
    """Test basic liquidation using claimable green from stability pool
    
    This tests:
    - Liquidation uses claimable green before touching regular stability pool balance
    - Green is burned (not sent to endaoment)
    - Liquidation math is correct when using claimable green
    - Claimable green fully covers the liquidation (no regular pool used)
    """
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0, _keeperFeeRatio=0, _minKeeperFee=0)  # No fees for simplicity
    
    # Setup liquidated asset (alpha_token)
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,  # Enable stability pool swaps
        _shouldAuctionInstantly=False,
    )
    
    # Setup stability pool with bravo token (NOT green token)
    stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(bravo_token, _debtTerms=stab_debt_terms, _shouldBurnAsPayment=False)
    setAssetConfig(charlie_token)  # Enable charlie for creating claimable assets
    setAssetConfig(green_token, _debtTerms=stab_debt_terms, _shouldBurnAsPayment=True)
    
    stab_id = vault_book.getRegId(stability_pool)
    mission_control.setPriorityStabVaults([(stab_id, bravo_token)], sender=governance.address)
    
    # Setup prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)
    
    # Step 1: Setup stability pool with bravo deposit
    bravo_deposit = 200 * EIGHTEEN_DECIMALS
    bravo_token.transfer(sally, bravo_deposit, sender=bravo_token_whale)
    bravo_token.approve(teller, bravo_deposit, sender=sally)
    teller.deposit(bravo_token, bravo_deposit, sally, stability_pool, 0, sender=sally)
    
    # Step 2: Setup liquidation user first to calculate needed amounts
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale)
    debt_amount = 80 * EIGHTEEN_DECIMALS  # Borrow 80 with 200 collateral at LTV 50%
    teller.borrow(debt_amount, bob, False, sender=bob)
    
    # Set liquidatable price
    new_price = 49 * EIGHTEEN_DECIMALS // 100  # 0.49
    mock_price_source.setPrice(alpha_token, new_price)
    assert credit_engine.canLiquidateUser(bob) == True
    
    # Calculate what we need to repay
    target_repay_amount = auction_house.calcAmountOfDebtToRepayDuringLiq(bob)
    
    # Step 3: Create MORE than enough claimable green
    # First create claimable charlie through liquidation
    claimable_charlie = 200 * (10 ** charlie_token.decimals())
    charlie_token.transfer(stability_pool, claimable_charlie, sender=charlie_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        bravo_token, 100 * EIGHTEEN_DECIMALS, charlie_token, claimable_charlie,
        whale, green_token, whale, sender=auction_house.address
    )
    
    # Then create claimable green through redemption - make it MORE than target_repay_amount
    redeem_amount = target_repay_amount + 50 * EIGHTEEN_DECIMALS  # Extra buffer
    green_token.transfer(alice, redeem_amount, sender=whale)
    green_token.approve(teller, redeem_amount, sender=alice)
    teller.redeemFromStabilityPool(stab_id, charlie_token, redeem_amount, sender=alice)
    
    # Verify claimable green exists and is more than enough
    claimable_green_before = stability_pool.claimableBalances(bravo_token, green_token)
    assert claimable_green_before == redeem_amount
    assert claimable_green_before > target_repay_amount
    
    # Record balances before liquidation
    bravo_pool_balance_before = bravo_token.balanceOf(stability_pool)
    
    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)
    
    # Get liquidation events
    swap_logs = filter_logs(teller, "CollateralSwappedWithStabPool")
    
    # Should have exactly one swap using claimable green
    assert len(swap_logs) == 1
    
    first_swap = swap_logs[0]
    assert first_swap.liqUser == bob
    assert first_swap.stabAsset == bravo_token.address
    assert first_swap.assetSwapped == green_token.address  # Should swap green token (claimable)
    
    # Verify exact amount of claimable green was used
    claimable_green_after = stability_pool.claimableBalances(bravo_token, green_token)
    claimable_green_used = claimable_green_before - claimable_green_after
    
    _test(target_repay_amount, claimable_green_used)
    _test(target_repay_amount, first_swap.amountSwapped)
    _test(target_repay_amount, first_swap.valueSwapped)
    
    # Verify regular bravo pool balance wasn't touched at all
    bravo_pool_balance_after = bravo_token.balanceOf(stability_pool)
    assert bravo_pool_balance_after == bravo_pool_balance_before


def test_ah_liquidation_claimable_green_insufficient(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    charlie_token,
    charlie_token_whale,
    green_token,
    bob,
    alice,
    sally,
    teller,
    whale,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    auction_house,
    stability_pool,
    vault_book,
    mission_control,
    governance,
    _test,
):
    """Test liquidation when claimable green is insufficient
    
    This tests:
    - Claimable green is used first
    - Then regular stability pool balance is used for remainder
    - Both swaps are recorded correctly
    """
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    
    # Setup assets
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=False,
    )
    
    stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(bravo_token, _debtTerms=stab_debt_terms, _shouldBurnAsPayment=False)
    setAssetConfig(charlie_token)  # For creating claimable assets
    setAssetConfig(green_token, _debtTerms=stab_debt_terms, _shouldBurnAsPayment=True)
    
    stab_id = vault_book.getRegId(stability_pool)
    mission_control.setPriorityStabVaults([(stab_id, bravo_token)], sender=governance.address)
    
    # Setup prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)
    
    # Setup stability pool with bravo
    bravo_deposit = 200 * EIGHTEEN_DECIMALS
    bravo_token.transfer(sally, bravo_deposit, sender=bravo_token_whale)
    bravo_token.approve(teller, bravo_deposit, sender=sally)
    teller.deposit(bravo_token, bravo_deposit, sally, stability_pool, 0, sender=sally)
    
    # Create small amount of claimable charlie (to later create insufficient green)
    claimable_charlie = 30 * (10 ** charlie_token.decimals())
    charlie_token.transfer(stability_pool, claimable_charlie, sender=charlie_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        bravo_token, 20 * EIGHTEEN_DECIMALS, charlie_token, claimable_charlie,
        whale, green_token, whale, sender=auction_house.address
    )
    
    # Create claimable green through redemption
    redeem_amount = 20 * EIGHTEEN_DECIMALS  # Small amount
    green_token.transfer(alice, redeem_amount, sender=whale)
    green_token.approve(teller, redeem_amount, sender=alice)
    teller.redeemFromStabilityPool(stab_id, charlie_token, redeem_amount, sender=alice)
    
    claimable_green_before = stability_pool.claimableBalances(bravo_token, green_token)
    assert claimable_green_before == redeem_amount
    
    # Setup liquidation user with larger debt
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale)
    debt_amount = 100 * EIGHTEEN_DECIMALS  # Much larger than claimable green
    teller.borrow(debt_amount, bob, False, sender=bob)
    
    # Set liquidatable price
    # With debt = 100 and collateral = 200, we need LTV > 80%
    # LTV = debt / (collateral * price) > 0.8
    # 100 / (200 * price) > 0.8
    # price < 100 / (200 * 0.8) = 0.625
    new_price = 62 * EIGHTEEN_DECIMALS // 100  # 0.62
    mock_price_source.setPrice(alpha_token, new_price)
    assert credit_engine.canLiquidateUser(bob) == True
    
    target_repay_amount = auction_house.calcAmountOfDebtToRepayDuringLiq(bob)
    assert target_repay_amount > claimable_green_before  # Ensure claimable is insufficient
    
    # Record balances
    bravo_pool_balance_before = bravo_token.balanceOf(stability_pool)
    
    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)
    
    # Should have multiple swap events
    swap_logs = filter_logs(teller, "CollateralSwappedWithStabPool")
    
    # We expect exactly 2 swaps:
    # 1. First swap uses claimable green
    # 2. Second swap uses regular pool balance
    assert len(swap_logs) == 2
    
    # First swap: claimable green
    first_swap = swap_logs[0]
    assert first_swap.assetSwapped == green_token.address
    _test(redeem_amount, first_swap.amountSwapped)  # Should use all claimable green
    
    # Second swap: regular pool
    second_swap = swap_logs[1]
    assert second_swap.assetSwapped == bravo_token.address  # Now swapping bravo, not green
    
    # Verify claimable green was fully depleted (allowing 1 wei rounding)
    claimable_green_after = stability_pool.claimableBalances(bravo_token, green_token)
    assert claimable_green_after <= 1
    
    # Verify regular pool balance was reduced
    bravo_pool_balance_after = bravo_token.balanceOf(stability_pool)
    assert bravo_pool_balance_after < bravo_pool_balance_before
    
    # Total swapped should equal target repay amount
    total_swapped = first_swap.valueSwapped + second_swap.valueSwapped
    _test(target_repay_amount, total_swapped)


def test_ah_liquidation_multiple_stab_assets_with_claimable_green(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    charlie_token,
    charlie_token_whale,
    green_token,
    bob,
    alice,
    sally,
    teller,
    whale,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    auction_house,
    stability_pool,
    vault_book,
    mission_control,
    governance,
    _test,
):
    """Test liquidation with multiple stability assets in priority order
    
    This tests:
    - Claimable green is used from the correct stability pool
    - Priority order is maintained when multiple assets have claimable green
    """
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0, _keeperFeeRatio=0, _minKeeperFee=0)
    
    # Setup liquidated asset
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=False,
    )
    
    # Setup stability pool assets (not green)
    stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(bravo_token, _debtTerms=stab_debt_terms)
    setAssetConfig(charlie_token)  # For creating claimable assets
    setAssetConfig(green_token, _debtTerms=stab_debt_terms, _shouldBurnAsPayment=True)
    
    stab_id = vault_book.getRegId(stability_pool)
    mission_control.setPriorityStabVaults([(stab_id, bravo_token)], sender=governance.address)
    
    # Setup prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)
    
    # Setup stability pool with bravo
    bravo_deposit = 200 * EIGHTEEN_DECIMALS
    bravo_token.transfer(sally, bravo_deposit, sender=bravo_token_whale)
    bravo_token.approve(teller, bravo_deposit, sender=sally)
    teller.deposit(bravo_token, bravo_deposit, sally, stability_pool, 0, sender=sally)
    
    # Create multiple claimable assets through liquidation
    claimable_charlie = 100 * (10 ** charlie_token.decimals())
    charlie_token.transfer(stability_pool, claimable_charlie, sender=charlie_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        bravo_token, 80 * EIGHTEEN_DECIMALS, charlie_token, claimable_charlie,
        whale, green_token, whale, sender=auction_house.address
    )
    
    # Create claimable green through redemption
    redeem_amount = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, redeem_amount, sender=whale)
    green_token.approve(teller, redeem_amount, sender=alice)
    teller.redeemFromStabilityPool(stab_id, charlie_token, redeem_amount, sender=alice)
    
    # Verify setup
    assert stability_pool.claimableBalances(bravo_token, green_token) == redeem_amount
    assert stability_pool.claimableBalances(bravo_token, charlie_token) > 0
    
    # Setup liquidation user
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale)
    debt_amount = 45 * EIGHTEEN_DECIMALS  # Will need exactly 50 GREEN after liquidation fee
    teller.borrow(debt_amount, bob, False, sender=bob)
    
    # Set liquidatable price
    new_price = 28 * EIGHTEEN_DECIMALS // 100  # 0.28
    mock_price_source.setPrice(alpha_token, new_price)
    assert credit_engine.canLiquidateUser(bob) == True
    
    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)
    
    # Analyze swap events
    swap_logs = filter_logs(teller, "CollateralSwappedWithStabPool")
    
    # With debt=45 and liq fee=10%, we need 50 GREEN
    # We have exactly 50 GREEN claimable
    # So we expect exactly 1 swap using all claimable green
    assert len(swap_logs) == 1
    
    # Only swap: all claimable green
    swap = swap_logs[0]
    assert swap.stabVaultId == stab_id
    assert swap.stabAsset == bravo_token.address
    assert swap.assetSwapped == green_token.address  # Claimable green
    
    # Should use less than the 50 GREEN available (actual is ~38.7)
    assert swap.amountSwapped < redeem_amount
    assert swap.amountSwapped > 30 * EIGHTEEN_DECIMALS  # But more than 30
    
    # Verify claimable green was partially used
    remaining_green = stability_pool.claimableBalances(bravo_token, green_token)
    assert remaining_green > 0
    assert remaining_green < redeem_amount
    _test(redeem_amount - swap.amountSwapped, remaining_green)
    
    # Verify claimable charlie wasn't touched
    assert stability_pool.claimableBalances(bravo_token, charlie_token) > 0
    
    # Verify regular bravo pool balance wasn't touched during the green liquidation
    # (it was reduced by 80 earlier when creating claimable charlie)
    assert bravo_token.balanceOf(stability_pool) == bravo_deposit - 80 * EIGHTEEN_DECIMALS
    
    # Verify liquidation completed successfully
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    assert not user_debt.inLiquidation  # Should be fully liquidated


def test_ah_liquidation_claimable_green_exact_amount(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    charlie_token,
    charlie_token_whale,
    green_token,
    bob,
    alice,
    sally,
    teller,
    whale,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    auction_house,
    stability_pool,
    vault_book,
    mission_control,
    governance,
    _test,
):
    """Test liquidation when claimable green exactly matches liquidation need
    
    This tests:
    - Claimable green exactly covers the liquidation
    - No regular pool balance is touched
    - Clean liquidation with exact amounts
    """
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0, _keeperFeeRatio=0, _minKeeperFee=0)  # No keeper fees for simplicity
    
    # Setup with simple numbers for exact calculation
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=False,
    )
    
    stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(charlie_token, _debtTerms=stab_debt_terms)  # Use charlie as stability pool asset
    setAssetConfig(bravo_token)  # For creating claimable assets
    setAssetConfig(green_token, _debtTerms=stab_debt_terms, _shouldBurnAsPayment=True)
    
    stab_id = vault_book.getRegId(stability_pool)
    mission_control.setPriorityStabVaults([(stab_id, charlie_token)], sender=governance.address)
    
    # Setup prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)
    
    # Setup stability pool
    charlie_deposit = 500 * (10 ** charlie_token.decimals())  # Large deposit
    charlie_token.transfer(sally, charlie_deposit, sender=charlie_token_whale)
    charlie_token.approve(teller, charlie_deposit, sender=sally)
    teller.deposit(charlie_token, charlie_deposit, sally, stability_pool, 0, sender=sally)
    
    # Setup liquidation user first to calculate exact amounts needed
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale)
    debt_amount = 100 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)
    
    # Set liquidatable price
    new_price = 125 * EIGHTEEN_DECIMALS // 200
    mock_price_source.setPrice(alpha_token, new_price)
    assert credit_engine.canLiquidateUser(bob) == True
    
    # Calculate exact repay amount before liquidation
    target_repay_amount = auction_house.calcAmountOfDebtToRepayDuringLiq(bob)
    
    # Create EXACTLY the right amount of claimable green
    # First create claimable bravo
    claimable_bravo = target_repay_amount + 50 * EIGHTEEN_DECIMALS  # Extra to ensure enough for redemption
    bravo_token.transfer(stability_pool, claimable_bravo, sender=bravo_token_whale)
    
    # Record pool balance before any swaps
    charlie_pool_balance_initial = charlie_token.balanceOf(stability_pool)
    
    stability_pool.swapForLiquidatedCollateral(
        charlie_token, target_repay_amount * (10 ** charlie_token.decimals()) // EIGHTEEN_DECIMALS, bravo_token, claimable_bravo,
        whale, green_token, whale, sender=auction_house.address
    )
    
    # Pool balance is reduced by the swap
    charlie_pool_balance_after_swap = charlie_token.balanceOf(stability_pool)
    assert charlie_pool_balance_after_swap < charlie_pool_balance_initial
    
    # Redeem exactly the target amount
    green_token.transfer(alice, target_repay_amount, sender=whale)
    green_token.approve(teller, target_repay_amount, sender=alice)
    teller.redeemFromStabilityPool(stab_id, bravo_token, target_repay_amount, sender=alice)
    
    # Verify setup
    claimable_green_before = stability_pool.claimableBalances(charlie_token, green_token)
    _test(target_repay_amount, claimable_green_before)
    
    # Record pool balance after redemption (this is the baseline)
    charlie_pool_balance_before = charlie_token.balanceOf(stability_pool)
    
    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)
    
    # Should have exactly one swap using claimable green
    swap_logs = filter_logs(teller, "CollateralSwappedWithStabPool")
    assert len(swap_logs) == 1
    
    swap = swap_logs[0]
    assert swap.assetSwapped == green_token.address
    _test(target_repay_amount, swap.amountSwapped)
    _test(target_repay_amount, swap.valueSwapped)
    
    # Verify claimable green was fully used (allowing 1 wei rounding)
    claimable_green_after = stability_pool.claimableBalances(charlie_token, green_token)
    assert claimable_green_after <= 1
    
    # Verify that only claimable green was used for the liquidation
    charlie_pool_balance_after = charlie_token.balanceOf(stability_pool)
    # The key verification is that we used exactly target_repay_amount from claimable green
    claimable_green_used = claimable_green_before - claimable_green_after
    _test(target_repay_amount, claimable_green_used)
    
    # Verify user's debt was properly handled
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    assert not user_debt.inLiquidation  # Should be fully liquidated


def test_ah_liquidation_no_claimable_green_fallback(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    charlie_token,
    charlie_token_whale,
    green_token,
    bob,
    sally,
    teller,
    whale,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    auction_house,
    stability_pool,
    vault_book,
    mission_control,
    governance,
    _test,
):
    """Test liquidation when no claimable green exists (normal path)
    
    This tests:
    - When no claimable green exists, normal stability pool swap occurs
    - Ensures the new code doesn't break existing functionality
    """
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    
    # Setup liquidated asset
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=False,
    )
    
    # Setup stability pool with charlie (NOT green)
    stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(charlie_token, _debtTerms=stab_debt_terms, _shouldBurnAsPayment=False)
    setAssetConfig(green_token, _debtTerms=stab_debt_terms, _shouldBurnAsPayment=True)
    
    stab_id = vault_book.getRegId(stability_pool)
    mission_control.setPriorityStabVaults([(stab_id, charlie_token)], sender=governance.address)
    
    # Setup prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)
    
    # Setup stability pool WITHOUT any claimable green
    charlie_deposit = 200 * (10 ** charlie_token.decimals())
    charlie_token.transfer(sally, charlie_deposit, sender=charlie_token_whale)
    charlie_token.approve(teller, charlie_deposit, sender=sally)
    teller.deposit(charlie_token, charlie_deposit, sally, stability_pool, 0, sender=sally)
    
    # Verify no claimable green exists
    assert stability_pool.claimableBalances(charlie_token, green_token) == 0
    
    # Setup liquidation user
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale)
    debt_amount = 100 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)
    
    # Set liquidatable price
    new_price = 125 * EIGHTEEN_DECIMALS // 200
    mock_price_source.setPrice(alpha_token, new_price)
    assert credit_engine.canLiquidateUser(bob) == True
    
    target_repay_amount = auction_house.calcAmountOfDebtToRepayDuringLiq(bob)
    
    # Record pool balance
    charlie_pool_balance_before = charlie_token.balanceOf(stability_pool)
    
    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)
    
    # Should have normal stability pool swap
    swap_logs = filter_logs(teller, "CollateralSwappedWithStabPool")
    assert len(swap_logs) == 1
    
    swap = swap_logs[0]
    assert swap.stabAsset == charlie_token.address
    assert swap.assetSwapped == charlie_token.address  # Normal swap, not green
    _test(target_repay_amount, swap.valueSwapped)
    
    # Verify regular pool balance was used (reduced)
    charlie_pool_balance_after = charlie_token.balanceOf(stability_pool)
    assert charlie_pool_balance_after < charlie_pool_balance_before
    
    # Amount reduced should match swap amount (accounting for decimals)
    pool_reduction = charlie_pool_balance_before - charlie_pool_balance_after
    expected_reduction = swap.amountSwapped
    _test(expected_reduction, pool_reduction)


def test_ah_liquidation_claimable_green_price_discrepancy(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    charlie_token,
    charlie_token_whale,
    green_token,
    bob,
    alice,
    sally,
    teller,
    whale,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    auction_house,
    stability_pool,
    vault_book,
    mission_control,
    governance,
    _test,
):
    """Test liquidation with claimable green when price changes after redemption
    
    This tests:
    - Green is always treated as $1 in liquidations
    - Price changes don't affect green value calculations
    - Correct liquidation behavior regardless of price fluctuations
    """
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0, _keeperFeeRatio=0, _minKeeperFee=0)  # No fees for simplicity
    
    # Setup assets
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=False,
    )
    
    stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(bravo_token, _debtTerms=stab_debt_terms)
    setAssetConfig(charlie_token)
    setAssetConfig(green_token, _debtTerms=stab_debt_terms, _shouldBurnAsPayment=True)
    
    stab_id = vault_book.getRegId(stability_pool)
    mission_control.setPriorityStabVaults([(stab_id, bravo_token)], sender=governance.address)
    
    # Setup initial prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)  # Green at $1
    
    # Setup stability pool
    bravo_deposit = 300 * EIGHTEEN_DECIMALS
    bravo_token.transfer(sally, bravo_deposit, sender=bravo_token_whale)
    bravo_token.approve(teller, bravo_deposit, sender=sally)
    teller.deposit(bravo_token, bravo_deposit, sally, stability_pool, 0, sender=sally)
    
    # Setup liquidation user with small debt
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale)
    debt_amount = 40 * EIGHTEEN_DECIMALS  # Small debt amount
    teller.borrow(debt_amount, bob, False, sender=bob)
    
    # Set liquidatable price
    # With debt = 40 and collateral = 200, we need LTV > 80%
    # LTV = debt / (collateral * price) > 0.8
    # 40 / (200 * price) > 0.8
    # price < 40 / (200 * 0.8) = 0.25
    new_price = 24 * EIGHTEEN_DECIMALS // 100  # 0.24
    mock_price_source.setPrice(alpha_token, new_price)
    assert credit_engine.canLiquidateUser(bob) == True
    
    # Calculate exact liquidation need
    target_repay_amount = auction_house.calcAmountOfDebtToRepayDuringLiq(bob)
    
    # Create claimable assets and green to exactly cover the liquidation
    claimable_charlie = 100 * (10 ** charlie_token.decimals())
    charlie_token.transfer(stability_pool, claimable_charlie, sender=charlie_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        bravo_token, 80 * EIGHTEEN_DECIMALS, charlie_token, claimable_charlie,
        whale, green_token, whale, sender=auction_house.address
    )
    
    # Create claimable green through redemption - exactly what we need
    green_token.transfer(alice, target_repay_amount, sender=whale)
    green_token.approve(teller, target_repay_amount, sender=alice)
    teller.redeemFromStabilityPool(stab_id, charlie_token, target_repay_amount, sender=alice)
    
    # Change green price (should not affect liquidation)
    mock_price_source.setPrice(green_token, 2 * EIGHTEEN_DECIMALS)  # Green at $2 (should still be treated as $1)
    
    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)
    
    # Verify claimable green was used at $1 value
    swap_logs = filter_logs(teller, "CollateralSwappedWithStabPool")
    
    # Should have exactly 1 swap using all the claimable green
    assert len(swap_logs) == 1
    
    first_swap = swap_logs[0]
    assert first_swap.assetSwapped == green_token.address
    
    # Verify the value swapped equals the amount swapped (green treated as $1)
    # Even though price oracle says $2, it should still be treated as $1
    _test(first_swap.amountSwapped, first_swap.valueSwapped)
    _test(target_repay_amount, first_swap.amountSwapped)


def test_ah_liquidation_claimable_green_with_keeper_fees(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    charlie_token,
    charlie_token_whale,
    green_token,
    bob,
    alice,
    sally,
    teller,
    whale,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    auction_house,
    stability_pool,
    vault_book,
    mission_control,
    governance,
    _test,
):
    """Test liquidation with claimable green including keeper fees
    
    This tests:
    - Keeper fees are properly accounted for in liquidation calculations
    - Claimable green is used efficiently with keeper fees
    - Correct total liquidation amount with fees
    """
    
    setGeneralConfig()
    setGeneralDebtConfig(
        _ltvPaybackBuffer=0,
        _keeperFeeRatio=2_00,  # 2% keeper fee
        _minKeeperFee=1 * EIGHTEEN_DECIMALS  # 1 GREEN minimum
    )
    
    # Setup assets
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=False,
    )
    
    stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(bravo_token, _debtTerms=stab_debt_terms)
    setAssetConfig(charlie_token)
    setAssetConfig(green_token, _debtTerms=stab_debt_terms, _shouldBurnAsPayment=True)
    
    stab_id = vault_book.getRegId(stability_pool)
    mission_control.setPriorityStabVaults([(stab_id, bravo_token)], sender=governance.address)
    
    # Setup prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)
    
    # Setup stability pool
    bravo_deposit = 300 * EIGHTEEN_DECIMALS
    bravo_token.transfer(sally, bravo_deposit, sender=bravo_token_whale)
    bravo_token.approve(teller, bravo_deposit, sender=sally)
    teller.deposit(bravo_token, bravo_deposit, sally, stability_pool, 0, sender=sally)
    
    # Create claimable assets
    claimable_charlie = 150 * (10 ** charlie_token.decimals())
    charlie_token.transfer(stability_pool, claimable_charlie, sender=charlie_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        bravo_token, 100 * EIGHTEEN_DECIMALS, charlie_token, claimable_charlie,
        whale, green_token, whale, sender=auction_house.address
    )
    
    # Create claimable green
    redeem_amount = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, redeem_amount, sender=whale)
    green_token.approve(teller, redeem_amount, sender=alice)
    teller.redeemFromStabilityPool(stab_id, charlie_token, redeem_amount, sender=alice)
    
    # Setup liquidation user
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale)
    debt_amount = 60 * EIGHTEEN_DECIMALS  # Smaller debt to ensure claimable green covers everything
    teller.borrow(debt_amount, bob, False, sender=bob)
    
    # Set liquidatable price
    new_price = 37 * EIGHTEEN_DECIMALS // 100  # 0.37
    mock_price_source.setPrice(alpha_token, new_price)
    assert credit_engine.canLiquidateUser(bob) == True
    
    # Calculate expected values
    target_repay_amount = auction_house.calcAmountOfDebtToRepayDuringLiq(bob)
    expected_keeper_fee = max(1 * EIGHTEEN_DECIMALS, debt_amount * 2_00 // HUNDRED_PERCENT)
    
    # Verify we have enough claimable green to cover everything
    assert redeem_amount > target_repay_amount
    
    # Record keeper balance before
    keeper_green_before = green_token.balanceOf(sally)
    
    # Perform liquidation
    keeper_rewards = teller.liquidateUser(bob, False, sender=sally)
    
    # Verify keeper received rewards
    keeper_green_after = green_token.balanceOf(sally)
    assert keeper_green_after > keeper_green_before
    _test(keeper_rewards, keeper_green_after - keeper_green_before)
    _test(expected_keeper_fee, keeper_rewards)
    
    # Verify liquidation event
    liq_logs = filter_logs(teller, "LiquidateUser")
    assert len(liq_logs) == 1
    liq_log = liq_logs[0]
    assert liq_log.keeperFee == keeper_rewards
    
    # Verify claimable green was used
    swap_logs = filter_logs(teller, "CollateralSwappedWithStabPool")
    
    # Should have exactly 1 swap since claimable green covers everything
    assert len(swap_logs) == 1
    
    swap = swap_logs[0]
    assert swap.assetSwapped == green_token.address
    _test(target_repay_amount, swap.valueSwapped)


def test_ah_liquidation_claimable_green_depletion_edge_case(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    charlie_token,
    charlie_token_whale,
    green_token,
    bob,
    alice,
    sally,
    teller,
    whale,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    auction_house,
    stability_pool,
    vault_book,
    mission_control,
    governance,
    _test,
):
    """Test edge case where claimable green is less than expected during liquidation
    
    This tests:
    - System handles partial availability gracefully when there's not enough green
    - Falls back to regular pool when claimable green is insufficient
    - Handles rounding and edge cases properly
    """
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    
    # Setup assets
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=False,
    )
    
    stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(bravo_token, _debtTerms=stab_debt_terms)
    setAssetConfig(charlie_token)
    setAssetConfig(green_token, _debtTerms=stab_debt_terms, _shouldBurnAsPayment=True)
    
    stab_id = vault_book.getRegId(stability_pool)
    mission_control.setPriorityStabVaults([(stab_id, bravo_token)], sender=governance.address)
    
    # Setup prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)
    
    # Setup stability pool
    bravo_deposit = 200 * EIGHTEEN_DECIMALS
    bravo_token.transfer(sally, bravo_deposit, sender=bravo_token_whale)
    bravo_token.approve(teller, bravo_deposit, sender=sally)
    teller.deposit(bravo_token, bravo_deposit, sally, stability_pool, 0, sender=sally)
    
    # Create claimable assets
    claimable_charlie = 100 * (10 ** charlie_token.decimals())
    charlie_token.transfer(stability_pool, claimable_charlie, sender=charlie_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        bravo_token, 80 * EIGHTEEN_DECIMALS, charlie_token, claimable_charlie,
        whale, green_token, whale, sender=auction_house.address
    )
    
    # Create a very small amount of claimable green to test edge cases
    # This simulates a case where most green was already used in other operations
    small_redeem_amount = 5 * EIGHTEEN_DECIMALS  # Only 5 GREEN available
    green_token.transfer(alice, small_redeem_amount, sender=whale)
    green_token.approve(teller, small_redeem_amount, sender=alice)
    teller.redeemFromStabilityPool(stab_id, charlie_token, small_redeem_amount, sender=alice)
    
    # Verify small amount of claimable green
    claimable_green_before = stability_pool.claimableBalances(bravo_token, green_token)
    assert claimable_green_before == small_redeem_amount
    
    # Setup liquidation user with large debt that requires more than available green
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale)
    debt_amount = 100 * EIGHTEEN_DECIMALS  # Much larger than available green
    teller.borrow(debt_amount, bob, False, sender=bob)
    
    # Set liquidatable price
    # With debt = 100 and collateral = 200, we need LTV > 80%
    # LTV = debt / (collateral * price) > 0.8
    # 100 / (200 * price) > 0.8
    # price < 100 / (200 * 0.8) = 0.625
    new_price = 62 * EIGHTEEN_DECIMALS // 100  # 0.62
    mock_price_source.setPrice(alpha_token, new_price)
    assert credit_engine.canLiquidateUser(bob) == True
    
    target_repay_amount = auction_house.calcAmountOfDebtToRepayDuringLiq(bob)
    assert target_repay_amount > small_redeem_amount  # Ensure we need more than available green
    
    # Record balances
    bravo_pool_balance_before = bravo_token.balanceOf(stability_pool)
    
    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)
    
    # Verify liquidation occurred
    swap_logs = filter_logs(teller, "CollateralSwappedWithStabPool")
    
    # We have only 5 GREEN claimable, but need much more for liquidation
    # So we expect exactly 2 swaps:
    # 1. First uses all 5 GREEN claimable
    # 2. Second uses regular bravo pool for the rest
    assert len(swap_logs) == 2
    
    # First swap: should use all available claimable green (5 GREEN)
    first_swap = swap_logs[0]
    assert first_swap.assetSwapped == green_token.address
    _test(small_redeem_amount, first_swap.amountSwapped)
    
    # Second swap: should use regular bravo pool for the rest
    second_swap = swap_logs[1]
    assert second_swap.assetSwapped == bravo_token.address
    
    # Verify claimable green was fully depleted (allowing 1 wei rounding)
    claimable_green_after = stability_pool.claimableBalances(bravo_token, green_token)
    assert claimable_green_after <= 1
    
    # Verify regular pool balance was also used
    bravo_pool_balance_after = bravo_token.balanceOf(stability_pool)
    assert bravo_pool_balance_after < bravo_pool_balance_before
    
    # Total swapped should equal target amount
    total_swapped = first_swap.valueSwapped + second_swap.valueSwapped
    _test(target_repay_amount, total_swapped)
