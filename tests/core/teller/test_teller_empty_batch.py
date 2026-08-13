import boa
import pytest

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS


def _debt_tuple(debt):
    return (
        debt.amount,
        debt.principal,
        tuple(debt.debtTerms),
        debt.lastTimestamp,
        debt.inLiquidation,
    )


def _borrow_points_tuple(points):
    return (points.lastPrincipal, points.points, points.lastUpdate)


def _deposit_points_tuple(points):
    return (points.balancePoints, points.lastBalance, points.lastUpdate)


def _asset_points_tuple(points):
    return (
        points.balancePoints,
        points.lastBalance,
        points.lastUsdValue,
        points.ripeStakerPoints,
        points.ripeVotePoints,
        points.ripeGenPoints,
        points.lastUpdate,
        points.precision,
    )


def _global_deposit_points_tuple(points):
    return (
        points.lastUsdValue,
        points.ripeStakerPoints,
        points.ripeVotePoints,
        points.ripeGenPoints,
        points.lastUpdate,
    )


def _user_state(ledger, user, vault_id, asset):
    borrow = ledger.getBorrowPointsBundle(user)
    deposit = ledger.getDepositPointsBundle(user, vault_id, asset)
    return (
        ledger.lastTouch(user),
        _debt_tuple(ledger.userDebt(user)),
        _borrow_points_tuple(borrow.userPoints),
        _borrow_points_tuple(borrow.globalPoints),
        borrow.userDebtPrincipal,
        _deposit_points_tuple(deposit.userPoints),
        _asset_points_tuple(deposit.assetPoints),
        _global_deposit_points_tuple(deposit.globalPoints),
    )


def _call_empty_batch(teller, entrypoint, user, caller):
    with boa.reverts("empty batch"):
        getattr(teller, entrypoint)(user, [], sender=caller)


def _enable_fresh_action_block(
    mission_control,
    switchboard_alpha,
    ledger,
    victim,
):
    boa.env.time_travel(blocks=1)
    action_block = boa.env.evm.patch.block_number
    assert ledger.lastTouch(victim) != action_block
    mission_control.setShouldCheckLastTouch(
        True,
        sender=switchboard_alpha.address,
    )
    assert mission_control.shouldCheckLastTouch() is True
    assert mission_control.underscoreRegistry() == ZERO_ADDRESS
    return action_block


def _set_up_position(
    victim,
    alpha_token,
    alpha_token_whale,
    setGeneralConfig,
    setAssetConfig,
    performDeposit,
):
    setGeneralConfig()
    setAssetConfig(alpha_token)
    amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(victim, amount, alpha_token, alpha_token_whale)
    return amount


@pytest.mark.parametrize("entrypoint", ("depositMany", "withdrawMany"))
def test_empty_batch_reverts_without_state_changes(
    entrypoint,
    teller,
    ledger,
    credit_engine,
    vault_book,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    mock_price_source,
    bob,
    sally,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
):
    setGeneralConfig()
    setGeneralDebtConfig()
    setRipeRewardsConfig(_arePointsEnabled=True)
    setAssetConfig(alpha_token)
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(
        bob,
        deposit_amount,
        alpha_token,
        alpha_token_whale,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    borrow_amount = 25 * EIGHTEEN_DECIMALS
    assert teller.borrow(
        borrow_amount,
        bob,
        False,
        sender=bob,
    ) == borrow_amount

    boa.env.time_travel(seconds=24 * 60 * 60)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    debt = ledger.userDebt(bob)
    borrow_points = ledger.getBorrowPointsBundle(bob)
    deposit_points = ledger.getDepositPointsBundle(bob, vault_id, alpha_token)
    assert ledger.lastTouch(bob) != 0
    assert debt.amount == debt.principal == borrow_amount
    assert debt.lastTimestamp != 0
    assert credit_engine.getUserDebtAmount(bob) > debt.amount
    assert borrow_points.userDebtPrincipal == borrow_amount
    assert (
        simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
        == deposit_amount
    )
    assert deposit_points.userPoints.lastBalance > 0
    before = _user_state(ledger, bob, vault_id, alpha_token)

    _call_empty_batch(teller, entrypoint, bob, sally)

    assert _user_state(ledger, bob, vault_id, alpha_token) == before


def test_action_block_control_rejects_legitimate_higher_risk_batch(
    teller,
    ledger,
    mission_control,
    switchboard_alpha,
    vault_book,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
):
    setGeneralConfig()
    setAssetConfig(alpha_token)
    amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, amount, sender=alpha_token_whale)
    alpha_token.approve(teller, amount, sender=bob)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    action_block = _enable_fresh_action_block(
        mission_control,
        switchboard_alpha,
        ledger,
        bob,
    )

    assert teller.depositMany(
        bob,
        [(alpha_token.address, amount, simple_erc20_vault.address, vault_id)],
        sender=bob,
    ) == 1
    assert ledger.lastTouch(bob) == action_block

    with boa.reverts("one action per block"):
        teller.withdrawMany(
            bob,
            [(alpha_token.address, amount, simple_erc20_vault.address, vault_id)],
            sender=bob,
        )


@pytest.mark.parametrize("entrypoint", ("depositMany", "withdrawMany"))
def test_empty_batch_does_not_arm_same_block_higher_risk_action(
    entrypoint,
    teller,
    ledger,
    mission_control,
    switchboard_alpha,
    vault_book,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    setGeneralConfig,
    setAssetConfig,
    performDeposit,
):
    amount = _set_up_position(
        bob,
        alpha_token,
        alpha_token_whale,
        setGeneralConfig,
        setAssetConfig,
        performDeposit,
    )
    vault_id = vault_book.getRegId(simple_erc20_vault)
    action_block = _enable_fresh_action_block(
        mission_control,
        switchboard_alpha,
        ledger,
        bob,
    )
    touch_before = ledger.lastTouch(bob)

    _call_empty_batch(teller, entrypoint, bob, sally)

    assert ledger.lastTouch(bob) == touch_before
    assert teller.withdrawMany(
        bob,
        [(alpha_token.address, amount, simple_erc20_vault.address, vault_id)],
        sender=bob,
    ) == 1
    assert ledger.lastTouch(bob) == action_block
    assert alpha_token.balanceOf(bob) == amount


@pytest.mark.parametrize("entrypoint", ("depositMany", "withdrawMany"))
def test_empty_batch_cannot_force_debt_terms_points_or_timestamp_refresh(
    entrypoint,
    teller,
    ledger,
    credit_engine,
    vault_book,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    mock_price_source,
    bob,
    sally,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    createDebtTerms,
    performDeposit,
):
    setGeneralConfig()
    setGeneralDebtConfig()
    setRipeRewardsConfig(_arePointsEnabled=True)
    original_terms = createDebtTerms(_borrowRate=5_00)
    setAssetConfig(alpha_token, _debtTerms=original_terms)
    performDeposit(
        bob,
        100 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    assert teller.borrow(
        25 * EIGHTEEN_DECIMALS,
        bob,
        False,
        sender=bob,
    ) == 25 * EIGHTEEN_DECIMALS

    refreshed_terms = createDebtTerms(_borrowRate=9_00)
    setAssetConfig(alpha_token, _debtTerms=refreshed_terms)
    boa.env.time_travel(seconds=365 * 24 * 60 * 60)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    before = _user_state(ledger, bob, vault_id, alpha_token)
    stored_debt = ledger.userDebt(bob)
    latest_debt, latest_terms, new_interest = (
        credit_engine.getLatestUserDebtAndTerms(bob, False)
    )
    assert latest_debt.amount > stored_debt.amount
    assert new_interest > 0
    assert tuple(stored_debt.debtTerms) == original_terms
    assert tuple(latest_terms.debtTerms) == refreshed_terms

    _call_empty_batch(teller, entrypoint, bob, sally)

    assert _user_state(ledger, bob, vault_id, alpha_token) == before


def test_paused_teller_error_precedes_empty_batch_error(
    teller,
    switchboard_alpha,
    bob,
    sally,
):
    teller.pause(True, sender=switchboard_alpha.address)
    assert teller.isPaused()

    with boa.reverts("contract paused"):
        teller.depositMany(bob, [], sender=sally)
    with boa.reverts("contract paused"):
        teller.withdrawMany(bob, [], sender=sally)


def test_non_empty_deposit_batch_behavior_is_unchanged(
    teller,
    ledger,
    mission_control,
    switchboard_alpha,
    vault_book,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
):
    setGeneralConfig()
    setAssetConfig(alpha_token)
    amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, amount, sender=alpha_token_whale)
    alpha_token.approve(teller, amount, sender=bob)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    action_block = _enable_fresh_action_block(
        mission_control,
        switchboard_alpha,
        ledger,
        bob,
    )

    assert teller.depositMany(
        bob,
        [(alpha_token.address, amount, simple_erc20_vault.address, vault_id)],
        sender=bob,
    ) == 1
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == amount
    assert ledger.lastTouch(bob) == action_block


def test_non_empty_withdrawal_batch_behavior_is_unchanged(
    teller,
    ledger,
    mission_control,
    switchboard_alpha,
    vault_book,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    performDeposit,
):
    amount = _set_up_position(
        bob,
        alpha_token,
        alpha_token_whale,
        setGeneralConfig,
        setAssetConfig,
        performDeposit,
    )
    vault_id = vault_book.getRegId(simple_erc20_vault)
    action_block = _enable_fresh_action_block(
        mission_control,
        switchboard_alpha,
        ledger,
        bob,
    )

    assert teller.withdrawMany(
        bob,
        [(alpha_token.address, amount, simple_erc20_vault.address, vault_id)],
        sender=bob,
    ) == 1
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0
    assert alpha_token.balanceOf(bob) == amount
    assert ledger.lastTouch(bob) == action_block
