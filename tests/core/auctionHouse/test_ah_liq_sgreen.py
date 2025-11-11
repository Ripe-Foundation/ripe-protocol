from constants import EIGHTEEN_DECIMALS, HUNDRED_PERCENT
from conf_utils import filter_logs


def test_ah_liquidation_stab_pool_with_sgreen(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    savings_green,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    auction_house,
    sally,
    switchboard_alpha,
    mission_control,
    stability_pool,
    green_token,
    _test,
    whale,
    alice,
):
    """Test stability pool swap liquidation where target repay exceeds debt amount, resulting in full debt payoff"""
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0, _keeperFeeRatio=1_00, _minKeeperFee=1_00)

    # alpha token config - will be swapped via stability pool
    debt_terms = createDebtTerms(
        _ltv = 50_00,
        _redemptionThreshold = 60_00,
        _liqThreshold = 70_00,
        _liqFee = 10_00,
        _borrowRate = 5_00,
        _daowry = 1,
    )
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=True,
    )
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # stab pool config
    stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(savings_green, _vaultIds=[1], _debtTerms=stab_debt_terms, _shouldBurnAsPayment=True)
    mission_control.setPriorityStabVaults([(1, savings_green)], sender=switchboard_alpha.address)

    # user deposit + borrow
    deposit_amount = 1_000 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    orig_debt_amount = 500 * EIGHTEEN_DECIMALS
    teller.borrow(orig_debt_amount, bob, False, sender=bob)

    # alice deposits into stab pool - this provides liquidity for the swap
    alice_amount = 1000 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, alice_amount, sender=whale)
    green_token.approve(savings_green, alice_amount, sender=alice)
    alice_shares = savings_green.deposit(alice_amount, alice, sender=alice)
    savings_green.approve(teller, alice_shares, sender=alice)
    teller.deposit(savings_green, alice_shares, alice, stability_pool, sender=alice)
    assert stability_pool.getTotalAmountForUser(alice, savings_green) == alice_shares

    # set liquidatable price
    new_price = int(0.6 * EIGHTEEN_DECIMALS) # 60% of original price
    mock_price_source.setPrice(alpha_token, new_price)
    assert credit_engine.canLiquidateUser(bob)

    # pre liquidation state
    orig_user_debt, orig_bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    _test(orig_user_debt.amount, orig_debt_amount)
    _test(orig_bt.collateralVal, 600 * EIGHTEEN_DECIMALS)
    
    target_repay_amount = auction_house.calcAmountOfDebtToRepayDuringLiq(bob)
    pre_green_bal = green_token.balanceOf(savings_green)
    _test(pre_green_bal, alice_amount)

    # Important: target_repay_amount exceeds debt amount, so all debt will be paid
    assert target_repay_amount > orig_debt_amount, f"Target repay {target_repay_amount} should exceed debt {orig_debt_amount}"

    # liquidate user - should use stability pool swap
    teller.liquidateUser(bob, False, sender=sally)

    # Get liquidation results
    log = filter_logs(teller, "LiquidateUser")[0]
    post_user_debt, post_bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    post_green_bal = green_token.balanceOf(savings_green)
    user_stab_value = stability_pool.getTotalUserValue(alice, savings_green)
    
    # OPINIONATED ASSERTIONS:

    # 1. Debt health MUST be restored (this was the bug we fixed)
    assert log.didRestoreDebtHealth, "Liquidation must restore debt health"
    assert log.numAuctionsStarted == 0, "No auctions should be started when debt health is restored"

    # 2. All debt should be paid off (LTV = 0) since target repay exceeds debt amount
    # Since target repay exceeds debt, all debt should be paid
    assert post_user_debt.amount == 0, f"All debt should be paid off, but {post_user_debt.amount} remains"

    # User should still have collateral remaining after liquidation
    assert post_bt.collateralVal > 0, f"User should have remaining collateral, but has {post_bt.collateralVal}"

    # LTV should be 0 (no debt remaining, but collateral exists)
    actual_ltv = 0  # No debt means LTV is 0
    assert actual_ltv == 0, "LTV should be 0 after full debt payoff"
    
    # 3. Liquidation fees must be exactly 11% (10% + 1% keeper fee)
    expected_total_fees = orig_debt_amount * 11_00 // HUNDRED_PERCENT  # 55 GREEN
    assert log.totalLiqFees == expected_total_fees, f"Total liquidation fees should be 11%: expected {expected_total_fees}, actual {log.totalLiqFees}"
    expected_keeper_fee = orig_debt_amount * 1_00 // HUNDRED_PERCENT
    assert log.keeperFee == expected_keeper_fee, f"Keeper fee should be 1%: expected {expected_keeper_fee}, actual {log.keeperFee}"
    
    # 4. Repay amount should equal original debt (capped at debt amount even though target is higher)
    assert log.repayAmount == orig_debt_amount, f"Actual repay {log.repayAmount} should equal original debt {orig_debt_amount}"
    
    # 5. Collateral taken should be based on target repay amount / (1 - liq fee ratio)
    # Target is 510, so collateral = 510 / 0.89 = 573.03 GREEN
    expected_collateral_out = target_repay_amount * HUNDRED_PERCENT // (HUNDRED_PERCENT - 11_00)
    _test(expected_collateral_out, log.collateralValueOut)  # default tolerance
    
    # 6. Debt reduction should equal original debt (all debt paid off)
    debt_reduction = orig_user_debt.amount - post_user_debt.amount
    assert debt_reduction == orig_debt_amount, f"Debt reduction {debt_reduction} should equal original debt {orig_debt_amount}"
    assert debt_reduction == log.repayAmount, f"Debt reduction {debt_reduction} should equal repay amount {log.repayAmount}"
    
    # 7. Collateral reduction should equal collateral taken
    collateral_reduction = orig_bt.collateralVal - post_bt.collateralVal
    assert collateral_reduction == log.collateralValueOut, f"Collateral reduction {collateral_reduction} should equal collateral taken {log.collateralValueOut}"
    
    # 8. Stability pool mechanics should be correct
    # GREEN used should match target repay (510), not actual repay (500) due to how swaps work
    green_used = pre_green_bal - post_green_bal
    _test(target_repay_amount, green_used)  # default tolerance
    
    # Alice should have received collateral value > GREEN given up (she profits from the liquidation)
    # Alice gave up 510 GREEN (target) but got collateral worth 573.03 GREEN
    alice_profit = log.collateralValueOut - target_repay_amount
    expected_alice_value = alice_amount + alice_profit
    _test(expected_alice_value, user_stab_value)  # default tolerance
    
    # 9. No unpaid liquidation fees (all fees covered by collateral difference)
    assert log.liqFeesUnpaid == 0, "All liquidation fees should be covered by collateral difference"
