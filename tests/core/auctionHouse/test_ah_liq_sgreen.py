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
    """Test stability pool swap liquidation with corrected debt repayment calculation"""
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=1_00, _keeperFeeRatio=1_00, _minKeeperFee=1_00) # 1% payback buffer

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
    
    # 2. Target LTV must be achieved (49% = 50% - 1% buffer)
    target_ltv = 49_00  # 50% - 1% payback buffer
    actual_ltv = post_user_debt.amount * HUNDRED_PERCENT // post_bt.collateralVal
    # Allow 1% tolerance for rounding
    assert abs(actual_ltv - target_ltv) <= 100, f"LTV {actual_ltv/100:.1f}% should be close to target {target_ltv/100:.1f}%"
    
    # 3. Liquidation fees must be exactly 11% (10% + 1% keeper fee)
    expected_total_fees = orig_debt_amount * 11_00 // HUNDRED_PERCENT  # 55 GREEN
    assert log.totalLiqFees == expected_total_fees, f"Total liquidation fees should be 11%: expected {expected_total_fees}, actual {log.totalLiqFees}"
    expected_keeper_fee = orig_debt_amount * 1_00 // HUNDRED_PERCENT
    assert log.keeperFee == expected_keeper_fee, f"Keeper fee should be 1%: expected {expected_keeper_fee}, actual {log.keeperFee}"
    
    # 4. Repay amount should closely match target (within 1 wei for rounding)
    assert abs(log.repayAmount - target_repay_amount) <= 1, f"Actual repay {log.repayAmount} should match target {target_repay_amount}"
    
    # 5. Collateral taken should equal repay amount / (1 - liq fee ratio)
    expected_collateral_out = log.repayAmount * HUNDRED_PERCENT // (HUNDRED_PERCENT - 11_00)
    _test(log.collateralValueOut, expected_collateral_out, 1)  # 1 wei tolerance
    
    # 6. Debt reduction should equal repay amount exactly
    debt_reduction = orig_user_debt.amount - post_user_debt.amount
    assert debt_reduction == log.repayAmount, f"Debt reduction {debt_reduction} should equal repay amount {log.repayAmount}"
    
    # 7. Collateral reduction should equal collateral taken
    collateral_reduction = orig_bt.collateralVal - post_bt.collateralVal
    assert collateral_reduction == log.collateralValueOut, f"Collateral reduction {collateral_reduction} should equal collateral taken {log.collateralValueOut}"
    
    # 8. Stability pool mechanics should be correct
    green_used = pre_green_bal - post_green_bal
    assert green_used == log.repayAmount, f"GREEN used {green_used} should equal repay amount {log.repayAmount}"
    
    # Alice should have received collateral value > GREEN given up (she profits from the liquidation)
    alice_profit = log.collateralValueOut - log.repayAmount
    expected_alice_value = alice_amount + alice_profit
    _test(user_stab_value, expected_alice_value, 1)  # 1 wei tolerance
    
    # 9. No unpaid liquidation fees (all fees covered by collateral difference)
    assert log.liqFeesUnpaid == 0, "All liquidation fees should be covered by collateral difference"
