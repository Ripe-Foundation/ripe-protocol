import boa
import pytest

from conf_utils import filter_logs, redeem_collateral
from constants import EIGHTEEN_DECIMALS


ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"


def _raw_source(
    price=0,
    has_feed=False,
    price_mode=0,
    has_feed_mode=0,
    snapshot_mode=0,
):
    source = boa.load(
        "contracts/mock/MockRawPriceSource.vy",
        name="raw_price_source",
    )
    source.configure(
        price,
        has_feed,
        price_mode,
        has_feed_mode,
        snapshot_mode,
    )
    return source


def _isolated_price_desk(ripe_hq, deploy3r, sources):
    desk = boa.load(
        "contracts/registries/PriceDesk.vy",
        ripe_hq,
        deploy3r,
        ETH,
        1,
        2,
        name="isolated_price_desk",
    )
    for index, source in enumerate(sources, start=1):
        assert desk.startAddNewAddressToRegistry(
            source,
            f"source {index}",
            sender=deploy3r,
        )
        assert desk.confirmNewAddressToRegistry(source, sender=deploy3r) == index
    return desk


def _set_priorities(mission_control, switchboard_alpha, source_ids):
    mission_control.setPriorityPriceSourceIds(
        source_ids,
        sender=switchboard_alpha.address,
    )


def _register_sources(price_desk, governance, sources):
    for index, source in enumerate(sources, start=1):
        assert price_desk.startAddNewAddressToRegistry(
            source,
            f"isolation {index}",
            sender=governance.address,
        )
    boa.env.time_travel(blocks=price_desk.registryChangeTimeLock() + 1)
    ids = []
    for source in sources:
        ids.append(
            price_desk.confirmNewAddressToRegistry(
                source,
                sender=governance.address,
            )
        )
    return ids


def test_reverting_priority_source_falls_through_to_healthy_source(
    ripe_hq,
    deploy3r,
    alpha_token,
    mission_control,
    switchboard_alpha,
):
    failed = _raw_source(price_mode=1)
    healthy = _raw_source(2 * EIGHTEEN_DECIMALS, True)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [failed, healthy])
    _set_priorities(mission_control, switchboard_alpha, [1, 2])

    assert desk.getPrice(alpha_token, True) == 2 * EIGHTEEN_DECIMALS


def test_reverting_non_priority_source_falls_through_to_healthy_source(
    ripe_hq,
    deploy3r,
    alpha_token,
    mission_control,
    switchboard_alpha,
):
    failed = _raw_source(price_mode=1)
    healthy = _raw_source(3 * EIGHTEEN_DECIMALS, True)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [failed, healthy])
    _set_priorities(mission_control, switchboard_alpha, [])

    assert desk.getPrice(alpha_token, True) == 3 * EIGHTEEN_DECIMALS


@pytest.mark.parametrize(
    "mode",
    (2, 3, 4, 5, 6),
    ids=("empty", "short", "oversized_65", "noncanonical_bool", "oversized_96"),
)
def test_malformed_price_response_falls_through_to_healthy_source(
    mode,
    ripe_hq,
    deploy3r,
    alpha_token,
    mission_control,
    switchboard_alpha,
):
    malformed = _raw_source(99 * EIGHTEEN_DECIMALS, True, price_mode=mode)
    healthy = _raw_source(4 * EIGHTEEN_DECIMALS, True)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [malformed, healthy])
    _set_priorities(mission_control, switchboard_alpha, [1, 2])

    assert desk.getPrice(alpha_token, True) == 4 * EIGHTEEN_DECIMALS


def test_exact_canonical_response_and_primary_price_still_win(
    ripe_hq,
    deploy3r,
    alpha_token,
    mission_control,
    switchboard_alpha,
):
    primary = _raw_source(5 * EIGHTEEN_DECIMALS, True)
    fallback = _raw_source(6 * EIGHTEEN_DECIMALS, True)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [primary, fallback])
    _set_priorities(mission_control, switchboard_alpha, [1, 2])

    assert desk.getPrice(alpha_token, True) == 5 * EIGHTEEN_DECIMALS


def test_valid_zero_configured_feed_falls_through_to_healthy_source(
    ripe_hq,
    deploy3r,
    alpha_token,
    mission_control,
    switchboard_alpha,
):
    zero_feed = _raw_source(0, True)
    healthy = _raw_source(7 * EIGHTEEN_DECIMALS, True)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [zero_feed, healthy])
    _set_priorities(mission_control, switchboard_alpha, [1, 2])

    assert desk.getPrice(alpha_token, True) == 7 * EIGHTEEN_DECIMALS


def test_all_sources_failed_preserves_strict_and_non_strict_intent(
    ripe_hq,
    deploy3r,
    alpha_token,
    mission_control,
    switchboard_alpha,
):
    reverted = _raw_source(price_mode=1)
    malformed = _raw_source(price_mode=5)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [reverted, malformed])
    _set_priorities(mission_control, switchboard_alpha, [1, 2])

    assert desk.getPrice(alpha_token, False) == 0
    with boa.reverts("has price config, no price"):
        desk.getPrice(alpha_token, True)


@pytest.mark.parametrize(
    "mode",
    (1, 2, 3, 4, 5, 6),
    ids=("revert", "empty", "short", "oversized_33", "noncanonical_bool", "oversized_96"),
)
def test_malformed_has_price_feed_falls_through_to_healthy_source(
    mode,
    ripe_hq,
    deploy3r,
    alpha_token,
):
    failed = _raw_source(has_feed=True, has_feed_mode=mode)
    healthy = _raw_source(has_feed=True)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [failed, healthy])

    assert desk.hasPriceFeed(alpha_token)


@pytest.mark.parametrize(
    "mode",
    (1, 2, 3, 4, 5, 6),
    ids=("revert", "empty", "short", "oversized_33", "noncanonical_bool", "oversized_96"),
)
def test_all_failed_has_price_feed_queries_return_false(
    mode,
    ripe_hq,
    deploy3r,
    alpha_token,
):
    failed = _raw_source(has_feed=True, has_feed_mode=mode)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [failed])

    assert not desk.hasPriceFeed(alpha_token)


@pytest.mark.parametrize(
    "mode",
    (1, 2, 3, 4, 5),
    ids=("revert", "empty", "short", "oversized", "noncanonical_bool"),
)
def test_failed_snapshot_source_does_not_block_later_healthy_source(
    mode,
    ripe_hq,
    deploy3r,
    alpha_token,
    teller,
):
    failed = _raw_source(
        EIGHTEEN_DECIMALS,
        has_feed=True,
        snapshot_mode=mode,
    )
    healthy = _raw_source(EIGHTEEN_DECIMALS, has_feed=True)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [failed, healthy])

    assert desk.addPriceSnapshot(alpha_token, sender=teller.address)
    # A revert rolls back the failing source's own write. Malformed returndata
    # is observed only after a successful source call, so its write remains.
    assert failed.snapshotCount() == (0 if mode == 1 else 1)
    assert healthy.snapshotCount() == 1


def test_earlier_successful_snapshot_remains_when_later_source_fails(
    ripe_hq,
    deploy3r,
    alpha_token,
    teller,
):
    healthy = _raw_source(has_feed=True)
    failed = _raw_source(has_feed=True, snapshot_mode=1)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [healthy, failed])

    assert desk.addPriceSnapshot(alpha_token, sender=teller.address)
    assert healthy.snapshotCount() == 1
    assert failed.snapshotCount() == 0


@pytest.mark.parametrize("mode", (1, 5), ids=("revert", "noncanonical_bool"))
def test_snapshot_skips_failed_has_feed_query_and_reaches_healthy_source(
    mode,
    ripe_hq,
    deploy3r,
    alpha_token,
    teller,
):
    failed = _raw_source(has_feed=True, has_feed_mode=mode)
    healthy = _raw_source(has_feed=True)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [failed, healthy])

    assert desk.addPriceSnapshot(alpha_token, sender=teller.address)
    assert failed.snapshotCount() == 0
    assert healthy.snapshotCount() == 1


def test_failed_snapshot_source_no_longer_blocks_teller_deposit(
    price_desk,
    governance,
    alpha_token,
    alpha_token_whale,
    bob,
    simple_erc20_vault,
    teller,
    setGeneralConfig,
    setAssetConfig,
):
    failed = _raw_source(
        EIGHTEEN_DECIMALS,
        has_feed=True,
        snapshot_mode=1,
    )
    healthy = _raw_source(EIGHTEEN_DECIMALS, has_feed=True)
    _register_sources(price_desk, governance, [failed, healthy])

    setGeneralConfig()
    setAssetConfig(alpha_token)
    amount = 10 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, amount, sender=alpha_token_whale)
    alpha_token.approve(teller, amount, sender=bob)

    assert teller.deposit(
        alpha_token,
        amount,
        bob,
        simple_erc20_vault,
        sender=bob,
    ) == amount
    assert failed.snapshotCount() == 0
    assert healthy.snapshotCount() == 1


def test_healthy_fallback_restores_strict_credit_engine_repay(
    price_desk,
    governance,
    alpha_token,
    alpha_token_whale,
    bob,
    mission_control,
    switchboard_alpha,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    green_token,
    ledger,
):
    failed = _raw_source(has_feed=True, price_mode=1)
    failed_id = _register_sources(price_desk, governance, [failed])[0]
    healthy_id = price_desk.getRegId(mock_price_source)
    assert healthy_id != 0
    _set_priorities(mission_control, switchboard_alpha, [failed_id, healthy_id])

    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    performDeposit(
        bob,
        100 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
    )
    borrowed = teller.borrow(40 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    repay_amount = 10 * EIGHTEEN_DECIMALS
    green_token.approve(teller, repay_amount, sender=bob)
    assert teller.repay(repay_amount, bob, False, False, sender=bob)
    assert ledger.userDebt(bob).amount == borrowed - repay_amount


@pytest.mark.parametrize(
    "primary_failure",
    (
        pytest.param("zero", id="zero-primary"),
        pytest.param("revert", id="reverting-primary"),
    ),
)
def test_healthy_fallback_permits_strict_credit_redemption(
    primary_failure,
    price_desk,
    governance,
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
    mission_control,
    switchboard_alpha,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    green_token,
    whale,
    credit_engine,
    ledger,
    simple_erc20_vault,
    vault_book,
):
    """A bad primary does not fail the strict preflight when fallback is healthy."""
    if primary_failure == "zero":
        failed = _raw_source(has_feed=True)
    else:
        failed = _raw_source(has_feed=True, price_mode=1)
    failed_id = _register_sources(price_desk, governance, [failed])[0]
    healthy_id = price_desk.getRegId(mock_price_source)
    assert healthy_id != 0
    _set_priorities(mission_control, switchboard_alpha, [failed_id, healthy_id])

    setGeneralConfig()
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=70_00,
        _liqThreshold=80_00,
        _borrowRate=0,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    performDeposit(
        bob,
        200 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
    )
    debt = teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    mock_price_source.setPrice(alpha_token, 70 * EIGHTEEN_DECIMALS // 100)

    strict_terms = credit_engine.getUserBorrowTermsWithNumVaults(
        bob,
        ledger.numUserVaults(bob),
        True,
    )
    assert strict_terms.collateralVal == 140 * EIGHTEEN_DECIMALS
    assert credit_engine.canRedeemUserCollateral(bob)

    payment = 30 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, payment, sender=whale)
    green_token.approve(teller, payment, sender=alice)
    vault_id = vault_book.getRegId(simple_erc20_vault)

    spent = redeem_collateral(
        teller,
        bob,
        vault_id,
        alpha_token,
        payment,
        sender=alice,
    )

    assert spent == payment
    assert credit_engine.getUserDebtAmount(bob) == debt - payment
    logs = filter_logs(teller, "CollateralRedeemed")
    assert len(logs) == 1
    assert logs[0].user == bob
    assert logs[0].asset == alpha_token.address
    assert logs[0].repayValue == payment


# These two cross-module characterizations stay beside the PriceDesk isolation
# matrix because source-failure policy is their trigger. CreditEngine and
# CreditRedeem modules retain their ordinary health/redemption coverage.
def test_full_source_outage_marks_healthy_borrower_liquidatable_but_execution_fails_closed(
    price_desk,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    mission_control,
    switchboard_alpha,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    ledger,
):
    """B-AUD-004 residual: a non-strict eligibility view zero-values an outage."""
    source_id = price_desk.getRegId(mock_price_source)
    assert source_id != 0
    _set_priorities(mission_control, switchboard_alpha, [source_id])

    setGeneralConfig()
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=70_00,
        _liqThreshold=80_00,
        _borrowRate=0,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    performDeposit(
        bob,
        200 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
    )
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    assert not credit_engine.canLiquidateUser(bob)

    debt_before = ledger.userDebt(bob)
    mock_price_source.setShouldRevert(alpha_token, True)
    assert credit_engine.canLiquidateUser(bob)
    with boa.reverts("has price config, no price"):
        teller.liquidateUser(bob, False, sender=sally)
    assert ledger.userDebt(bob) == debt_before


def test_partial_source_outage_views_misclassify_but_empty_redemption_batch_rolls_back(
    price_desk,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob,
    alice,
    mission_control,
    switchboard_alpha,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    credit_redeem,
    green_token,
    whale,
    simple_erc20_vault,
    vault_book,
):
    """Views may misclassify; execution skips unsafe valuation and rolls back."""
    source_id = price_desk.getRegId(mock_price_source)
    assert source_id != 0
    _set_priorities(mission_control, switchboard_alpha, [source_id])

    setGeneralConfig()
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=70_00,
        _liqThreshold=80_00,
        _borrowRate=0,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setAssetConfig(bravo_token, _debtTerms=debt_terms)
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    performDeposit(
        bob,
        100 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
    )
    performDeposit(
        bob,
        100 * EIGHTEEN_DECIMALS,
        bravo_token,
        bravo_token_whale,
    )
    debt_before = teller.borrow(
        100 * EIGHTEEN_DECIMALS,
        bob,
        False,
        sender=bob,
    )
    assert not credit_engine.canRedeemUserCollateral(bob)

    mock_price_source.setShouldRevert(bravo_token, True)
    assert credit_engine.canRedeemUserCollateral(bob)
    assert credit_redeem.getMaxRedeemValue(bob) == debt_before

    payment = 30 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, payment, sender=whale)
    green_token.approve(teller, payment, sender=alice)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    before = (
        green_token.balanceOf(alice),
        green_token.allowance(alice, teller),
        green_token.balanceOf(credit_redeem),
        credit_engine.getUserDebtAmount(bob),
        alpha_token.balanceOf(alice),
        simple_erc20_vault.getTotalAmountForUser(bob, alpha_token),
        bravo_token.balanceOf(alice),
        simple_erc20_vault.getTotalAmountForUser(bob, bravo_token),
    )
    assert filter_logs(teller, "CollateralRedeemed") == []
    with boa.reverts("no redemptions occurred"):
        redeem_collateral(
            teller,
            bob,
            vault_id,
            alpha_token,
            payment,
            sender=alice,
        )
    assert (
        green_token.balanceOf(alice),
        green_token.allowance(alice, teller),
        green_token.balanceOf(credit_redeem),
        credit_engine.getUserDebtAmount(bob),
        alpha_token.balanceOf(alice),
        simple_erc20_vault.getTotalAmountForUser(bob, alpha_token),
        bravo_token.balanceOf(alice),
        simple_erc20_vault.getTotalAmountForUser(bob, bravo_token),
    ) == before
    assert filter_logs(teller, "CollateralRedeemed") == []
