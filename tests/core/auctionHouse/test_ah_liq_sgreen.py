
from constants import EIGHTEEN_DECIMALS


def test_ah_liquidation_phase_1_pay_via_stab_pool(
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
):
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0) # no payback buffer

    # alpha token config
    debt_terms = createDebtTerms(
        _ltv = 50_00,
        _redemptionThreshold = 60_00,
        _liqThreshold = 70_00,
        _liqFee = 10_00,
        _borrowRate = 5_00,
    )
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=False,
    )
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # stab pool config
    stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(savings_green, _vaultIds=[1], _debtTerms=stab_debt_terms, _shouldBurnAsPayment=True)
    mission_control.setPriorityStabVaults([(1, savings_green)], sender=switchboard_alpha.address)

    # user depotit + borrow
    deposit_amount = 1_000 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    orig_debt_amount = 500 * EIGHTEEN_DECIMALS
    teller.borrow(orig_debt_amount, bob, True, sender=bob)

    # deposit into stab pool
    pre_savings_bal = savings_green.balanceOf(bob)
    savings_green.approve(teller, pre_savings_bal, sender=bob)
    teller.deposit(savings_green, pre_savings_bal, bob, stability_pool, sender=bob)
    assert stability_pool.getTotalAmountForUser(bob, savings_green) == pre_savings_bal

    # test underlying balance
    pre_green_underlying_bal = savings_green.convertToAssets(pre_savings_bal)
    _test(orig_debt_amount, pre_green_underlying_bal)

    # set liquidatable price
    new_price = int(0.6 * EIGHTEEN_DECIMALS) # 60% of original price
    mock_price_source.setPrice(alpha_token, new_price)
    assert credit_engine.canLiquidateUser(bob)

    # pre liquidation
    orig_user_debt, orig_bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    _test(orig_user_debt.amount, orig_debt_amount)
    _test(orig_bt.collateralVal, 600 * EIGHTEEN_DECIMALS)
    
    target_repay_amount = auction_house.calcAmountOfDebtToRepayDuringLiq(bob)
    _test(target_repay_amount, 450 * EIGHTEEN_DECIMALS)

    pre_green_bal = green_token.balanceOf(savings_green)
    _test(pre_green_bal, orig_debt_amount)

    # liquidate user
    teller.liquidateUser(bob, False, sender=sally)

    post_savings_bal = stability_pool.getTotalAmountForUser(bob, savings_green)
    _test(post_savings_bal, pre_savings_bal // 10) # 1/10 taken from stab pool

    # get latest debt and terms
    post_user_debt, post_bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    _test(post_user_debt.amount, orig_user_debt.amount - target_repay_amount + 50 * EIGHTEEN_DECIMALS) # liq fee
    _test(post_bt.collateralVal, orig_bt.collateralVal) # same

    post_green_bal = green_token.balanceOf(savings_green)
    _test(post_green_bal, pre_green_bal - target_repay_amount)
    green_underlying_bal = savings_green.convertToAssets(post_savings_bal)
    _test(green_underlying_bal, pre_green_underlying_bal // 10)
