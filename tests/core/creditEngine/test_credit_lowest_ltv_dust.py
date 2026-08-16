import boa

from constants import EIGHTEEN_DECIMALS, HUNDRED_PERCENT
from conf_utils import filter_logs, redeem_collateral


def _target_repay(debt_amount, collateral_value, target_ltv):
    coll_adjusted = collateral_value * target_ltv // HUNDRED_PERCENT
    if debt_amount <= coll_adjusted:
        return debt_amount
    return min(
        (debt_amount - coll_adjusted) * HUNDRED_PERCENT // (HUNDRED_PERCENT - target_ltv),
        debt_amount,
    )


def _configure_mixed_ltv(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    mock_price_source,
    alpha_token,
    bravo_token,
    high_ltv=50_00,
    low_ltv=10_00,
):
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0, _keeperFeeRatio=0, _minKeeperFee=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=createDebtTerms(
            _ltv=high_ltv,
            _redemptionThreshold=70_00,
            _liqThreshold=80_00,
            _liqFee=0,
            _borrowRate=0,
        ),
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=True,
        _shouldTransferToEndaoment=False,
        _shouldBurnAsPayment=False,
    )
    setAssetConfig(
        bravo_token,
        _debtTerms=createDebtTerms(
            _ltv=low_ltv,
            _redemptionThreshold=70_00,
            _liqThreshold=80_00,
            _liqFee=0,
            _borrowRate=0,
        ),
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=True,
        _shouldTransferToEndaoment=True,
        _shouldBurnAsPayment=False,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)


def test_sc26_fail_first_dust_no_longer_sets_lowest_ltv(
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    credit_engine,
    createDebtTerms,
):
    high_ltv = 50_00
    low_ltv = 10_00
    _configure_mixed_ltv(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        mock_price_source,
        alpha_token,
        bravo_token,
        high_ltv,
        low_ltv,
    )

    meaningful = 100 * EIGHTEEN_DECIMALS
    dust = 1
    performDeposit(bob, meaningful, alpha_token, alpha_token_whale)
    performDeposit(bob, dust, bravo_token, bravo_token_whale)

    terms = credit_engine.getUserBorrowTerms(bob, True)
    dust_usd = terms.collateralVal - meaningful
    assert dust_usd < HUNDRED_PERCENT
    dust_max_debt = dust_usd * low_ltv // HUNDRED_PERCENT
    assert dust_max_debt == 0
    # Pre-fix: lowestLtv would follow the dust asset.
    pre_fix_lowest_ltv = min(high_ltv, low_ltv)
    assert pre_fix_lowest_ltv == low_ltv
    assert terms.lowestLtv == high_ltv
    assert terms.lowestLtv != pre_fix_lowest_ltv
    assert terms.totalMaxDebt == meaningful * high_ltv // HUNDRED_PERCENT


def test_sc26_zero_capacity_ignored_nonzero_capacity_participates(
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    credit_engine,
    createDebtTerms,
):
    high_ltv = 50_00
    low_ltv = 10_00
    _configure_mixed_ltv(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        mock_price_source,
        alpha_token,
        bravo_token,
        high_ltv,
        low_ltv,
    )

    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    performDeposit(bob, 9, bravo_token, bravo_token_whale)
    zero_terms = credit_engine.getUserBorrowTerms(bob, True)
    assert 9 * low_ltv // HUNDRED_PERCENT == 0
    assert zero_terms.lowestLtv == high_ltv

    performDeposit(bob, 1, bravo_token, bravo_token_whale)
    live_terms = credit_engine.getUserBorrowTerms(bob, True)
    assert 10 * low_ltv // HUNDRED_PERCENT == 1
    assert live_terms.lowestLtv == low_ltv


def test_sc26_all_zero_capacity_portfolio_is_defined(
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    credit_engine,
    createDebtTerms,
):
    _configure_mixed_ltv(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        mock_price_source,
        alpha_token,
        bravo_token,
    )
    performDeposit(bob, 1, alpha_token, alpha_token_whale)
    performDeposit(bob, 1, bravo_token, bravo_token_whale)

    terms = credit_engine.getUserBorrowTerms(bob, True)
    assert terms.totalMaxDebt == 0
    assert terms.lowestLtv == 0
    assert terms.lowestLtv != 2 ** 256 - 1
    assert terms.debtTerms.ltv >= 0
    assert terms.collateralVal > 0


def test_sc26_missing_price_still_quarantines(
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    credit_engine,
    createDebtTerms,
):
    _configure_mixed_ltv(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        mock_price_source,
        alpha_token,
        bravo_token,
    )
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, bravo_token, bravo_token_whale)
    mock_price_source.setPrice(bravo_token, 0)

    terms = credit_engine.getUserBorrowTerms(bob, False)
    assert terms.hasQuarantinedAsset
    with boa.reverts("has price config, no price"):
        credit_engine.getUserBorrowTerms(bob, True)


def test_sc26_consumers_follow_meaningful_lowest_ltv(
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob,
    alice,
    sally,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    credit_engine,
    credit_redeem,
    deleverage,
    auction_house,
    teller,
    green_token,
    whale,
    simple_erc20_vault,
    vault_book,
    createDebtTerms,
):
    high_ltv = 50_00
    dust_low_ltv = 10_00
    _configure_mixed_ltv(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        mock_price_source,
        alpha_token,
        bravo_token,
        high_ltv,
        dust_low_ltv,
    )

    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    performDeposit(bob, 1, bravo_token, bravo_token_whale)
    teller.borrow(50 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    healthy = credit_engine.getUserBorrowTerms(bob, True)
    assert healthy.lowestLtv == high_ltv

    # The 1-wei low-LTV position has zero borrowing capacity. Drop the meaningful
    # collateral so each unwind consumer must use the high-LTV target.
    mock_price_source.setPrice(alpha_token, 60 * EIGHTEEN_DECIMALS // 100)
    mock_price_source.setPrice(bravo_token, 60 * EIGHTEEN_DECIMALS // 100)
    terms = credit_engine.getUserBorrowTerms(bob, False)
    assert terms.lowestLtv == high_ltv
    debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    expected_target = _target_repay(debt, terms.collateralVal, high_ltv)
    dust_target = _target_repay(debt, terms.collateralVal, dust_low_ltv)
    assert expected_target != dust_target

    assert credit_redeem.getMaxRedeemValue(bob) == expected_target
    assert deleverage.getMaxDeleverageAmount(bob) == expected_target
    assert auction_house.calcTargetRepayAmount(
        debt,
        terms.collateralVal,
        terms.lowestLtv,
    ) == expected_target

    payment = 10 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, payment, sender=whale)
    green_token.approve(teller, payment, sender=alice)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    redeemed = redeem_collateral(
        teller,
        bob,
        vault_id,
        alpha_token,
        payment,
        sender=alice,
    )
    assert redeemed == payment
    assert payment < expected_target


def test_sc26_liquidation_target_uses_meaningful_not_dust_ltv(
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob,
    sally,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    credit_engine,
    auction_house,
    teller,
    createDebtTerms,
):
    high_ltv = 50_00
    low_ltv = 10_00
    _configure_mixed_ltv(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        mock_price_source,
        alpha_token,
        bravo_token,
        high_ltv,
        low_ltv,
    )

    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    performDeposit(bob, 1, bravo_token, bravo_token_whale)
    teller.borrow(50 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    mock_price_source.setPrice(alpha_token, 60 * EIGHTEEN_DECIMALS // 100)
    mock_price_source.setPrice(bravo_token, 60 * EIGHTEEN_DECIMALS // 100)
    terms = credit_engine.getUserBorrowTerms(bob, False)
    assert terms.lowestLtv == high_ltv
    debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    expected = auction_house.calcTargetRepayAmount(debt, terms.collateralVal, high_ltv)
    dust_expected = auction_house.calcTargetRepayAmount(debt, terms.collateralVal, low_ltv)
    assert expected != dust_expected
    assert credit_engine.canLiquidateUser(bob)

    teller.liquidateUser(bob, False, sender=sally)
    liq_log = filter_logs(teller, "LiquidateUser")[0]
    assert liq_log.targetRepayAmount == expected
    assert liq_log.targetRepayAmount != dust_expected


def test_sc26_zero_balance_registration_has_no_borrow_capacity(
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    createDebtTerms,
    simple_erc20_vault,
):
    """A retained registration without capacity cannot set lowestLtv."""
    high_ltv = 50_00
    low_ltv = 10_00
    _configure_mixed_ltv(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        mock_price_source,
        alpha_token,
        bravo_token,
        high_ltv,
        low_ltv,
    )

    amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, amount, alpha_token, alpha_token_whale)
    performDeposit(bob, amount, bravo_token, bravo_token_whale)
    assert teller.withdraw(
        bravo_token,
        amount,
        bob,
        simple_erc20_vault,
        sender=bob,
    ) == amount
    assert simple_erc20_vault.getUserAssetAndAmountAtIndex(bob, 2) == (
        bravo_token.address,
        0,
    )

    terms = credit_engine.getUserBorrowTerms(bob, True)
    assert terms.collateralVal == amount
    assert terms.totalMaxDebt == amount * high_ltv // HUNDRED_PERCENT
    assert terms.lowestLtv == high_ltv


def test_sc26_intentional_zero_ltv_asset_remains_excluded(
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    credit_engine,
    createDebtTerms,
):
    high_ltv = 50_00
    _configure_mixed_ltv(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        mock_price_source,
        alpha_token,
        bravo_token,
        high_ltv,
        0,
    )
    amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, amount, alpha_token, alpha_token_whale)
    performDeposit(bob, amount, bravo_token, bravo_token_whale)
    mock_price_source.setPrice(bravo_token, 0)

    terms = credit_engine.getUserBorrowTerms(bob, True)
    assert terms.lowestLtv == high_ltv
    assert terms.collateralVal == amount
    assert not terms.hasQuarantinedAsset
