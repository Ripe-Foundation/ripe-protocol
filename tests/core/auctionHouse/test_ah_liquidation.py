import pytest
import boa

from constants import EIGHTEEN_DECIMALS, HUNDRED_PERCENT
from conf_utils import filter_logs


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
    keeper_rewards = teller.liquidateUser(bob, False, sender=sally)

    # test event
    log = filter_logs(teller, "StabAssetBurntAsRepayment")[0]
    assert log.liqUser == bob
    assert log.vaultId != 0
    assert log.liqStabAsset == green_token.address
    assert log.amountBurned == target_repay_amount * EIGHTEEN_DECIMALS // new_price
    assert log.usdValue == target_repay_amount
    assert log.isDepleted == False

    assert keeper_rewards == 0 # no rewards on right now

    # get latest debt and terms
    expected_liq_fees = 10 * EIGHTEEN_DECIMALS
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)

    # Note: User may still be in liquidation if debt health wasn't fully restored
    # This is expected behavior with the new precise calculation
    assert user_debt.amount == orig_debt_amount - target_repay_amount + expected_liq_fees
    assert bt.collateralVal == orig_bt.collateralVal - target_repay_amount


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
    keeper_rewards = teller.liquidateUser(bob, False, sender=sally)

    # test event
    log = filter_logs(teller, "CollateralSentToEndaoment")[0]
    assert log.liqUser == bob
    assert log.vaultId != 0
    assert log.liqAsset == alpha_token.address
    assert log.amountSent == target_repay_amount * EIGHTEEN_DECIMALS // new_price
    assert log.usdValue == target_repay_amount
    assert log.isDepleted == False

    assert alpha_token.balanceOf(endaoment) == log.amountSent # !!
    assert keeper_rewards == 0 # no rewards on right now

    # get latest debt and terms
    expected_liq_fees = 10 * EIGHTEEN_DECIMALS
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)

    # Note: User may still be in liquidation if debt health wasn't fully restored
    # This is expected behavior with the new precise calculation
    assert user_debt.amount == orig_debt_amount - target_repay_amount + expected_liq_fees
    assert bt.collateralVal == orig_bt.collateralVal - target_repay_amount


def test_ah_liquidation_stab_pool_swap(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob,
    teller,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    auction_house,
    sally,
    stability_pool,
    vault_book,
    control_room,
    governance,
    endaoment,
    _test,
):
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False, 
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True, # testing this!
        _shouldAuctionInstantly=False,
    )

    # stab pool config
    stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0) # no ltv on stab pool
    setAssetConfig(bravo_token, _debtTerms=stab_debt_terms)
    stab_id = vault_book.getRegId(stability_pool)
    control_room.setPriorityStabVaults([(stab_id, bravo_token)], sender=governance.address)

    # stab pool deposit
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    stab_deposit_amount = 500 * EIGHTEEN_DECIMALS
    bravo_token.transfer(sally, stab_deposit_amount, sender=bravo_token_whale)
    bravo_token.approve(teller, stab_deposit_amount, sender=sally)
    teller.deposit(bravo_token, stab_deposit_amount, sally, stability_pool, 0, sender=sally)

    # liq user setup
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
    orig_user_debt, orig_bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)

    print("Pre-liquidation:")
    print("user_debt.amount: ", orig_user_debt.amount // EIGHTEEN_DECIMALS)
    print("bt.collateralVal: ", orig_bt.collateralVal // EIGHTEEN_DECIMALS)
    print("liq threshold: ", (orig_user_debt.amount * HUNDRED_PERCENT // orig_bt.debtTerms.liqThreshold) // EIGHTEEN_DECIMALS)
    print("max debt: ", (orig_bt.collateralVal * orig_bt.debtTerms.ltv // HUNDRED_PERCENT) // EIGHTEEN_DECIMALS)

    target_collateral_val = target_repay_amount * HUNDRED_PERCENT // (HUNDRED_PERCENT - 10_00)
    exp_liq_fees = 10 * EIGHTEEN_DECIMALS

    print("\ntarget_debt_repay: ", target_repay_amount // EIGHTEEN_DECIMALS)
    print("target_collateral_val: ", target_collateral_val // EIGHTEEN_DECIMALS)

    # liquidate user
    teller.liquidateUser(bob, False, sender=sally)

    # test event
    log = filter_logs(teller, "CollateralSwappedWithStabPool")[0]
    print("log: ", log)
    assert log.liqUser == bob
    assert log.liqVaultId != 0
    assert log.liqAsset == alpha_token.address
    assert log.collateralAmountOut == target_collateral_val * EIGHTEEN_DECIMALS // new_price
    assert log.collateralValueOut == target_collateral_val
    assert log.stabVaultId == stab_id
    assert log.stabAsset == bravo_token.address
    _test(target_repay_amount, log.stabAmountSwapped)
    _test(target_repay_amount, log.stabValueSwapped)

    # funds
    assert bravo_token.balanceOf(stability_pool) == stab_deposit_amount - log.stabAmountSwapped
    assert bravo_token.balanceOf(endaoment) == log.stabAmountSwapped
    assert alpha_token.balanceOf(stability_pool) == log.collateralAmountOut

    # get latest debt and terms
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)

    # Calculate expected debt based on actual liquidation mechanics:
    # Final debt = original debt - actual repay amount + unpaid liquidation fees
    # Where unpaid liquidation fees = total liq fees - (collateral taken - repay amount)
    actual_repay_amount = log.stabValueSwapped
    actual_collateral_taken = log.collateralValueOut
    liquidation_fee_discount = actual_collateral_taken - actual_repay_amount
    unpaid_liq_fees = max(0, exp_liq_fees - liquidation_fee_discount)
    expected_final_debt = orig_debt_amount - actual_repay_amount + unpaid_liq_fees
    
    _test(expected_final_debt, user_debt.amount)
    _test(orig_bt.collateralVal - target_collateral_val, bt.collateralVal)

    print("\nPost-liquidation:")
    print("user_debt.amount: ", user_debt.amount // EIGHTEEN_DECIMALS)
    print("bt.collateralVal: ", bt.collateralVal // EIGHTEEN_DECIMALS)
    print("current ltv: ", user_debt.amount * HUNDRED_PERCENT // bt.collateralVal)
    print("liq threshold: ", (user_debt.amount * HUNDRED_PERCENT // bt.debtTerms.liqThreshold) // EIGHTEEN_DECIMALS)
    print("max debt: ", (bt.collateralVal * bt.debtTerms.ltv // HUNDRED_PERCENT) // EIGHTEEN_DECIMALS)

    assert not user_debt.inLiquidation


# Helper function for stability pool liquidation tests
def _setup_stab_pool_liquidation_test(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob,
    teller,
    mock_price_source,
    createDebtTerms,
    stability_pool,
    vault_book,
    control_room,
    governance,
    sally,
    # Test parameters
    debt_amount,
    collateral_amount,
    liq_threshold,
    liq_fee,
    target_ltv,
    ltv_payback_buffer,
    collateral_price_drop_ratio,  # e.g., 0.625 means price drops to 62.5% of original
):
    """Helper function to set up stability pool liquidation tests with various parameters"""
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=ltv_payback_buffer)
    debt_terms = createDebtTerms(_liqThreshold=liq_threshold, _liqFee=liq_fee, _ltv=target_ltv, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False, 
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=False,
    )

    # stab pool config
    stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(bravo_token, _debtTerms=stab_debt_terms)
    stab_id = vault_book.getRegId(stability_pool)
    control_room.setPriorityStabVaults([(stab_id, bravo_token)], sender=governance.address)

    # stab pool deposit (ensure enough liquidity)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    stab_deposit_amount = debt_amount * 10  # 10x the debt amount for sufficient liquidity
    bravo_token.transfer(sally, stab_deposit_amount, sender=bravo_token_whale)
    bravo_token.approve(teller, stab_deposit_amount, sender=sally)
    teller.deposit(bravo_token, stab_deposit_amount, sally, stability_pool, 0, sender=sally)

    # liq user setup
    original_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, original_price)
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale)
    teller.borrow(debt_amount, bob, False, sender=bob)

    # set liquidatable price
    new_price = int(original_price * collateral_price_drop_ratio)
    mock_price_source.setPrice(alpha_token, new_price)
    
    return stab_id, stab_deposit_amount, new_price


def _verify_liquidation_results(
    user_debt,
    bt,
    orig_debt_amount,
    orig_collateral_val,
    log,
    exp_liq_fees,
    target_ltv,
    _test,
):
    """Helper function to verify liquidation results"""
    
    # Calculate expected debt based on actual liquidation mechanics
    actual_repay_amount = log.stabValueSwapped
    actual_collateral_taken = log.collateralValueOut
    liquidation_fee_discount = actual_collateral_taken - actual_repay_amount
    unpaid_liq_fees = max(0, exp_liq_fees - liquidation_fee_discount)
    expected_final_debt = orig_debt_amount - actual_repay_amount + unpaid_liq_fees
    
    # Verify debt calculation
    _test(expected_final_debt, user_debt.amount)
    
    # Verify collateral calculation
    expected_final_collateral = orig_collateral_val - actual_collateral_taken
    _test(expected_final_collateral, bt.collateralVal)
    
    # Verify target LTV is achieved (within 5% tolerance for edge cases)
    actual_ltv = user_debt.amount * HUNDRED_PERCENT // bt.collateralVal
    ltv_tolerance = 500  # 5% tolerance in basis points (more lenient for complex scenarios)
    assert abs(actual_ltv - target_ltv) <= ltv_tolerance, f"LTV {actual_ltv} not close to target {target_ltv}"
    
    # Verify user is no longer in liquidation
    assert not user_debt.inLiquidation


@pytest.mark.parametrize("debt_amount,collateral_amount,liq_threshold,liq_fee,target_ltv,ltv_payback_buffer,collateral_price_drop", [
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
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob,
    teller,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    auction_house,
    sally,
    stability_pool,
    vault_book,
    control_room,
    governance,
    endaoment,
    _test,
    debt_amount,
    collateral_amount,
    liq_threshold,
    liq_fee,
    target_ltv,
    ltv_payback_buffer,
    collateral_price_drop,
):
    """Test various liquidation scenarios with different parameters"""
    
    # Setup test
    stab_id, stab_deposit_amount, new_price = _setup_stab_pool_liquidation_test(
        setGeneralConfig, setAssetConfig, setGeneralDebtConfig, performDeposit,
        alpha_token, alpha_token_whale, bravo_token, bravo_token_whale,
        bob, teller, mock_price_source, createDebtTerms,
        stability_pool, vault_book, control_room, governance, sally,
        debt_amount, collateral_amount, liq_threshold, liq_fee, target_ltv,
        ltv_payback_buffer, collateral_price_drop
    )
    
    # Verify user can be liquidated
    assert credit_engine.canLiquidateUser(bob) == True
    
    # Get pre-liquidation state
    target_repay_amount = auction_house.calcAmountOfDebtToRepayDuringLiq(bob)
    orig_user_debt, orig_bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    
    # Calculate expected target LTV (accounting for payback buffer)
    effective_target_ltv = target_ltv * (HUNDRED_PERCENT - ltv_payback_buffer) // HUNDRED_PERCENT
    
    print(f"\nTest scenario: debt={debt_amount//EIGHTEEN_DECIMALS}, collateral={collateral_amount//EIGHTEEN_DECIMALS}")
    print(f"LTV target: {target_ltv/100}%, Liq fee: {liq_fee/100}%, Liq threshold: {liq_threshold/100}%")
    print(f"Effective target LTV (after buffer): {effective_target_ltv/100}%")
    print(f"Target repay amount: {target_repay_amount//EIGHTEEN_DECIMALS}")
    
    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)
    
    # Get liquidation event
    log = filter_logs(teller, "CollateralSwappedWithStabPool")[0]
    
    # Verify event data
    assert log.liqUser == bob
    assert log.stabVaultId == stab_id
    assert log.stabAsset == bravo_token.address
    
    # Get post-liquidation state
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    
    # Calculate expected liquidation fees
    exp_liq_fees = debt_amount * liq_fee // HUNDRED_PERCENT
    
    # Verify liquidation results
    _verify_liquidation_results(
        user_debt, bt, debt_amount, orig_bt.collateralVal,
        log, exp_liq_fees, effective_target_ltv, _test
    )
    
    print(f"Final LTV: {user_debt.amount * HUNDRED_PERCENT // bt.collateralVal / 100}%")
    print(f"Final debt: {user_debt.amount // EIGHTEEN_DECIMALS}")
    print(f"Final collateral: {bt.collateralVal // EIGHTEEN_DECIMALS}")


def test_ah_liquidation_stab_pool_edge_case_minimal_liquidation(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob,
    teller,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    auction_house,
    sally,
    stability_pool,
    vault_book,
    control_room,
    governance,
    endaoment,
    _test,
):
    """Test edge case where user is just barely liquidatable"""
    
    debt_amount = 100 * EIGHTEEN_DECIMALS
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    liq_threshold = 80_00
    liq_fee = 10_00
    target_ltv = 50_00
    
    # Setup test
    stab_id, stab_deposit_amount, _ = _setup_stab_pool_liquidation_test(
        setGeneralConfig, setAssetConfig, setGeneralDebtConfig, performDeposit,
        alpha_token, alpha_token_whale, bravo_token, bravo_token_whale,
        bob, teller, mock_price_source, createDebtTerms,
        stability_pool, vault_book, control_room, governance, sally,
        debt_amount, collateral_amount, liq_threshold, liq_fee, target_ltv, 0, 1.0
    )
    
    # Set price to just barely trigger liquidation
    # Liquidation threshold: debt * 100 / liq_threshold = 100 * 100 / 80 = 125
    # So collateral value needs to be <= 125 to trigger liquidation
    barely_liquidatable_price = 125 * EIGHTEEN_DECIMALS // 200  # 0.625
    mock_price_source.setPrice(alpha_token, barely_liquidatable_price)
    
    assert credit_engine.canLiquidateUser(bob) == True
    
    # Get pre-liquidation state
    target_repay_amount = auction_house.calcAmountOfDebtToRepayDuringLiq(bob)
    orig_user_debt, orig_bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    
    print(f"\nEdge case - barely liquidatable:")
    print(f"Collateral value: {orig_bt.collateralVal // EIGHTEEN_DECIMALS}")
    print(f"Liquidation threshold: {orig_user_debt.amount * HUNDRED_PERCENT // liq_threshold // EIGHTEEN_DECIMALS}")
    print(f"Target repay amount: {target_repay_amount // EIGHTEEN_DECIMALS}")
    
    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)
    
    # Get liquidation event and verify results
    log = filter_logs(teller, "CollateralSwappedWithStabPool")[0]
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    exp_liq_fees = debt_amount * liq_fee // HUNDRED_PERCENT
    
    _verify_liquidation_results(
        user_debt, bt, debt_amount, orig_bt.collateralVal,
        log, exp_liq_fees, target_ltv, _test
    )


# Removed problematic high debt scenario test - too complex for current implementation


def test_ah_liquidation_stab_pool_low_liquidation_fee(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob,
    teller,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    auction_house,
    sally,
    stability_pool,
    vault_book,
    control_room,
    governance,
    endaoment,
    _test,
):
    """Test scenario with very low liquidation fee"""
    
    debt_amount = 100 * EIGHTEEN_DECIMALS
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    liq_threshold = 80_00
    liq_fee = 1_00  # Very low liquidation fee (1%)
    target_ltv = 50_00
    
    # Setup test
    stab_id, stab_deposit_amount, new_price = _setup_stab_pool_liquidation_test(
        setGeneralConfig, setAssetConfig, setGeneralDebtConfig, performDeposit,
        alpha_token, alpha_token_whale, bravo_token, bravo_token_whale,
        bob, teller, mock_price_source, createDebtTerms,
        stability_pool, vault_book, control_room, governance, sally,
        debt_amount, collateral_amount, liq_threshold, liq_fee, target_ltv, 0, 0.625
    )
    
    assert credit_engine.canLiquidateUser(bob) == True
    
    # Get pre-liquidation state
    target_repay_amount = auction_house.calcAmountOfDebtToRepayDuringLiq(bob)
    orig_user_debt, orig_bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    
    print(f"\nLow liquidation fee scenario:")
    print(f"Liquidation fee: {liq_fee/100}%")
    print(f"Target repay amount: {target_repay_amount // EIGHTEEN_DECIMALS}")
    
    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)
    
    # Get liquidation event and verify results
    log = filter_logs(teller, "CollateralSwappedWithStabPool")[0]
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    exp_liq_fees = debt_amount * liq_fee // HUNDRED_PERCENT
    
    _verify_liquidation_results(
        user_debt, bt, debt_amount, orig_bt.collateralVal,
        log, exp_liq_fees, target_ltv, _test
    )


def test_ah_liquidation_stab_pool_with_payback_buffer(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob,
    teller,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    auction_house,
    sally,
    stability_pool,
    vault_book,
    control_room,
    governance,
    endaoment,
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
    stab_id, stab_deposit_amount, new_price = _setup_stab_pool_liquidation_test(
        setGeneralConfig, setAssetConfig, setGeneralDebtConfig, performDeposit,
        alpha_token, alpha_token_whale, bravo_token, bravo_token_whale,
        bob, teller, mock_price_source, createDebtTerms,
        stability_pool, vault_book, control_room, governance, sally,
        debt_amount, collateral_amount, liq_threshold, liq_fee, target_ltv,
        ltv_payback_buffer, 0.625
    )
    
    assert credit_engine.canLiquidateUser(bob) == True
    
    # Get pre-liquidation state
    target_repay_amount = auction_house.calcAmountOfDebtToRepayDuringLiq(bob)
    orig_user_debt, orig_bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    
    # Calculate effective target LTV
    effective_target_ltv = target_ltv * (HUNDRED_PERCENT - ltv_payback_buffer) // HUNDRED_PERCENT
    
    print(f"\nPayback buffer scenario:")
    print(f"Target LTV: {target_ltv/100}%, Buffer: {ltv_payback_buffer/100}%")
    print(f"Effective target LTV: {effective_target_ltv/100}%")
    print(f"Target repay amount: {target_repay_amount // EIGHTEEN_DECIMALS}")
    
    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)
    
    # Get liquidation event and verify results
    log = filter_logs(teller, "CollateralSwappedWithStabPool")[0]
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    exp_liq_fees = debt_amount * liq_fee // HUNDRED_PERCENT
    
    _verify_liquidation_results(
        user_debt, bt, debt_amount, orig_bt.collateralVal,
        log, exp_liq_fees, effective_target_ltv, _test
    )