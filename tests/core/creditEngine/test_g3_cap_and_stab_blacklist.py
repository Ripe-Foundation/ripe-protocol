"""Group 3 fix 1: post-accrual global cap. Stab-enter sGREEN blacklist is not in CreditEngine."""

import boa
import pytest

from constants import EIGHTEEN_DECIMALS, HUNDRED_PERCENT, ONE_YEAR
from conf_utils import clear_transient_storage, has_dev_reason


WRAP_CUTOFF = 10**9


def _interest(amount, rate, elapsed):
    return (amount * rate * elapsed) // (HUNDRED_PERCENT * ONE_YEAR)


def _open_rate_position(
    *,
    user,
    asset,
    asset_whale,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    first_borrow,
    global_limit,
    borrow_rate=100_00,
    deposit=400 * EIGHTEEN_DECIMALS,
):
    setGeneralConfig()
    setAssetConfig(
        asset,
        _debtTerms=createDebtTerms(
            _ltv=50_00,
            _redemptionThreshold=60_00,
            _liqThreshold=70_00,
            _liqFee=10_00,
            _borrowRate=borrow_rate,
            _daowry=0,
        ),
    )
    setGeneralDebtConfig(_globalDebtLimit=global_limit)
    mock_price_source.setPrice(asset, EIGHTEEN_DECIMALS)
    performDeposit(user, deposit, asset, asset_whale)
    clear_transient_storage()
    assert teller.borrow(first_borrow, user, False, sender=user) == first_borrow
    clear_transient_storage()


def test_zero_interest_boundary_lands_exactly_on_global_cap(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    ledger,
    credit_engine,
):
    first = 40 * EIGHTEEN_DECIMALS
    headroom = 10 * EIGHTEEN_DECIMALS
    cap = first + headroom
    _open_rate_position(
        user=bob,
        asset=alpha_token,
        asset_whale=alpha_token_whale,
        setGeneralConfig=setGeneralConfig,
        setAssetConfig=setAssetConfig,
        setGeneralDebtConfig=setGeneralDebtConfig,
        createDebtTerms=createDebtTerms,
        performDeposit=performDeposit,
        mock_price_source=mock_price_source,
        teller=teller,
        first_borrow=first,
        global_limit=cap,
        borrow_rate=0,
    )
    quote = credit_engine.getMaxBorrowAmount(bob)
    accepted = teller.borrow(headroom, bob, False, sender=bob)
    assert quote == headroom
    assert accepted == quote
    assert ledger.totalDebt() == cap


def test_exact_capacity_includes_this_call_new_interest(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    ledger,
    credit_engine,
):
    first = 40 * EIGHTEEN_DECIMALS
    remainder = 20 * EIGHTEEN_DECIMALS
    cap = 100 * EIGHTEEN_DECIMALS
    _open_rate_position(
        user=bob,
        asset=alpha_token,
        asset_whale=alpha_token_whale,
        setGeneralConfig=setGeneralConfig,
        setAssetConfig=setAssetConfig,
        setGeneralDebtConfig=setGeneralDebtConfig,
        createDebtTerms=createDebtTerms,
        performDeposit=performDeposit,
        mock_price_source=mock_price_source,
        teller=teller,
        first_borrow=first,
        global_limit=10**30,
    )
    boa.env.time_travel(seconds=ONE_YEAR)
    new_interest = _interest(
        ledger.userDebt(bob).amount,
        ledger.userDebt(bob).debtTerms.borrowRate,
        ONE_YEAR,
    )
    assert new_interest == first
    setGeneralDebtConfig(_globalDebtLimit=cap)

    quote = credit_engine.getMaxBorrowAmount(bob)
    accepted = teller.borrow(remainder, bob, False, sender=bob)
    assert quote == remainder
    assert accepted == quote
    assert ledger.totalDebt() == cap
    assert ledger.userDebt(bob).amount == first + new_interest + remainder
    assert ledger.userDebt(bob).principal == first + remainder


def test_live_total_at_or_over_cap_rejects_new_principal(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    ledger,
    credit_engine,
    green_token,
):
    first = 40 * EIGHTEEN_DECIMALS
    cap = 50 * EIGHTEEN_DECIMALS
    _open_rate_position(
        user=bob,
        asset=alpha_token,
        asset_whale=alpha_token_whale,
        setGeneralConfig=setGeneralConfig,
        setAssetConfig=setAssetConfig,
        setGeneralDebtConfig=setGeneralDebtConfig,
        createDebtTerms=createDebtTerms,
        performDeposit=performDeposit,
        mock_price_source=mock_price_source,
        teller=teller,
        first_borrow=first,
        global_limit=10**30,
    )
    boa.env.time_travel(seconds=ONE_YEAR)
    setGeneralDebtConfig(_globalDebtLimit=cap)
    supply_before = green_token.totalSupply()
    yield_before = ledger.unrealizedYield()
    assert credit_engine.getMaxBorrowAmount(bob) == 0
    with boa.reverts("global debt limit reached"):
        teller.borrow(10 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    assert ledger.totalDebt() == first
    assert ledger.userDebt(bob).amount == first
    assert ledger.unrealizedYield() == yield_before
    assert green_token.totalSupply() == supply_before


def test_second_borrower_is_blocked_after_first_fills_post_accrual_cap(
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    ledger,
    credit_engine,
):
    first = 40 * EIGHTEEN_DECIMALS
    remainder = 20 * EIGHTEEN_DECIMALS
    cap = 100 * EIGHTEEN_DECIMALS
    setGeneralConfig()
    terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=60_00,
        _liqThreshold=70_00,
        _liqFee=10_00,
        _borrowRate=100_00,
        _daowry=0,
    )
    setAssetConfig(alpha_token, _debtTerms=terms)
    setGeneralDebtConfig(_globalDebtLimit=10**30)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    performDeposit(bob, 400 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    performDeposit(sally, 400 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    clear_transient_storage()
    assert teller.borrow(first, bob, False, sender=bob) == first
    clear_transient_storage()

    boa.env.time_travel(seconds=ONE_YEAR)
    setGeneralDebtConfig(_globalDebtLimit=cap)
    assert teller.borrow(remainder, bob, False, sender=bob) == remainder
    assert ledger.totalDebt() == cap
    assert credit_engine.getMaxBorrowAmount(sally) == 0
    with boa.reverts("global debt limit reached"):
        teller.borrow(1, sally, False, sender=sally)


def _setup_stab_borrow(
    *,
    user,
    alpha_token,
    alpha_token_whale,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    savings_green,
):
    setGeneralConfig()
    setAssetConfig(alpha_token, _debtTerms=createDebtTerms(_borrowRate=0, _daowry=0))
    setAssetConfig(savings_green, [1])
    setGeneralDebtConfig()
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    performDeposit(user, 400 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    clear_transient_storage()


def test_stab_enter_credits_green_only_blacklisted_target(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    green_token,
    savings_green,
    stability_pool,
    switchboard,
):
    _setup_stab_borrow(
        user=bob,
        alpha_token=alpha_token,
        alpha_token_whale=alpha_token_whale,
        setGeneralConfig=setGeneralConfig,
        setAssetConfig=setAssetConfig,
        setGeneralDebtConfig=setGeneralDebtConfig,
        createDebtTerms=createDebtTerms,
        performDeposit=performDeposit,
        mock_price_source=mock_price_source,
        savings_green=savings_green,
    )
    green_token.setBlacklist(bob, True, sender=switchboard.address)

    with pytest.raises(boa.BoaError) as exc_info:
        teller.borrow(50 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    assert has_dev_reason(exc_info.value, "recipient blacklisted")

    amount = 50 * EIGHTEEN_DECIMALS
    accepted = teller.borrow(amount, bob, True, True, sender=bob)
    assert accepted == amount
    assert stability_pool.getTotalAmountForUser(bob, savings_green.address) == amount
    assert green_token.balanceOf(bob) == 0
    assert savings_green.balanceOf(bob) == 0


def test_stab_flag_below_cutoff_delivers_green_to_sgreen_blacklisted_target(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    green_token,
    savings_green,
    stability_pool,
    switchboard,
    ledger,
):
    _setup_stab_borrow(
        user=bob,
        alpha_token=alpha_token,
        alpha_token_whale=alpha_token_whale,
        setGeneralConfig=setGeneralConfig,
        setAssetConfig=setAssetConfig,
        setGeneralDebtConfig=setGeneralDebtConfig,
        createDebtTerms=createDebtTerms,
        performDeposit=performDeposit,
        mock_price_source=mock_price_source,
        savings_green=savings_green,
    )
    savings_green.setBlacklist(bob, True, sender=switchboard.address)

    amount = WRAP_CUTOFF
    accepted = teller.borrow(amount, bob, True, True, sender=bob)
    assert accepted == amount
    assert green_token.balanceOf(bob) == amount
    assert savings_green.balanceOf(bob) == 0
    assert stability_pool.getTotalAmountForUser(bob, savings_green.address) == 0
    assert ledger.userDebt(bob).amount == amount
