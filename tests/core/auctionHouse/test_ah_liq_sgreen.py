from constants import EIGHTEEN_DECIMALS, HUNDRED_PERCENT
from conf_utils import clear_transient_storage, filter_logs


def _setup_105_collateral_90_debt_case(
    setGeneralConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    setAssetConfig,
    alpha_token,
    savings_green,
    mission_control,
    switchboard_alpha,
    mock_price_source,
    performDeposit,
    bob,
    alpha_token_whale,
    teller,
    should_auction_instantly,
):
    setGeneralConfig()
    setGeneralDebtConfig(
        _keeperFeeRatio=1_00,
        _minKeeperFee=EIGHTEEN_DECIMALS,
        _ltvPaybackBuffer=0,
    )
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=60_00,
        _liqThreshold=80_00,
        _liqFee=10_00,
        _borrowRate=0,
    )
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=should_auction_instantly,
    )
    setAssetConfig(
        savings_green,
        _vaultIds=[1],
        _debtTerms=createDebtTerms(0, 0, 0, 0, 0, 0),
        _shouldBurnAsPayment=True,
    )
    mission_control.setPriorityStabVaults(
        [(1, savings_green)],
        sender=switchboard_alpha.address,
    )

    mock_price_source.setPrice(alpha_token, 2 * EIGHTEEN_DECIMALS)
    performDeposit(
        bob,
        105 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
    )
    teller.borrow(90 * EIGHTEEN_DECIMALS, bob, False, sender=bob)


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
    iterator_asset, iterator_amount = stability_pool.getUserAssetAndAmountAtIndex(
        alice,
        1,
    )
    assert iterator_asset == savings_green.address
    assert iterator_amount == stability_pool.getTotalAmountForUser(
        alice,
        savings_green,
    )
    
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
    
    # 4. The keeper fee is booked before repayment, so repayment covers the
    # original debt plus the keeper debt recorded by this liquidation.
    assert log.liqFeesUnpaid == expected_keeper_fee
    assert log.repayAmount == orig_debt_amount + expected_keeper_fee
    
    # 5. Only the 10% base fee controls the Stability Pool spread.
    net_rate = HUNDRED_PERCENT - 10_00
    expected_collateral_out = (
        log.repayAmount * HUNDRED_PERCENT - 1
    ) // net_rate + 1
    assert log.collateralValueOut == expected_collateral_out
    assert log.collateralValueOut * net_rate // HUNDRED_PERCENT == log.repayAmount
    assert (
        (log.collateralValueOut - 1) * net_rate // HUNDRED_PERCENT
        < log.repayAmount
    )
    
    # 6. Debt reduction should equal original debt (all debt paid off)
    debt_reduction = orig_user_debt.amount - post_user_debt.amount
    assert debt_reduction == orig_debt_amount, f"Debt reduction {debt_reduction} should equal original debt {orig_debt_amount}"
    assert debt_reduction == log.repayAmount - log.liqFeesUnpaid
    
    # 7. Collateral reduction should equal collateral taken
    collateral_reduction = orig_bt.collateralVal - post_bt.collateralVal
    assert collateral_reduction == log.collateralValueOut, f"Collateral reduction {collateral_reduction} should equal collateral taken {log.collateralValueOut}"
    
    # 8. Stability pool mechanics should be correct
    # GREEN used must equal the repayment CreditEngine actually credits.
    green_used = pre_green_bal - post_green_bal
    _test(log.repayAmount, green_used)  # default tolerance
    
    # Alice should have received collateral value > GREEN given up (she profits from the liquidation)
    # Alice receives only the base-fee Stability spread.
    alice_profit = log.collateralValueOut - log.repayAmount
    expected_alice_value = alice_amount + alice_profit
    _test(expected_alice_value, user_stab_value)  # default tolerance
    
    # 9. The base fee is covered by collateral; the keeper fee is borrower debt.
    assert log.liqFeesUnpaid == log.keeperFee


def test_depleted_collateral_burn_is_capped_by_creditable_debt(
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
    whale,
    ledger,
):
    _setup_105_collateral_90_debt_case(
        setGeneralConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        setAssetConfig,
        alpha_token,
        savings_green,
        mission_control,
        switchboard_alpha,
        mock_price_source,
        performDeposit,
        bob,
        alpha_token_whale,
        teller,
        True,
    )

    pool_assets = 200 * EIGHTEEN_DECIMALS
    green_token.transfer(sally, pool_assets, sender=whale)
    green_token.approve(savings_green, pool_assets, sender=sally)
    pool_shares = savings_green.deposit(pool_assets, sally, sender=sally)
    savings_green.approve(teller, pool_shares, sender=sally)
    teller.deposit(
        savings_green,
        pool_shares,
        sally,
        stability_pool,
        sender=sally,
    )

    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    debt_before, terms_before, _ = credit_engine.getLatestUserDebtAndTerms(
        bob,
        False,
    )
    assert debt_before.amount == 90 * EIGHTEEN_DECIMALS
    assert terms_before.collateralVal == 105 * EIGHTEEN_DECIMALS
    assert auction_house.calcAmountOfDebtToRepayDuringLiq(bob) == (
        95 * EIGHTEEN_DECIMALS
    )

    supply_before = green_token.totalSupply()
    pool_green_before = green_token.balanceOf(savings_green)
    keeper_before = green_token.balanceOf(sally)
    teller.liquidateUser(bob, False, sender=sally)

    log = filter_logs(teller, "LiquidateUser")[0]
    debt_after, terms_after, _ = credit_engine.getLatestUserDebtAndTerms(
        bob,
        False,
    )
    pool_green_after = green_token.balanceOf(savings_green)
    gross_burn = pool_green_before - pool_green_after
    keeper_mint = green_token.balanceOf(sally) - keeper_before
    debt_reduction = debt_before.amount - debt_after.amount

    assert log.totalLiqFees == 10 * EIGHTEEN_DECIMALS
    assert log.keeperFee == EIGHTEEN_DECIMALS
    assert log.liqFeesUnpaid == log.keeperFee
    assert log.repayAmount == debt_before.amount + log.keeperFee
    assert gross_burn == log.repayAmount
    assert keeper_mint == log.keeperFee
    assert supply_before - green_token.totalSupply() == debt_reduction
    assert gross_burn == debt_reduction + keeper_mint
    assert terms_before.collateralVal - terms_after.collateralVal == (
        log.collateralValueOut
    )
    net_rate = HUNDRED_PERCENT - 10_00
    expected_collateral_out = (
        log.repayAmount * HUNDRED_PERCENT - 1
    ) // net_rate + 1
    assert log.collateralValueOut == expected_collateral_out
    assert log.collateralValueOut * net_rate // HUNDRED_PERCENT == log.repayAmount
    assert (
        (log.collateralValueOut - 1) * net_rate // HUNDRED_PERCENT
        < log.repayAmount
    )
    # liqFee is a discount rate. Its gross-up spread is intentionally larger
    # than the nominal base fee, while fee accounting credits only the base fee.
    assert log.collateralValueOut - log.repayAmount > (
        log.totalLiqFees - log.keeperFee
    )
    assert debt_after.amount == 0
    assert log.didRestoreDebtHealth
    assert log.numAuctionsStarted == 0
    assert not ledger.hasFungibleAuctions(bob)


def test_retry_stability_burn_is_capped_by_fee_free_live_debt(
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
    whale,
    ledger,
):
    _setup_105_collateral_90_debt_case(
        setGeneralConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        setAssetConfig,
        alpha_token,
        savings_green,
        mission_control,
        switchboard_alpha,
        mock_price_source,
        performDeposit,
        bob,
        alpha_token_whale,
        teller,
        False,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    assert auction_house.calcAmountOfDebtToRepayDuringLiq(bob) == (
        95 * EIGHTEEN_DECIMALS
    )

    # A borrower can permissionlessly start an economically empty episode.
    teller.liquidateUser(bob, False, sender=bob)
    first_log = filter_logs(teller, "LiquidateUser")[0]
    assert first_log.repayAmount == 0
    assert first_log.totalLiqFees == 0
    assert first_log.keeperFee == 0
    assert first_log.targetRepayAmount == 95 * EIGHTEEN_DECIMALS
    assert ledger.userDebt(bob).amount == 90 * EIGHTEEN_DECIMALS
    assert ledger.userDebt(bob).inLiquidation
    # The public helper remains a hypothetical fee-bearing risk target rather
    # than an executable retry quote.
    assert auction_house.calcAmountOfDebtToRepayDuringLiq(bob) == (
        95 * EIGHTEEN_DECIMALS
    )

    pool_assets = 200 * EIGHTEEN_DECIMALS
    green_token.transfer(sally, pool_assets, sender=whale)
    green_token.approve(savings_green, pool_assets, sender=sally)
    pool_shares = savings_green.deposit(pool_assets, sally, sender=sally)
    savings_green.approve(teller, pool_shares, sender=sally)
    teller.deposit(
        savings_green,
        pool_shares,
        sally,
        stability_pool,
        sender=sally,
    )

    debt_before = ledger.userDebt(bob).amount
    supply_before = green_token.totalSupply()
    pool_green_before = green_token.balanceOf(savings_green)
    keeper_before = green_token.balanceOf(sally)
    # Clear immediately before the retry so intervening setup cannot populate
    # transient state that would not survive a real transaction boundary.
    clear_transient_storage()
    teller.liquidateUser(bob, False, sender=sally)

    retry_log = filter_logs(teller, "LiquidateUser")[0]
    debt_after = ledger.userDebt(bob).amount
    gross_burn = pool_green_before - green_token.balanceOf(savings_green)
    debt_reduction = debt_before - debt_after

    assert retry_log.totalLiqFees == 0
    assert retry_log.liqFeesUnpaid == 0
    assert retry_log.keeperFee == 0
    assert retry_log.targetRepayAmount == 75 * EIGHTEEN_DECIMALS
    assert green_token.balanceOf(sally) == keeper_before
    assert gross_burn == retry_log.repayAmount
    assert gross_burn == debt_reduction
    assert retry_log.collateralValueOut == retry_log.repayAmount
    assert supply_before - green_token.totalSupply() == debt_reduction
    assert retry_log.didRestoreDebtHealth
    assert debt_after > 0
