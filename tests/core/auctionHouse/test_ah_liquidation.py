import pytest
import boa

from constants import EIGHTEEN_DECIMALS
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

    assert not user_debt.inLiquidation
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

    assert keeper_rewards == 0 # no rewards on right now

    # get latest debt and terms
    expected_liq_fees = 10 * EIGHTEEN_DECIMALS
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)

    assert not user_debt.inLiquidation
    assert user_debt.amount == orig_debt_amount - target_repay_amount + expected_liq_fees
    assert bt.collateralVal == orig_bt.collateralVal - target_repay_amount



def test_ah_liquidation_stab_pool_swap(
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

    assert keeper_rewards == 0 # no rewards on right now

    # get latest debt and terms
    expected_liq_fees = 10 * EIGHTEEN_DECIMALS
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)

    assert not user_debt.inLiquidation
    assert user_debt.amount == orig_debt_amount - target_repay_amount + expected_liq_fees
    assert bt.collateralVal == orig_bt.collateralVal - target_repay_amount