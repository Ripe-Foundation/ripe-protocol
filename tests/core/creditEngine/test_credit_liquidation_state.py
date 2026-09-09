import boa
import pytest

from constants import EIGHTEEN_DECIMALS
from conf_utils import redeem_collateral


SAFE_PRICE = 1 * EIGHTEEN_DECIMALS
REDEMPTION_PRICE = 80 * EIGHTEEN_DECIMALS // 100
LIQUIDATION_PRICE = 625 * EIGHTEEN_DECIMALS // 1000


@pytest.fixture
def liquidation_state_position(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    ledger,
    credit_engine,
    createDebtTerms,
):
    setGeneralConfig()
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=62_50,
        _liqThreshold=80_00,
        _liqFee=0,
        _borrowRate=0,
        _daowry=0,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()
    performDeposit(
        bob,
        100 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
    )
    mock_price_source.setPrice(alpha_token, SAFE_PRICE)
    assert teller.borrow(50 * EIGHTEEN_DECIMALS, bob, False, sender=bob) == (
        50 * EIGHTEEN_DECIMALS
    )
    return debt_terms


def _set_liquidation_flag(user, ledger, credit_engine, enabled):
    debt = ledger.userDebt(user)
    ledger.setUserDebt(
        user,
        (
            debt.amount,
            debt.principal,
            tuple(debt.debtTerms),
            debt.lastTimestamp,
            enabled,
        ),
        0,
        (0, 0),
        sender=credit_engine.address,
    )


def _create_auction(user, asset, ledger, auction_house):
    auction = (
        user,
        3,
        asset,
        0,
        50_00,
        boa.env.evm.patch.block_number,
        boa.env.evm.patch.block_number + 1000,
        True,
    )
    assert ledger.createNewFungibleAuction(
        auction,
        sender=auction_house.address,
    ) != 0


def _deregister_debt_asset(
    asset,
    debt_terms,
    set_asset_config,
    mission_control,
    switchboard_alpha,
):
    set_asset_config(
        asset,
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
        _debtTerms=debt_terms,
    )
    assert mission_control.deregisterAsset(
        asset,
        sender=switchboard_alpha.address,
    )
    assert not mission_control.isSupportedAsset(asset)


def _assert_new_exposure_remains_blocked(
    asset,
    asset_whale,
    user,
    teller,
    vault,
):
    fresh_amount = EIGHTEEN_DECIMALS
    asset.transfer(user, fresh_amount, sender=asset_whale)
    asset.approve(teller.address, fresh_amount, sender=user)
    wallet_before = asset.balanceOf(user)
    vault_before = vault.getTotalAmountForUser(user, asset)

    with boa.reverts("asset deposits disabled"):
        teller.deposit(asset, fresh_amount, user, vault, sender=user)
    assert asset.balanceOf(user) == wallet_before
    assert vault.getTotalAmountForUser(user, asset) == vault_before

    with boa.reverts("unsupported asset"):
        teller.borrow(EIGHTEEN_DECIMALS, user, False, sender=user)


def _deposit_green_liquidity(
    green_token,
    savings_green,
    green_holder,
    depositor,
    green_amount,
    teller,
    stability_pool,
):
    green_token.transfer(depositor, green_amount, sender=green_holder)
    green_token.approve(savings_green, green_amount, sender=depositor)
    savings_shares = savings_green.deposit(
        green_amount,
        depositor,
        sender=depositor,
    )
    savings_green.approve(teller, savings_shares, sender=depositor)
    teller.deposit(
        savings_green,
        savings_shares,
        depositor,
        stability_pool,
        0,
        sender=depositor,
    )


@pytest.mark.parametrize(
    (
        "price",
        "is_flagged",
        "has_auction",
        "expected_good_health",
        "expected_liquidatable",
        "expected_redeemable",
    ),
    (
        pytest.param(
            SAFE_PRICE,
            False,
            False,
            True,
            False,
            False,
            id="healthy-unfrozen",
        ),
        pytest.param(
            REDEMPTION_PRICE,
            False,
            False,
            False,
            False,
            True,
            id="redemption-threshold-unfrozen",
        ),
        pytest.param(
            LIQUIDATION_PRICE,
            False,
            False,
            False,
            True,
            True,
            id="liquidation-threshold-unfrozen",
        ),
        pytest.param(
            SAFE_PRICE,
            True,
            False,
            False,
            False,
            False,
            id="healthy-but-account-frozen",
        ),
        pytest.param(
            REDEMPTION_PRICE,
            True,
            False,
            False,
            False,
            False,
            id="redemption-blocked-while-frozen",
        ),
        pytest.param(
            LIQUIDATION_PRICE,
            True,
            False,
            False,
            True,
            False,
            id="frozen-without-auction-can-be-liquidated-again",
        ),
        pytest.param(
            LIQUIDATION_PRICE,
            True,
            True,
            False,
            False,
            False,
            id="active-auction-blocks-duplicate-liquidation",
        ),
    ),
)
def test_debt_health_state_matrix(
    price,
    is_flagged,
    has_auction,
    expected_good_health,
    expected_liquidatable,
    expected_redeemable,
    liquidation_state_position,
    alpha_token,
    bob,
    mock_price_source,
    ledger,
    credit_engine,
    auction_house,
):
    mock_price_source.setPrice(alpha_token, price)
    if is_flagged:
        _set_liquidation_flag(bob, ledger, credit_engine, True)
    if has_auction:
        _create_auction(bob, alpha_token, ledger, auction_house)

    assert credit_engine.hasGoodDebtHealth(bob) is expected_good_health
    assert credit_engine.canLiquidateUser(bob) is expected_liquidatable
    assert credit_engine.canRedeemUserCollateral(bob) is expected_redeemable


def test_liquidation_and_redemption_thresholds_use_exact_inclusive_boundaries(
    liquidation_state_position,
    alpha_token,
    bob,
    mock_price_source,
    credit_engine,
):
    debt = 50 * EIGHTEEN_DECIMALS
    expected_redemption_threshold = debt * 100_00 // 62_50
    expected_liquidation_threshold = debt * 100_00 // 80_00

    assert credit_engine.getRedemptionThreshold(bob) == expected_redemption_threshold
    assert credit_engine.getLiquidationThreshold(bob) == expected_liquidation_threshold

    mock_price_source.setPrice(alpha_token, REDEMPTION_PRICE + 1)
    assert not credit_engine.canRedeemUserCollateral(bob)
    mock_price_source.setPrice(alpha_token, REDEMPTION_PRICE)
    assert credit_engine.canRedeemUserCollateral(bob)

    mock_price_source.setPrice(alpha_token, LIQUIDATION_PRICE + 1)
    assert not credit_engine.canLiquidateUser(bob)
    mock_price_source.setPrice(alpha_token, LIQUIDATION_PRICE)
    assert credit_engine.canLiquidateUser(bob)


def test_deregistered_debt_position_remains_liquidatable_and_redeemable(
    liquidation_state_position,
    alpha_token,
    bob,
    mock_price_source,
    credit_engine,
    mission_control,
    switchboard_alpha,
    setAssetConfig,
):
    setAssetConfig(
        alpha_token,
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
        _debtTerms=liquidation_state_position,
    )
    assert mission_control.deregisterAsset(
        alpha_token,
        sender=switchboard_alpha.address,
    )

    mock_price_source.setPrice(alpha_token, LIQUIDATION_PRICE)
    terms = credit_engine.getUserBorrowTerms(bob, False)
    assert not terms.hasQuarantinedAsset
    assert terms.highestLtv == 100_01
    assert credit_engine.canLiquidateUser(bob)
    assert credit_engine.canRedeemUserCollateral(bob)


def test_deregistered_debt_position_executes_liquidation_without_reopening_exposure(
    liquidation_state_position,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    whale,
    green_token,
    savings_green,
    stability_pool,
    vault_book,
    setAssetConfig,
    createDebtTerms,
    mission_control,
    switchboard_alpha,
    mock_price_source,
    teller,
    credit_engine,
    simple_erc20_vault,
):
    stab_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(
        savings_green,
        _vaultIds=[1],
        _debtTerms=stab_terms,
        _shouldBurnAsPayment=True,
    )
    stab_id = vault_book.getRegId(stability_pool)
    mission_control.setPriorityStabVaults(
        [(stab_id, savings_green)],
        sender=switchboard_alpha.address,
    )
    _deposit_green_liquidity(
        green_token,
        savings_green,
        whale,
        sally,
        500 * EIGHTEEN_DECIMALS,
        teller,
        stability_pool,
    )
    _deregister_debt_asset(
        alpha_token,
        liquidation_state_position,
        setAssetConfig,
        mission_control,
        switchboard_alpha,
    )

    mock_price_source.setPrice(alpha_token, LIQUIDATION_PRICE)
    assert credit_engine.canLiquidateUser(bob)
    debt_before = credit_engine.getUserDebtAmount(bob)
    collateral_before = simple_erc20_vault.getTotalAmountForUser(
        bob,
        alpha_token,
    )
    recipient_before = alpha_token.balanceOf(stability_pool)

    teller.liquidateUser(bob, False, sender=sally)

    debt_after = credit_engine.getUserDebtAmount(bob)
    collateral_after = simple_erc20_vault.getTotalAmountForUser(
        bob,
        alpha_token,
    )
    recipient_after = alpha_token.balanceOf(stability_pool)
    assert 0 < debt_after < debt_before
    assert 0 < collateral_after < collateral_before
    assert recipient_after - recipient_before == collateral_before - collateral_after
    assert not credit_engine.canLiquidateUser(bob)
    assert not mission_control.isSupportedAsset(alpha_token)

    _assert_new_exposure_remains_blocked(
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        simple_erc20_vault,
    )


def test_deregistered_debt_position_executes_redemption_without_reopening_exposure(
    liquidation_state_position,
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
    whale,
    green_token,
    vault_book,
    setAssetConfig,
    mission_control,
    switchboard_alpha,
    mock_price_source,
    teller,
    credit_engine,
    simple_erc20_vault,
):
    _deregister_debt_asset(
        alpha_token,
        liquidation_state_position,
        setAssetConfig,
        mission_control,
        switchboard_alpha,
    )
    mock_price_source.setPrice(alpha_token, REDEMPTION_PRICE)
    assert credit_engine.canRedeemUserCollateral(bob)

    payment_amount = 10 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, payment_amount, sender=whale)
    green_token.approve(teller, payment_amount, sender=alice)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    debt_before = credit_engine.getUserDebtAmount(bob)
    collateral_before = simple_erc20_vault.getTotalAmountForUser(
        bob,
        alpha_token,
    )
    recipient_before = alpha_token.balanceOf(alice)

    spent = redeem_collateral(
        teller,
        bob,
        vault_id,
        alpha_token,
        payment_amount,
        sender=alice,
    )

    debt_after = credit_engine.getUserDebtAmount(bob)
    collateral_after = simple_erc20_vault.getTotalAmountForUser(
        bob,
        alpha_token,
    )
    delivered = alpha_token.balanceOf(alice) - recipient_before
    assert spent == payment_amount
    assert debt_before - debt_after == spent
    assert collateral_before - collateral_after == delivered
    assert delivered > 0
    assert debt_after > 0
    assert collateral_after > 0
    assert not mission_control.isSupportedAsset(alpha_token)

    _assert_new_exposure_remains_blocked(
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        simple_erc20_vault,
    )


def test_removing_last_auction_reenables_only_liquidation_check(
    liquidation_state_position,
    alpha_token,
    bob,
    mock_price_source,
    ledger,
    credit_engine,
    auction_house,
):
    mock_price_source.setPrice(alpha_token, LIQUIDATION_PRICE)
    _set_liquidation_flag(bob, ledger, credit_engine, True)
    _create_auction(bob, alpha_token, ledger, auction_house)

    assert not credit_engine.hasGoodDebtHealth(bob)
    assert not credit_engine.canLiquidateUser(bob)
    assert not credit_engine.canRedeemUserCollateral(bob)

    ledger.removeFungibleAuction(
        bob,
        3,
        alpha_token,
        sender=auction_house.address,
    )

    assert not ledger.hasFungibleAuctions(bob)
    assert not credit_engine.hasGoodDebtHealth(bob)
    assert credit_engine.canLiquidateUser(bob)
    assert not credit_engine.canRedeemUserCollateral(bob)


def test_zero_thresholds_disable_liquidation_and_redemption(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    createDebtTerms,
):
    setGeneralConfig()
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=0,
        _liqThreshold=0,
        _borrowRate=0,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()
    performDeposit(
        bob,
        100 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
    )
    mock_price_source.setPrice(alpha_token, SAFE_PRICE)
    teller.borrow(50 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    mock_price_source.setPrice(alpha_token, 0)

    assert credit_engine.getLiquidationThreshold(bob) == 0
    assert credit_engine.getRedemptionThreshold(bob) == 0
    assert not credit_engine.canLiquidateUser(bob)
    assert not credit_engine.canRedeemUserCollateral(bob)


def test_no_debt_health_results_remain_well_defined(
    bob,
    credit_engine,
):
    assert credit_engine.hasGoodDebtHealth(bob)
    assert not credit_engine.canLiquidateUser(bob)
    assert not credit_engine.canRedeemUserCollateral(bob)
    assert credit_engine.getLiquidationThreshold(bob) == 0
    assert credit_engine.getRedemptionThreshold(bob) == 0
