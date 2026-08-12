import boa
import pytest

from constants import EIGHTEEN_DECIMALS


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

