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
    meaningful_low_ltv = 20_00
    _configure_mixed_ltv(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        mock_price_source,
        alpha_token,
        bravo_token,
        high_ltv,
        meaningful_low_ltv,
    )

    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, bravo_token, bravo_token_whale)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    healthy = credit_engine.getUserBorrowTerms(bob, True)
    assert healthy.lowestLtv == meaningful_low_ltv

    # Max debt is 70 (50% of 100 + 20% of 100). Drop value so 70/coll > 70%.
    mock_price_source.setPrice(alpha_token, 45 * EIGHTEEN_DECIMALS // 100)
    mock_price_source.setPrice(bravo_token, 45 * EIGHTEEN_DECIMALS // 100)
    terms = credit_engine.getUserBorrowTerms(bob, False)
    assert terms.lowestLtv == meaningful_low_ltv
    debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    expected_target = _target_repay(debt, terms.collateralVal, meaningful_low_ltv)
    high_ltv_target = _target_repay(debt, terms.collateralVal, high_ltv)
    assert expected_target != high_ltv_target

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


def test_sc26_zero_balance_registration_keeps_borrow_term_floor(
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
    """Withdraw-to-zero stays registered and still floors lowestLtv.

    Dust with a positive leftover amount is ignored (see the fail-first
    test). A fully withdrawn registration is the 2026-08-05 fail-closed
    invariant and must not be treated as dust.
    """
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
    assert terms.lowestLtv == low_ltv


def test_sc26_share_rounding_dust_does_not_set_lowest_ltv(
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob,
    alice,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    credit_engine,
    createDebtTerms,
    simple_erc20_vault,
    rebase_erc20_vault,
    vault_book,
):
    """amount == 0 with a remaining share balance is SC-26 dust, not a floor."""
    high_ltv = 50_00
    low_ltv = 10_00
    rebase_id = vault_book.getRegId(rebase_erc20_vault)
    simple_id = vault_book.getRegId(simple_erc20_vault)
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0, _keeperFeeRatio=0, _minKeeperFee=0)
    setAssetConfig(
        alpha_token,
        _vaultIds=[simple_id],
        _debtTerms=createDebtTerms(
            _ltv=high_ltv,
            _redemptionThreshold=70_00,
            _liqThreshold=80_00,
            _liqFee=0,
            _borrowRate=0,
        ),
    )
    setAssetConfig(
        bravo_token,
        _vaultIds=[rebase_id],
        _debtTerms=createDebtTerms(
            _ltv=low_ltv,
            _redemptionThreshold=70_00,
            _liqThreshold=80_00,
            _liqFee=0,
            _borrowRate=0,
        ),
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)

    meaningful = 100 * EIGHTEEN_DECIMALS
    performDeposit(alice, meaningful, bravo_token, bravo_token_whale, rebase_erc20_vault)
    performDeposit(bob, meaningful, alpha_token, alpha_token_whale, simple_erc20_vault)
    performDeposit(bob, 1, bravo_token, bravo_token_whale, rebase_erc20_vault)

    # Leave 1 wei in the rebase vault so bob's leftover shares convert to 0
    # while alice keeps the vault non-empty and bob still has a share balance.
    leftover = 1
    drain = bravo_token.balanceOf(rebase_erc20_vault) - leftover
    bravo_token.transfer(bravo_token_whale, drain, sender=rebase_erc20_vault.address)

    bravo_index = rebase_erc20_vault.indexOfUserAsset(bob, bravo_token)
    dust_asset, dust_amount = rebase_erc20_vault.getUserAssetAndAmountAtIndex(bob, bravo_index)
    assert dust_asset == bravo_token.address
    assert dust_amount == 0
    assert rebase_erc20_vault.doesUserHaveBalance(bob, bravo_token)
    assert rebase_erc20_vault.getTotalAmountForVault(bravo_token) == leftover

    terms = credit_engine.getUserBorrowTerms(bob, True)
    assert not terms.hasQuarantinedAsset
    assert terms.lowestLtv == high_ltv
    assert terms.lowestLtv != low_ltv
    assert terms.collateralVal == meaningful
    assert terms.totalMaxDebt == meaningful * high_ltv // HUNDRED_PERCENT


def test_sc26_consumers_follow_share_rounding_lowest_ltv(
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
    simple_erc20_vault,
    rebase_erc20_vault,
    vault_book,
    createDebtTerms,
):
    """Share-rounding dust must not change liquidation, redeem, or deleverage targets."""
    high_ltv = 50_00
    low_ltv = 10_00
    rebase_id = vault_book.getRegId(rebase_erc20_vault)
    simple_id = vault_book.getRegId(simple_erc20_vault)
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0, _keeperFeeRatio=0, _minKeeperFee=0)
    setAssetConfig(
        alpha_token,
        _vaultIds=[simple_id],
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
        _vaultIds=[rebase_id],
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

    meaningful = 100 * EIGHTEEN_DECIMALS
    performDeposit(alice, meaningful, bravo_token, bravo_token_whale, rebase_erc20_vault)
    performDeposit(bob, meaningful, alpha_token, alpha_token_whale, simple_erc20_vault)
    performDeposit(bob, 1, bravo_token, bravo_token_whale, rebase_erc20_vault)
    leftover = 1
    drain = bravo_token.balanceOf(rebase_erc20_vault) - leftover
    bravo_token.transfer(bravo_token_whale, drain, sender=rebase_erc20_vault.address)
    assert rebase_erc20_vault.getUserAssetAndAmountAtIndex(
        bob,
        rebase_erc20_vault.indexOfUserAsset(bob, bravo_token),
    ) == (bravo_token.address, 0)
    assert rebase_erc20_vault.doesUserHaveBalance(bob, bravo_token)

    teller.borrow(50 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    mock_price_source.setPrice(alpha_token, 60 * EIGHTEEN_DECIMALS // 100)
    mock_price_source.setPrice(bravo_token, 60 * EIGHTEEN_DECIMALS // 100)

    terms = credit_engine.getUserBorrowTerms(bob, False)
    assert terms.lowestLtv == high_ltv
    debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    expected = auction_house.calcTargetRepayAmount(debt, terms.collateralVal, high_ltv)
    dust_expected = auction_house.calcTargetRepayAmount(debt, terms.collateralVal, low_ltv)
    assert expected != dust_expected
    assert credit_redeem.getMaxRedeemValue(bob) == expected
    assert deleverage.getMaxDeleverageAmount(bob) == expected
    assert credit_engine.canLiquidateUser(bob)

    teller.liquidateUser(bob, False, sender=sally)
    liq_log = filter_logs(teller, "LiquidateUser")[0]
    assert liq_log.targetRepayAmount == expected
    assert liq_log.targetRepayAmount != dust_expected
