import pytest
import boa

from constants import EIGHTEEN_DECIMALS, HUNDRED_PERCENT
from conf_utils import filter_logs


@pytest.fixture(scope="module")
def setupStabPoolLiquidation(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    green_token,
    bob,
    teller,
    whale,
    mock_price_source,
    createDebtTerms,
    stability_pool,
    vault_book,
    control_room,
    governance,
    sally,
):
    def setupStabPoolLiquidation(
        _debt_amount,
        _collateral_amount,
        _liq_threshold,
        _liq_fee,
        _target_ltv,
        _ltv_payback_buffer,
        _collateral_price_drop_ratio, # e.g., 0.625 means price drops to 62.5% of original
    ):
        setGeneralConfig()
        setGeneralDebtConfig(_ltvPaybackBuffer=_ltv_payback_buffer)
        debt_terms = createDebtTerms(_liqThreshold=_liq_threshold, _liqFee=_liq_fee, _ltv=_target_ltv, _borrowRate=0)
        setAssetConfig(
            alpha_token,
            _debtTerms=debt_terms,
            _shouldBurnAsPayment=False, 
            _shouldTransferToEndaoment=False,
            _shouldSwapInStabPools=True, # testing this!
            _shouldAuctionInstantly=False,
        )

        # stab pool config
        stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
        setAssetConfig(green_token, _debtTerms=stab_debt_terms, _shouldBurnAsPayment=True)
        stab_id = vault_book.getRegId(stability_pool)
        control_room.setPriorityStabVaults([(stab_id, green_token)], sender=governance.address)

        # stab pool deposit (ensure enough liquidity)
        mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)
        stab_deposit_amount = _debt_amount * 10  # 10x the debt amount for sufficient liquidity
        green_token.transfer(sally, stab_deposit_amount, sender=whale)
        green_token.approve(teller, stab_deposit_amount, sender=sally)
        teller.deposit(green_token, stab_deposit_amount, sally, stability_pool, 0, sender=sally)

        # liq user setup
        original_price = 1 * EIGHTEEN_DECIMALS
        mock_price_source.setPrice(alpha_token, original_price)
        performDeposit(bob, _collateral_amount, alpha_token, alpha_token_whale)
        teller.borrow(_debt_amount, bob, False, sender=bob)

        # set liquidatable price
        new_price = int(original_price * _collateral_price_drop_ratio)
        mock_price_source.setPrice(alpha_token, new_price)
        
        return stab_id, stab_deposit_amount, new_price

    yield setupStabPoolLiquidation


def verifyStabPoolLiqResults(
    _user_debt,
    _bt,
    _orig_debt_amount,
    _orig_collateral_val,
    _log,
    _exp_liq_fees,
    _target_ltv,
    _test,
):
    """Helper function to verify liquidation results"""
    
    # Calculate expected debt based on actual liquidation mechanics
    actual_repay_amount = _log.stabValueSwapped
    actual_collateral_taken = _log.collateralValueOut
    liq_fees_paid = actual_collateral_taken - actual_repay_amount
    unpaid_liq_fees = max(0, _exp_liq_fees - liq_fees_paid)
    expected_final_debt = _orig_debt_amount - actual_repay_amount + unpaid_liq_fees
    
    # Verify debt calculation
    _test(expected_final_debt, _user_debt.amount)
    
    # Verify collateral calculation
    expected_final_collateral = _orig_collateral_val - actual_collateral_taken
    _test(expected_final_collateral, _bt.collateralVal)
    
    # Verify target LTV is achieved (within tight tolerance)
    actual_ltv = _user_debt.amount * HUNDRED_PERCENT // _bt.collateralVal
    ltv_tolerance = 50 # 0.5% tolerance in basis points (50 bp = 0.5%)
    assert abs(actual_ltv - _target_ltv) <= ltv_tolerance, f"LTV {actual_ltv} not close to target {_target_ltv}"
    
    # Verify user is no longer in liquidation
    assert not _user_debt.inLiquidation


###############
# Liquidation #
###############


def test_ah_liquidation_threshold(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    mock_price_source,
    createDebtTerms,
    credit_engine,
):
    setGeneralConfig()
    setGeneralDebtConfig()
    debt_terms = createDebtTerms(_liqThreshold=80_00)
    setAssetConfig(alpha_token, _debtTerms=debt_terms)

    # set mock price
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)

    # deposit
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # borrow
    borrow_amount = 100 * EIGHTEEN_DECIMALS
    amount = teller.borrow(borrow_amount, bob, False, sender=bob)
    assert amount == borrow_amount

    assert credit_engine.getLiquidationThreshold(bob) == 125 * EIGHTEEN_DECIMALS

    # set new price (can liquidate)
    new_price = 125 * EIGHTEEN_DECIMALS // 200
    mock_price_source.setPrice(alpha_token, new_price)
    assert credit_engine.canLiquidateUser(bob) == True


# burn stab asset


def test_ah_liquidation_burn_asset(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    green_token,
    whale,
    bob,
    teller,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    auction_house,
    sally,
):
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0) # no payback buffer
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _borrowRate=0)
    setAssetConfig(
        green_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=True, # testing this!
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=False,
    )

    # setup
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, green_token, whale)
    orig_debt_amount = 100 * EIGHTEEN_DECIMALS
    teller.borrow(orig_debt_amount, bob, False, sender=bob)

    # set liquidatable price
    new_price = 125 * EIGHTEEN_DECIMALS // 200
    mock_price_source.setPrice(green_token, new_price)
    assert credit_engine.canLiquidateUser(bob) == True

    target_repay_amount = auction_house.calcAmountOfDebtToRepayDuringLiq(bob)
    _, orig_bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)

    # liquidate user
    teller.liquidateUser(bob, False, sender=sally)

    # test event
    log = filter_logs(teller, "StabAssetBurntAsRepayment")[0]
    assert log.liqUser == bob
    assert log.vaultId != 0
    assert log.liqStabAsset == green_token.address
    assert log.amountBurned == target_repay_amount * EIGHTEEN_DECIMALS // new_price
    assert log.usdValue == target_repay_amount
    assert log.isDepleted == False

    # get latest debt and terms
    expected_liq_fees = 10 * EIGHTEEN_DECIMALS
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)

    # Note: User may still be in liquidation if debt health wasn't fully restored
    # This is expected behavior with the new precise calculation
    assert user_debt.amount == orig_debt_amount - target_repay_amount + expected_liq_fees
    assert bt.collateralVal == orig_bt.collateralVal - target_repay_amount


# endaoment transfer


def test_ah_liquidation_endaoment_transfer(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    auction_house,
    sally,
    endaoment,
):
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0) # no payback buffer
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False, 
        _shouldTransferToEndaoment=True, # testing this!
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=False,
    )

    # setup
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    orig_debt_amount = 100 * EIGHTEEN_DECIMALS
    teller.borrow(orig_debt_amount, bob, False, sender=bob)

    # set liquidatable price
    new_price = 125 * EIGHTEEN_DECIMALS // 200
    mock_price_source.setPrice(alpha_token, new_price)
    assert credit_engine.canLiquidateUser(bob) == True

    target_repay_amount = auction_house.calcAmountOfDebtToRepayDuringLiq(bob)
    _, orig_bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)

    # liquidate user
    teller.liquidateUser(bob, False, sender=sally)

    # test event
    log = filter_logs(teller, "CollateralSentToEndaoment")[0]
    assert log.liqUser == bob
    assert log.vaultId != 0
    assert log.liqAsset == alpha_token.address
    assert log.amountSent == target_repay_amount * EIGHTEEN_DECIMALS // new_price
    assert log.usdValue == target_repay_amount
    assert log.isDepleted == False

    assert alpha_token.balanceOf(endaoment) == log.amountSent # !!

    # get latest debt and terms
    expected_liq_fees = 10 * EIGHTEEN_DECIMALS
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)

    # Note: User may still be in liquidation if debt health wasn't fully restored
    # This is expected behavior with the new precise calculation
    assert user_debt.amount == orig_debt_amount - target_repay_amount + expected_liq_fees
    assert bt.collateralVal == orig_bt.collateralVal - target_repay_amount


##################
# Stability Pool #
##################


def test_ah_liquidation_stab_pool_swap(
    setupStabPoolLiquidation,
    alpha_token,
    green_token,
    bob,
    teller,
    credit_engine,
    auction_house,
    sally,
    stability_pool,
    endaoment,
    _test,
):
    """Test stability pool liquidation swap - using setupStabPoolLiquidation fixture"""
    
    # Test parameters
    debt_amount = 100 * EIGHTEEN_DECIMALS
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    liq_threshold = 80_00
    liq_fee = 10_00
    ltv = 50_00
    ltv_payback_buffer = 0
    collateral_price_drop = 0.625
    
    # Setup test using fixture
    stab_id, stab_deposit_amount, new_price = setupStabPoolLiquidation(
        debt_amount, collateral_amount, liq_threshold, liq_fee, ltv,
        ltv_payback_buffer, collateral_price_drop
    )

    # verify user can be liquidated
    assert credit_engine.canLiquidateUser(bob) == True
    _, orig_bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)

    # expected values
    target_repay_amount = auction_house.calcAmountOfDebtToRepayDuringLiq(bob)
    target_collateral_val = target_repay_amount * HUNDRED_PERCENT // (HUNDRED_PERCENT - liq_fee)
    exp_liq_fees = debt_amount * liq_fee // HUNDRED_PERCENT

    # liquidate user
    teller.liquidateUser(bob, False, sender=sally)

    # test event
    log = filter_logs(teller, "CollateralSwappedWithStabPool")[0]
    assert log.liqUser == bob
    assert log.liqVaultId != stab_id
    assert log.liqAsset == alpha_token.address
    assert log.collateralAmountOut == target_collateral_val * EIGHTEEN_DECIMALS // new_price
    assert log.collateralValueOut == target_collateral_val
    assert log.stabVaultId == stab_id
    assert log.stabAsset == green_token.address  # fixture uses green_token for stab pool
    _test(target_repay_amount, log.stabAmountSwapped)
    _test(target_repay_amount, log.stabValueSwapped)

    # funds
    assert green_token.balanceOf(stability_pool) == stab_deposit_amount - log.stabAmountSwapped
    assert green_token.balanceOf(endaoment) == 0 # green burned
    assert alpha_token.balanceOf(stability_pool) == log.collateralAmountOut

    # get latest debt and terms
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)

    # Use the helper function for verification
    verifyStabPoolLiqResults(
        user_debt, bt, debt_amount, orig_bt.collateralVal,
        log, exp_liq_fees, ltv, _test
    )


@pytest.mark.parametrize("debt_amount,collateral_amount,liq_threshold,liq_fee,ltv,ltv_payback_buffer,collateral_price_drop", [
    # Test case 1: Standard case (50% LTV, 10% liq fee, 80% liq threshold)
    (100 * EIGHTEEN_DECIMALS, 200 * EIGHTEEN_DECIMALS, 80_00, 10_00, 50_00, 0, 0.625),
    
    # Test case 2: Higher LTV target (70% LTV)
    (100 * EIGHTEEN_DECIMALS, 200 * EIGHTEEN_DECIMALS, 80_00, 10_00, 70_00, 0, 0.625),
    
    # Test case 3: Lower liquidation fee (5%)
    (100 * EIGHTEEN_DECIMALS, 200 * EIGHTEEN_DECIMALS, 80_00, 5_00, 50_00, 0, 0.625),
    
    # Test case 4: Larger amounts
    (1000 * EIGHTEEN_DECIMALS, 2000 * EIGHTEEN_DECIMALS, 80_00, 10_00, 50_00, 0, 0.625),
    
    # Test case 5: With LTV payback buffer (5%)
    (100 * EIGHTEEN_DECIMALS, 200 * EIGHTEEN_DECIMALS, 80_00, 10_00, 50_00, 5_00, 0.625),
    
    # Test case 6: Conservative case - higher LTV target (60%)
    (100 * EIGHTEEN_DECIMALS, 200 * EIGHTEEN_DECIMALS, 80_00, 10_00, 60_00, 0, 0.625),
])
def test_ah_liquidation_stab_pool_various_scenarios(
    setupStabPoolLiquidation,
    green_token,
    bob,
    teller,
    credit_engine,
    auction_house,
    sally,
    _test,
    # params
    debt_amount,
    collateral_amount,
    liq_threshold,
    liq_fee,
    ltv,
    ltv_payback_buffer,
    collateral_price_drop,
):
    """Test various liquidation scenarios with different parameters"""
    
    # Setup test
    stab_id, stab_deposit_amount, new_price = setupStabPoolLiquidation(debt_amount, collateral_amount, liq_threshold, liq_fee, ltv, ltv_payback_buffer, collateral_price_drop)
    
    # Verify user can be liquidated
    assert credit_engine.canLiquidateUser(bob) == True
    _, orig_bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)

    # pre liq values
    target_repay_amount = auction_house.calcAmountOfDebtToRepayDuringLiq(bob)
    effective_target_ltv = ltv * (HUNDRED_PERCENT - ltv_payback_buffer) // HUNDRED_PERCENT
    exp_liq_fees = debt_amount * liq_fee // HUNDRED_PERCENT

    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)
    
    log = filter_logs(teller, "CollateralSwappedWithStabPool")[0]
    assert log.liqUser == bob
    assert log.stabVaultId == stab_id
    assert log.stabAsset == green_token.address
    _test(target_repay_amount, log.stabValueSwapped)

    # Get post-liquidation state
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    
    # Verify liquidation results
    verifyStabPoolLiqResults(
        user_debt, bt, debt_amount, orig_bt.collateralVal,
        log, exp_liq_fees, effective_target_ltv, _test
    )


def test_ah_liquidation_stab_pool_low_liquidation_fee(
    setupStabPoolLiquidation,
    bob,
    teller,
    credit_engine,
    auction_house,
    sally,
    _test,
):
    """Test scenario with very low liquidation fee"""
    
    debt_amount = 100 * EIGHTEEN_DECIMALS
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    liq_threshold = 80_00
    liq_fee = 1_00  # Very low liquidation fee (1%)
    target_ltv = 50_00
    
    # Setup test
    stab_id, stab_deposit_amount, new_price = setupStabPoolLiquidation(debt_amount, collateral_amount, liq_threshold, liq_fee, target_ltv, 0, 0.625)
    
    assert credit_engine.canLiquidateUser(bob) == True
    
    # Get pre-liquidation state
    target_repay_amount = auction_house.calcAmountOfDebtToRepayDuringLiq(bob)
    _, orig_bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)

    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)
    
    # Get liquidation event and verify results
    log = filter_logs(teller, "CollateralSwappedWithStabPool")[0]
    _test(target_repay_amount, log.stabValueSwapped)

    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    exp_liq_fees = debt_amount * liq_fee // HUNDRED_PERCENT
    
    verifyStabPoolLiqResults(
        user_debt, bt, debt_amount, orig_bt.collateralVal,
        log, exp_liq_fees, target_ltv, _test
    )


def test_ah_liquidation_stab_pool_with_payback_buffer(
    setupStabPoolLiquidation,
    bob,
    teller,
    credit_engine,
    auction_house,
    sally,
    _test,
):
    """Test scenario with LTV payback buffer"""
    
    debt_amount = 100 * EIGHTEEN_DECIMALS
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    liq_threshold = 80_00
    liq_fee = 10_00
    target_ltv = 50_00
    ltv_payback_buffer = 10_00  # 10% buffer
    
    # Setup test
    stab_id, stab_deposit_amount, new_price = setupStabPoolLiquidation(debt_amount, collateral_amount, liq_threshold, liq_fee, target_ltv, ltv_payback_buffer, 0.625)
    
    assert credit_engine.canLiquidateUser(bob) == True
    
    # Get pre-liquidation state
    target_repay_amount = auction_house.calcAmountOfDebtToRepayDuringLiq(bob)
    _, orig_bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    effective_target_ltv = target_ltv * (HUNDRED_PERCENT - ltv_payback_buffer) // HUNDRED_PERCENT
    
    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)
    
    # Get liquidation event and verify results
    log = filter_logs(teller, "CollateralSwappedWithStabPool")[0]
    _test(target_repay_amount, log.stabValueSwapped)

    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    exp_liq_fees = debt_amount * liq_fee // HUNDRED_PERCENT
    
    verifyStabPoolLiqResults(
        user_debt, bt, debt_amount, orig_bt.collateralVal,
        log, exp_liq_fees, effective_target_ltv, _test
    )


def test_ah_liquidation_multiple_stab_assets_same_pool(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    bob,
    teller,
    whale,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    auction_house,
    sally,
    alice,
    stability_pool,
    vault_book,
    control_room,
    governance,
    endaoment,
    _test,
):
    """Test liquidation with multiple stability assets in same pool - tests priority ordering"""
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    
    # Setup liquidated asset (alpha_token)
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False, 
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=False,
    )

    # Setup multiple stability pool assets
    stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(green_token, _debtTerms=stab_debt_terms)
    setAssetConfig(bravo_token, _debtTerms=stab_debt_terms)

    # Setup multiple stability assets with priority order (same pool, different assets)
    stab_pool_id = vault_book.getRegId(stability_pool)
    
    # Set priority: green_token first, then bravo_token
    control_room.setPriorityStabVaults([
        (stab_pool_id, green_token),      # Priority 1 - will be exhausted
        (stab_pool_id, bravo_token),      # Priority 2 - will handle remainder
    ], sender=governance.address)

    # Setup prices
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Deposit into stability pool with different assets and amounts
    # Green: Small amount - will be exhausted first
    green_deposit = 30 * EIGHTEEN_DECIMALS
    green_token.transfer(sally, green_deposit, sender=whale)
    green_token.approve(teller, green_deposit, sender=sally)
    teller.deposit(green_token, green_deposit, sally, stability_pool, 0, sender=sally)

    # Bravo: Larger amount - will handle remaining liquidation
    bravo_deposit = 100 * EIGHTEEN_DECIMALS
    bravo_token.transfer(alice, bravo_deposit, sender=bravo_token_whale)
    bravo_token.approve(teller, bravo_deposit, sender=alice)
    teller.deposit(bravo_token, bravo_deposit, alice, stability_pool, 0, sender=alice)

    # Setup liquidation user
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    debt_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale)
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Set liquidatable price
    new_price = 125 * EIGHTEEN_DECIMALS // 200  # 0.625
    mock_price_source.setPrice(alpha_token, new_price)
    assert credit_engine.canLiquidateUser(bob) == True

    # Get pre-liquidation state
    target_repay_amount = auction_house.calcAmountOfDebtToRepayDuringLiq(bob)
    
    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)

    # Should have multiple CollateralSwappedWithStabPool events
    logs = filter_logs(teller, "CollateralSwappedWithStabPool")
    assert len(logs) == 2
    
    # Verify the first swap used green_token (highest priority)
    first_log = logs[0]
    assert first_log.stabAsset == green_token.address
    assert first_log.stabVaultId == stab_pool_id
    
    # First swap should consume ALL green tokens since green_deposit < target_repay_amount
    assert green_deposit < target_repay_amount
    _test(green_deposit, first_log.stabValueSwapped)
    
    # Verify green tokens were burned (not sent to endaoment)
    assert green_token.balanceOf(endaoment) == 0
    assert green_token.balanceOf(stability_pool) == green_deposit - first_log.stabAmountSwapped

    # Since target repay amount > green pool liquidity, we should definitely have a second swap
    remaining_to_repay = target_repay_amount - green_deposit
    assert remaining_to_repay > 0
    
    second_log = logs[1]
    assert second_log.stabAsset == bravo_token.address
    assert second_log.stabVaultId == stab_pool_id
    
    # Verify bravo tokens went to endaoment (non-green asset)
    assert bravo_token.balanceOf(endaoment) == second_log.stabAmountSwapped
    assert bravo_token.balanceOf(stability_pool) == bravo_deposit - second_log.stabAmountSwapped
    
    # Verify the second swap covers the remaining amount
    _test(remaining_to_repay, second_log.stabValueSwapped)
    
    # Verify total liquidation results
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    
    # Calculate total swapped value
    total_swapped = sum(log.stabValueSwapped for log in logs)
    total_collateral_taken = sum(log.collateralValueOut for log in logs)
    
    # Verify liquidation math
    exp_liq_fees = debt_amount * 10_00 // HUNDRED_PERCENT
    liq_fees_paid = total_collateral_taken - total_swapped
    unpaid_liq_fees = max(0, exp_liq_fees - liq_fees_paid)
    expected_final_debt = debt_amount - total_swapped + unpaid_liq_fees
    
    _test(expected_final_debt, user_debt.amount)
    
    # Verify collateral was properly transferred to stability pool
    expected_total_collateral = sum(log.collateralAmountOut for log in logs)
    assert alpha_token.balanceOf(stability_pool) == expected_total_collateral


def test_ah_liquidation_insufficient_stab_pool_liquidity(
    setupStabPoolLiquidation,
    green_token,
    bob,
    teller,
    credit_engine,
    auction_house,
    sally,
    stability_pool,
    _test,
):
    """Test liquidation when stability pool has insufficient liquidity"""
    
    debt_amount = 100 * EIGHTEEN_DECIMALS
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    liq_threshold = 80_00
    liq_fee = 10_00
    ltv = 50_00
    
    # Setup with very limited stability pool liquidity (only 20% of what's needed)
    stab_id, _, new_price = setupStabPoolLiquidation(
        debt_amount, collateral_amount, liq_threshold, liq_fee, ltv, 0, 0.625
    )

    # Reduce stability pool liquidity to create insufficient scenario
    target_repay_amount = auction_house.calcAmountOfDebtToRepayDuringLiq(bob)
    limited_liquidity = target_repay_amount // 5  # Only 20% of needed amount
    
    # Withdraw excess from stability pool to simulate insufficient liquidity
    current_balance = green_token.balanceOf(stability_pool)
    excess_to_remove = current_balance - limited_liquidity
    
    # Transfer excess tokens out of the pool to create insufficient liquidity scenario
    green_token.transfer(sally, excess_to_remove, sender=stability_pool.address)
    
    # Verify we now have limited liquidity
    remaining_balance = green_token.balanceOf(stability_pool)
    assert remaining_balance == limited_liquidity
    
    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)
    
    # Should have exactly one stability pool swap event (limited by available liquidity)
    logs = filter_logs(teller, "CollateralSwappedWithStabPool")
    assert len(logs) == 1
    log = logs[0]
    
    # Verify swap was limited by available liquidity (should consume all remaining tokens)
    _test(remaining_balance, log.stabValueSwapped)
       
    # Since insufficient liquidity, swap should be less than target repay amount
    assert log.stabValueSwapped < target_repay_amount
    
    # Verify final state - user should still be in liquidation
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    
    # User should still be in liquidation since pools couldn't cover full amount
    assert user_debt.inLiquidation
    
    # Verify the partial liquidation math
    exp_liq_fees = debt_amount * liq_fee // HUNDRED_PERCENT
    actual_repay = log.stabValueSwapped
    actual_collateral_taken = log.collateralValueOut
    liq_fees_paid = actual_collateral_taken - actual_repay
    unpaid_liq_fees = max(0, exp_liq_fees - liq_fees_paid)
    expected_final_debt = debt_amount - actual_repay + unpaid_liq_fees
    
    _test(expected_final_debt, user_debt.amount)


def test_ah_liquidation_multiple_collateral_assets(
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
    teller,
    whale,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    sally,
    stability_pool,
    vault_book,
    control_room,
    governance,
    _test,
):
    """Test liquidation of user with multiple collateral assets"""
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    
    # Setup multiple collateral assets with different liquidation configs
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    
    # Alpha: Stability pool swaps
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=False,
    )
    
    # Bravo: Endaoment transfer
    setAssetConfig(
        bravo_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=False,
    )
    
    # Charlie: Auctions
    setAssetConfig(
        charlie_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=True,
    )

    # Setup stability pool for alpha_token liquidation
    stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(green_token, _debtTerms=stab_debt_terms)
    stab_id = vault_book.getRegId(stability_pool)
    control_room.setPriorityStabVaults([(stab_id, green_token)], sender=governance.address)

    # Setup prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)

    # Setup stability pool
    stab_deposit = 500 * EIGHTEEN_DECIMALS
    green_token.transfer(sally, stab_deposit, sender=whale)
    green_token.approve(teller, stab_deposit, sender=sally)
    teller.deposit(green_token, stab_deposit, sally, stability_pool, 0, sender=sally)

    # Setup user with multiple collateral assets
    alpha_amount = 100 * EIGHTEEN_DECIMALS
    bravo_amount = 150 * EIGHTEEN_DECIMALS
    charlie_amount = 200 * 10**6  # Charlie token has 6 decimals, not 18
    
    performDeposit(bob, alpha_amount, alpha_token, alpha_token_whale)
    performDeposit(bob, bravo_amount, bravo_token, bravo_token_whale)
    performDeposit(bob, charlie_amount, charlie_token, charlie_token_whale)
    
    # Borrow against total collateral
    debt_amount = 200 * EIGHTEEN_DECIMALS  # Borrow $200 against $450 collateral
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Set liquidatable prices (drop all assets to trigger liquidation)
    # Liquidation threshold: $200 * 100 / 80 = $250
    # Need collateral value <= $250, so drop to $0.55 each: $450 * 0.55 = $247.5 < $250
    new_price = 55 * EIGHTEEN_DECIMALS // 100  # Drop to $0.55 each
    mock_price_source.setPrice(alpha_token, new_price)
    mock_price_source.setPrice(bravo_token, new_price)
    mock_price_source.setPrice(charlie_token, new_price)
    
    assert credit_engine.canLiquidateUser(bob) == True

    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)

    # Verify different liquidation methods were used based on asset configs
    stab_pool_logs = filter_logs(teller, "CollateralSwappedWithStabPool")
    endaoment_logs = filter_logs(teller, "CollateralSentToEndaoment")
    auction_logs = filter_logs(teller, "NewFungibleAuctionCreated")
    
    # Should have exactly one of each liquidation type
    assert len(stab_pool_logs) == 1  # Alpha via stability pool
    assert len(endaoment_logs) == 1  # Bravo via endaoment
    assert len(auction_logs) == 1    # Charlie via auction
    
    alpha_log = stab_pool_logs[0]
    bravo_log = endaoment_logs[0]
    charlie_log = auction_logs[0]
    
    # Verify correct assets were liquidated via correct methods
    assert alpha_log.liqAsset == alpha_token.address
    assert bravo_log.liqAsset == bravo_token.address
    assert charlie_log.asset == charlie_token.address
    
    # Calculate total liquidated value (excluding charlie which goes to auction)
    total_liquidated_value = alpha_log.stabValueSwapped + bravo_log.usdValue
    
    # Verify final state
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    
    # Calculate expected final debt based on actual liquidations
    exp_liq_fees = debt_amount * 10_00 // HUNDRED_PERCENT
    actual_repay = total_liquidated_value
    
    # Calculate liquidation fees paid through collateral premium
    total_collateral_taken = alpha_log.collateralValueOut + bravo_log.usdValue
    liq_fees_paid = total_collateral_taken - actual_repay
    unpaid_liq_fees = max(0, exp_liq_fees - liq_fees_paid)
    
    expected_final_debt = debt_amount - actual_repay + unpaid_liq_fees
    _test(expected_final_debt, user_debt.amount)


def test_ah_liquidation_priority_asset_order(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    charlie_token,
    charlie_token_whale,
    bob,
    teller,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    sally,
    vault_book,
    control_room,
    governance,
    endaoment,
    _test,
):
    """Test that priority liquidation asset order is respected"""
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    
    # Setup all assets with endaoment transfer for simplicity
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    
    for token in [alpha_token, bravo_token, charlie_token]:
        setAssetConfig(
            token,
            _debtTerms=debt_terms,
            _shouldBurnAsPayment=False,
            _shouldTransferToEndaoment=True,
            _shouldSwapInStabPools=False,
            _shouldAuctionInstantly=False,
        )

    # Setup prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, 1 * EIGHTEEN_DECIMALS)

    # User deposits assets in order: alpha, bravo, charlie
    alpha_amount = 100 * EIGHTEEN_DECIMALS
    bravo_amount = 150 * EIGHTEEN_DECIMALS
    charlie_amount = 200 * 10**6  # Charlie has 6 decimals
    
    performDeposit(bob, alpha_amount, alpha_token, alpha_token_whale)
    performDeposit(bob, bravo_amount, bravo_token, bravo_token_whale)
    performDeposit(bob, charlie_amount, charlie_token, charlie_token_whale)
    
    # Borrow against collateral
    debt_amount = 200 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Set priority liquidation assets in DIFFERENT order than deposit order
    # Priority: charlie first, then alpha (bravo will be natural order last)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    control_room.setPriorityLiqAssetVaults([
        (vault_id, charlie_token),  # Priority 1: charlie (deposited 3rd)
        (vault_id, alpha_token),      # Priority 2: alpha (deposited 1st)
        # bravo not in priority list, so it goes in natural order (last)
    ], sender=governance.address)

    # Set liquidatable prices
    new_price = 55 * EIGHTEEN_DECIMALS // 100  # Drop to $0.55 each
    mock_price_source.setPrice(alpha_token, new_price)
    mock_price_source.setPrice(bravo_token, new_price)
    mock_price_source.setPrice(charlie_token, new_price)
    
    assert credit_engine.canLiquidateUser(bob) == True

    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)

    # Get all endaoment transfer events
    endaoment_logs = filter_logs(teller, "CollateralSentToEndaoment")
    
    # Should have liquidated all 3 assets via endaoment transfer
    assert len(endaoment_logs) == 3
    
    # Verify liquidation order matches priority: charlie, alpha, bravo
    assert endaoment_logs[0].liqAsset == charlie_token.address  # Priority 1
    assert endaoment_logs[1].liqAsset == alpha_token.address    # Priority 2  
    assert endaoment_logs[2].liqAsset == bravo_token.address    # Natural order (not in priority)
    
    # Verify assets were transferred to endaoment
    charlie_expected = endaoment_logs[0].amountSent
    alpha_expected = endaoment_logs[1].amountSent
    bravo_expected = endaoment_logs[2].amountSent
    
    assert charlie_token.balanceOf(endaoment) == charlie_expected
    assert alpha_token.balanceOf(endaoment) == alpha_expected
    assert bravo_token.balanceOf(endaoment) == bravo_expected
    
    # Verify liquidation math
    total_liquidated_value = sum(log.usdValue for log in endaoment_logs)
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    
    exp_liq_fees = debt_amount * 10_00 // HUNDRED_PERCENT
    expected_final_debt = debt_amount - total_liquidated_value + exp_liq_fees
    _test(expected_final_debt, user_debt.amount)


def test_ah_liquidation_iterate_thru_all_user_vaults(
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
    bob,
    teller,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    sally,
    endaoment,
    _test,
):
    """Test liquidation that goes through _iterateThruAllUserVaults (Phase 3)
    
    This test specifically exercises the natural vault iteration order when:
    - No stability pools are involved (Phase 1 skipped)
    - No priority liquidation assets are set (Phase 2 skipped)
    - Liquidation proceeds to Phase 3: iterate through all user vaults in order
    """
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    
    # Setup all assets with endaoment transfer (simple liquidation method)
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    
    for token in [alpha_token, bravo_token, charlie_token]:
        setAssetConfig(
            token,
            _debtTerms=debt_terms,
            _shouldBurnAsPayment=False,
            _shouldTransferToEndaoment=True,
            _shouldSwapInStabPools=False,  # No stability pools
            _shouldAuctionInstantly=False,
        )

    # Setup prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, 1 * EIGHTEEN_DECIMALS)

    # User deposits assets in specific order: alpha, bravo, charlie
    # This order should be preserved in the vault's user asset list
    alpha_amount = 100 * EIGHTEEN_DECIMALS
    bravo_amount = 150 * EIGHTEEN_DECIMALS
    charlie_amount = 200 * 10**6  # Charlie has 6 decimals
    
    performDeposit(bob, alpha_amount, alpha_token, alpha_token_whale)
    performDeposit(bob, bravo_amount, bravo_token, bravo_token_whale)
    performDeposit(bob, charlie_amount, charlie_token, charlie_token_whale)
    
    # Borrow against collateral
    debt_amount = 200 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # NOTE: We deliberately do NOT set any priority liquidation assets
    # This ensures Phase 2 is skipped and we go straight to Phase 3

    # Set liquidatable prices
    new_price = 55 * EIGHTEEN_DECIMALS // 100  # Drop to $0.55 each
    mock_price_source.setPrice(alpha_token, new_price)
    mock_price_source.setPrice(bravo_token, new_price)
    mock_price_source.setPrice(charlie_token, new_price)
    
    assert credit_engine.canLiquidateUser(bob) == True

    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)

    # Get all endaoment transfer events
    endaoment_logs = filter_logs(teller, "CollateralSentToEndaoment")
    
    # Should have liquidated all 3 assets via endaoment transfer
    assert len(endaoment_logs) == 3
    
    # Verify liquidation order matches the natural vault order (deposit order)
    # Since no priority assets are set, it should follow the order assets were deposited
    assert endaoment_logs[0].liqAsset == alpha_token.address   # First deposited
    assert endaoment_logs[1].liqAsset == bravo_token.address   # Second deposited  
    assert endaoment_logs[2].liqAsset == charlie_token.address # Third deposited
    
    # Verify assets were transferred to endaoment in the expected amounts
    alpha_expected = endaoment_logs[0].amountSent
    bravo_expected = endaoment_logs[1].amountSent
    charlie_expected = endaoment_logs[2].amountSent
    
    assert alpha_token.balanceOf(endaoment) == alpha_expected
    assert bravo_token.balanceOf(endaoment) == bravo_expected
    assert charlie_token.balanceOf(endaoment) == charlie_expected
    
    # Verify liquidation math
    total_liquidated_value = sum(log.usdValue for log in endaoment_logs)
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    
    exp_liq_fees = debt_amount * 10_00 // HUNDRED_PERCENT
    expected_final_debt = debt_amount - total_liquidated_value + exp_liq_fees
    _test(expected_final_debt, user_debt.amount)
    

def test_ah_liquidation_phase_1_liq_user_in_stability_pool(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    bob,
    teller,
    whale,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    auction_house,
    sally,
    stability_pool,
    vault_book,
    control_room,
    governance,
    _test,
):
    """Test Phase 1 of liquidation: liquidated user has deposits in stability pools
    
    This test specifically exercises Phase 1 where:
    - The liquidated user (bob) has deposits in stability pools
    - Those stability pool deposits are liquidated FIRST (before other collateral)
    - This tests the priorityStabVaults iteration and isParticipatingInVault check
    """
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    
    # Setup collateral asset (alpha_token) - will be liquidated via endaoment
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,  # Simple liquidation for collateral
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=False,
    )
    
    # Setup stability pool assets
    stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(green_token, _debtTerms=stab_debt_terms, _shouldBurnAsPayment=True)
    setAssetConfig(bravo_token, _debtTerms=stab_debt_terms, _shouldTransferToEndaoment=True)
    
    # Configure priority stability pools
    stab_pool_id = vault_book.getRegId(stability_pool)
    control_room.setPriorityStabVaults([
        (stab_pool_id, green_token),   # Priority 1
        (stab_pool_id, bravo_token),   # Priority 2
    ], sender=governance.address)

    # Setup prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)

    # Setup liquidation user (bob) with BOTH collateral AND stability pool deposits
    
    # 1. Bob deposits collateral (alpha_token)
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale)
    
    # 2. Bob deposits into stability pools (this is the key for Phase 1!)
    green_stab_amount = 30 * EIGHTEEN_DECIMALS
    bravo_stab_amount = 50 * EIGHTEEN_DECIMALS
    
    # Transfer tokens to bob and deposit into stability pool
    green_token.transfer(bob, green_stab_amount, sender=whale)
    green_token.approve(teller, green_stab_amount, sender=bob)
    teller.deposit(green_token, green_stab_amount, bob, stability_pool, 0, sender=bob)
    
    bravo_token.transfer(bob, bravo_stab_amount, sender=bravo_token_whale)
    bravo_token.approve(teller, bravo_stab_amount, sender=bob)
    teller.deposit(bravo_token, bravo_stab_amount, bob, stability_pool, 0, sender=bob)
    
    # 3. Bob borrows against his collateral
    debt_amount = 100 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Set liquidatable prices
    new_price = 55 * EIGHTEEN_DECIMALS // 100  # Drop to $0.55 each
    mock_price_source.setPrice(alpha_token, new_price)
    
    assert credit_engine.canLiquidateUser(bob) == True

    # Get pre-liquidation state
    target_repay_amount = auction_house.calcAmountOfDebtToRepayDuringLiq(bob)
    
    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)

    # Verify Phase 1 happened: stability pool assets were liquidated first
    # We should see StabAssetBurntAsRepayment events for bob's stability pool deposits
    burn_logs = filter_logs(teller, "StabAssetBurntAsRepayment")
    endaoment_logs = filter_logs(teller, "CollateralSentToEndaoment")
    
    # Should have burned stability pool assets first (Phase 1)
    assert len(burn_logs) == 1  # green from stability pool
    
    # green burned
    green_burn_log = burn_logs[0]   
    assert green_burn_log.liqStabAsset == green_token.address
    assert green_burn_log.liqUser == bob
    
    # bravo sent to endaoment
    bravo_endaoment_log = endaoment_logs[0]
    assert bravo_endaoment_log.liqAsset == bravo_token.address
    assert bravo_endaoment_log.liqUser == bob
    
    # Verify the amounts match bob's stability pool deposits
    _test(green_stab_amount, green_burn_log.amountBurned)
    _test(green_stab_amount, green_burn_log.usdValue)  # 1:1 price
    
    _test(bravo_stab_amount, bravo_endaoment_log.amountSent)
    _test(bravo_stab_amount, bravo_endaoment_log.usdValue)  # 1:1 price
    
    # Calculate total value from Phase 1 (stability pool liquidation)
    phase1_value = green_burn_log.usdValue + bravo_endaoment_log.usdValue
    
    # Phase 1 provides: 30 + 50 = 80 USD
    # Target repay amount should be ~99 USD (based on debt amount and liquidation mechanics)
    # Therefore Phase 1 will NOT cover everything, Phase 3 must handle the remainder
    assert phase1_value < target_repay_amount  # Verify our assumption
    
    # Phase 3 should handle the remainder with alpha_token
    assert len(endaoment_logs) == 2  # bravo (Phase 1) + alpha (Phase 3)
    alpha_endaoment_log = endaoment_logs[1]  # Second log should be alpha
    assert alpha_endaoment_log.liqAsset == alpha_token.address
    assert alpha_endaoment_log.liqUser == bob
    
    # Total liquidated value should equal target repay amount
    total_liquidated = phase1_value + alpha_endaoment_log.usdValue
    _test(target_repay_amount, total_liquidated)
    
    # Verify final debt state
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    
    # Calculate expected final debt
    total_liquidated_value = sum(log.usdValue for log in burn_logs) + sum(log.usdValue for log in endaoment_logs)
    exp_liq_fees = debt_amount * 10_00 // HUNDRED_PERCENT
    expected_final_debt = debt_amount - total_liquidated_value + exp_liq_fees
    _test(expected_final_debt, user_debt.amount)

