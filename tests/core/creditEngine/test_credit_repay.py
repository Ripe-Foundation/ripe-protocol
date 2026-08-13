import boa
import pytest

from constants import EIGHTEEN_DECIMALS, MAX_UINT256
from conf_utils import filter_logs, get_boa_dev_reasons


def test_basic_repay(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    credit_engine,
    teller,
    green_token,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()

    # deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # set mock prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # borrow
    borrow_amount = teller.borrow(MAX_UINT256, bob, False, sender=bob)
    assert borrow_amount == 50 * EIGHTEEN_DECIMALS

    # repay
    repay_amount = 25 * EIGHTEEN_DECIMALS
    assert green_token.approve(teller, repay_amount, sender=bob)
    assert teller.repay(repay_amount, bob, False, False, sender=bob)

    log = filter_logs(teller, "RepayDebt")[0]
    assert log.user == bob
    assert log.repayValue == repay_amount
    assert log.repayType == 1
    assert log.refundAmount == 0
    assert not log.refundWasSavingsGreen
    assert log.outstandingUserDebt == borrow_amount - repay_amount
    assert log.userCollateralVal == 100 * EIGHTEEN_DECIMALS
    assert log.maxUserDebt == 50 * EIGHTEEN_DECIMALS
    assert log.hasGoodDebtHealth

    # check balance
    assert green_token.balanceOf(bob) == borrow_amount - repay_amount
    assert green_token.balanceOf(credit_engine) == 0


def test_repay_low_risk_succeeds_between_checked_actions_and_rearms_guard(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    green_token,
    ledger,
    mission_control,
    switchboard_alpha,
):
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()
    performDeposit(
        bob,
        100 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
    )
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    mission_control.setShouldCheckLastTouch(
        True,
        sender=switchboard_alpha.address,
    )
    boa.env.time_travel(blocks=1)

    teller.borrow(20 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    repay_amount = 5 * EIGHTEEN_DECIMALS
    green_token.approve(teller, repay_amount, sender=bob)
    assert teller.repay(repay_amount, bob, False, False, sender=bob)

    debt = ledger.userDebt(bob).amount
    touch = ledger.lastTouch(bob)
    with boa.reverts("one action per block"):
        teller.borrow(1 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    assert ledger.userDebt(bob).amount == debt
    assert ledger.lastTouch(bob) == touch


def test_repay_zero_amount(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()

    # deposit and borrow
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    teller.borrow(MAX_UINT256, bob, False, sender=bob)

    # attempt to repay zero amount
    with boa.reverts("cannot transfer 0 amount"):
        teller.repay(0, bob, False, sender=bob)


def test_repay_max_amount(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    green_token,
    ledger,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()

    # deposit and borrow
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    teller.borrow(MAX_UINT256, bob, False, sender=bob)

    # max repay
    green_token.approve(teller, MAX_UINT256, sender=bob)
    teller.repay(MAX_UINT256, bob, False, sender=bob)

    assert ledger.userDebt(bob).amount == 0


def test_repay_no_debt(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    green_token,
    whale,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()

    # deposit but don't borrow
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # transfer green token to bob
    repay_amount = 25 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, repay_amount, sender=whale)

    # attempt to repay
    green_token.approve(teller, repay_amount, sender=bob)
    with boa.reverts("no debt outstanding"):
        teller.repay(repay_amount, bob, False, sender=bob)


def test_repay_protocol_paused(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    green_token,
    switchboard_alpha,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()

    # deposit and borrow
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    teller.borrow(MAX_UINT256, bob, False, sender=bob)

    # pause protocol
    teller.pause(True, sender=switchboard_alpha.address)
    assert teller.isPaused()

    # attempt to repay
    repay_amount = 25 * EIGHTEEN_DECIMALS
    green_token.approve(teller, repay_amount, sender=bob)
    with boa.reverts("contract paused"):
        teller.repay(repay_amount, bob, False, sender=bob)

    # unpause and try again
    teller.pause(False, sender=switchboard_alpha.address)
    assert teller.repay(repay_amount, bob, False, sender=bob)


def test_repay_unauthorized_sender(
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    green_token,
    setUserConfig,
    whale,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()

    # deposit and borrow
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    teller.borrow(MAX_UINT256, bob, False, sender=bob)

    # attempt to repay as unauthorized sender
    repay_amount = 25 * EIGHTEEN_DECIMALS
    green_token.transfer(sally, repay_amount, sender=whale)

    green_token.approve(teller, repay_amount, sender=sally)
    with boa.reverts("not allowed to repay for user"):
        teller.repay(repay_amount, bob, False, sender=sally)

    # success
    setUserConfig(bob, _canAnyoneRepayDebt=True)
    teller.repay(repay_amount, bob, False, sender=sally)


def test_repay_with_interest(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    green_token,
    ledger,
    credit_engine,
    createDebtTerms,
):
    # basic setup with high interest rate
    setGeneralConfig()
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=60_00,
        _liqThreshold=70_00,
        _liqFee=10_00,
        _borrowRate=100_00,  # 100% annual interest
        _daowry=1_00,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    # deposit and borrow
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    borrow_amount = teller.borrow(MAX_UINT256, bob, False, sender=bob)

    # time_travel forward by 1 year (31536000 seconds)
    boa.env.time_travel(seconds=31536000)

    # update debt to accrue interest
    credit_engine.updateDebtForUser(bob, sender=credit_engine.address)

    # verify interest accrued
    user_debt = ledger.userDebt(bob)
    assert user_debt.amount == borrow_amount * 2  # 100% interest

    # repay half the total debt
    repay_amount = borrow_amount
    green_token.approve(teller, repay_amount, sender=bob)
    assert teller.repay(repay_amount, bob, False, sender=bob)

    # verify remaining debt
    user_debt = ledger.userDebt(bob)
    assert user_debt.amount == borrow_amount  # original amount remains


def test_repay_with_savings_green_refund(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    green_token,
    savings_green,
    whale,
    ledger,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()

    # deposit and borrow
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    borrow_amount = teller.borrow(MAX_UINT256, bob, True, sender=bob)  # borrow savings_green

    # give bob 2x amount
    green_token.transfer(bob, borrow_amount, sender=whale)
    green_token.approve(teller, MAX_UINT256, sender=bob)
    assert teller.repay(MAX_UINT256, bob, False, True, sender=bob)

    assert ledger.userDebt(bob).amount == 0

    # verify balances
    assert savings_green.balanceOf(bob) != 0
    assert green_token.balanceOf(bob) == 0


def test_repay_updates_ledger_state(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    green_token,
    ledger,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()

    # deposit and borrow
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    borrow_amount = teller.borrow(MAX_UINT256, bob, False, sender=bob)

    # verify initial state
    assert ledger.totalDebt() == borrow_amount
    assert ledger.isBorrower(bob)
    assert ledger.indexOfBorrower(bob) == 1

    # repay
    repay_amount = borrow_amount  # full repay
    green_token.approve(teller, repay_amount, sender=bob)
    assert teller.repay(repay_amount, bob, False, sender=bob)

    assert ledger.userDebt(bob).amount == 0

    # verify ledger state
    assert ledger.totalDebt() == 0
    assert not ledger.isBorrower(bob)
    assert ledger.indexOfBorrower(bob) == 0
    assert ledger.getNumBorrowers() == 0
    assert ledger.numBorrowers() == 1  # array still has one element (zero address)


def test_repay_reduce_debt_amount(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    green_token,
    ledger,
    credit_engine,
    createDebtTerms,
    whale,
):
    # basic setup with high interest rate
    setGeneralConfig()
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=60_00,
        _liqThreshold=70_00,
        _liqFee=10_00,
        _borrowRate=100_00,  # 100% annual interest
        _daowry=1_00,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    # deposit and borrow
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    borrow_amount = teller.borrow(MAX_UINT256, bob, False, sender=bob)

    # time_travel forward by 1 year (31536000 seconds)
    boa.env.time_travel(seconds=31536000)

    # update debt to accrue interest
    credit_engine.updateDebtForUser(bob, sender=credit_engine.address)

    # verify initial state
    user_debt = ledger.userDebt(bob)
    assert user_debt.amount == borrow_amount * 2  # 100% interest
    assert user_debt.principal == borrow_amount

    # make sure bob has funds
    green_token.transfer(bob, borrow_amount * 4, sender=whale)

    # Case 1: Repay only interest
    interest_amount = borrow_amount
    green_token.approve(teller, interest_amount, sender=bob)
    assert teller.repay(interest_amount, bob, False, sender=bob)

    # verify state after interest-only repay
    user_debt = ledger.userDebt(bob)
    assert user_debt.amount == borrow_amount  # only principal remains
    assert user_debt.principal == borrow_amount  # principal unchanged

    # time_travel forward by another year
    boa.env.time_travel(seconds=31536000)
    credit_engine.updateDebtForUser(bob, sender=credit_engine.address)

    # Case 2: Repay partial interest and partial principal
    # At this point:
    # - Principal = borrow_amount
    # - Interest = borrow_amount (100% of principal)
    # - Total debt = borrow_amount * 2
    repay_amount = borrow_amount * 3 // 2  # 75% of total debt
    green_token.approve(teller, repay_amount, sender=bob)
    assert teller.repay(repay_amount, bob, False, sender=bob)

    # verify state after partial repay
    user_debt = ledger.userDebt(bob)
    assert user_debt.amount == borrow_amount // 2  # 25% of total debt remains
    assert user_debt.principal == borrow_amount // 2  # principal reduced by 50%


#############
# Alt Repay #
#############


def test_repay_during_liquidation(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    credit_engine,
    ledger,
    createDebtTerms,
    auction_house,
):
    # basic setup
    setGeneralConfig()
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=60_00,
        _liqThreshold=70_00,
        _liqFee=10_00,
        _borrowRate=5_00,
        _daowry=1_00,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    # deposit and borrow
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    borrow_amount = 50 * EIGHTEEN_DECIMALS

    # set user in liquidation
    user_debt = (borrow_amount, borrow_amount, debt_terms, boa.env.evm.patch.timestamp, True)

    # repay during liquidation
    repay_value = borrow_amount // 2
    assert credit_engine.repayFromDept(bob, user_debt, repay_value, 0, 0, sender=auction_house.address)

    # verify debt is cleared
    assert ledger.userDebt(bob).amount == borrow_amount - repay_value
    assert not ledger.isUserInLiquidation(bob)


def test_repay_during_auction_purchase(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    credit_engine,
    ledger,
    createDebtTerms,
    auction_house,
    green_token,
    whale,
):
    # basic setup
    setGeneralConfig()
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=60_00,
        _liqThreshold=70_00,
        _liqFee=10_00,
        _borrowRate=5_00,
        _daowry=1_00,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    # deposit and borrow
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    borrow_amount = 50 * EIGHTEEN_DECIMALS

    # set user in liquidation
    user_debt = (borrow_amount, borrow_amount, debt_terms, boa.env.evm.patch.timestamp, True)
    ledger.setUserDebt(bob, user_debt, 0, (0, 0), sender=credit_engine.address)
    assert ledger.isUserInLiquidation(bob)

    # move green to contract
    repay_amount = borrow_amount
    green_token.transfer(credit_engine, repay_amount, sender=whale)

    # repay during auction purchase
    credit_engine.repayDuringAuctionPurchase(bob, repay_amount, sender=auction_house.address)

    # verify debt is cleared
    assert ledger.userDebt(bob).amount == 0
    assert not ledger.isUserInLiquidation(bob)


def test_repay_during_auction_purchase_partial(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    credit_engine,
    ledger,
    createDebtTerms,
    auction_house,
    green_token,
    whale,
):
    # basic setup
    setGeneralConfig()
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=60_00,
        _liqThreshold=70_00,
        _liqFee=10_00,
        _borrowRate=5_00,
        _daowry=1_00,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    # deposit and borrow
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    borrow_amount = 50 * EIGHTEEN_DECIMALS

    # set user in liquidation
    user_debt = (borrow_amount, borrow_amount, debt_terms, boa.env.evm.patch.timestamp, True)
    ledger.setUserDebt(bob, user_debt, 0, (0, 0), sender=credit_engine.address)
    assert ledger.isUserInLiquidation(bob)

    # repay partial amount during auction purchase
    repay_amount = borrow_amount // 2
    green_token.transfer(credit_engine, repay_amount, sender=whale)
    assert credit_engine.repayDuringAuctionPurchase(bob, repay_amount, sender=auction_house.address)

    # verify remaining debt
    assert ledger.userDebt(bob).amount == borrow_amount - repay_amount
    assert not ledger.isUserInLiquidation(bob) # healthy ratios


def test_repay_during_liquidation_unauthorized(
    bob,
    credit_engine,
    createDebtTerms,
):
    debt_terms = createDebtTerms()
    user_debt = (0, 0, debt_terms, 0, True)

    # attempt to repay during liquidation as unauthorized sender
    with boa.reverts("not allowed"):
        credit_engine.repayFromDept(bob, user_debt, 10 * EIGHTEEN_DECIMALS, 0, 0, sender=bob)


def test_repay_during_auction_purchase_unauthorized(
    bob,
    credit_engine,
):
    # attempt to repay during auction purchase as unauthorized sender
    with boa.reverts("only auction house allowed"):
        credit_engine.repayDuringAuctionPurchase(bob, 10 * EIGHTEEN_DECIMALS, sender=bob)


def test_repay_with_savings_green_payment(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    green_token,
    savings_green,
    ledger,
    credit_engine,
    _test,
):
    """Test repaying debt using Savings Green tokens instead of Green tokens"""
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()

    # deposit and borrow
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    borrow_amount = teller.borrow(MAX_UINT256, bob, False, sender=bob)
    assert borrow_amount == 50 * EIGHTEEN_DECIMALS

    # deposit green tokens into savings green to get savings green tokens
    green_token.approve(savings_green, borrow_amount, sender=bob)
    shares = savings_green.deposit(borrow_amount, bob, sender=bob)
    
    # verify bob has savings green tokens
    assert savings_green.balanceOf(bob) == shares
    _test(borrow_amount, savings_green.convertToAssets(shares))

    # record initial debt
    initial_debt = ledger.userDebt(bob).amount
    assert initial_debt == borrow_amount

    # approve teller to spend savings green tokens
    repay_amount = shares // 2
    savings_green.approve(teller, MAX_UINT256, sender=bob)
    
    # repay using savings green tokens
    assert teller.repay(
        repay_amount, 
        bob, 
        True,   # _isPaymentSavingsGreen - this is the key parameter
        False,  # _shouldRefundSavingsGreen
        sender=bob
    )

    # verify debt was reduced
    remaining_debt = ledger.userDebt(bob).amount
    _test(remaining_debt, initial_debt // 2)

    # verify savings green tokens were used
    # The teller should have redeemed the exact amount needed
    _test(savings_green.balanceOf(bob), shares // 2)

    # verify green tokens were sent to credit engine
    assert green_token.balanceOf(credit_engine) == 0  # credit engine burns them immediately


def test_teller_savings_green_payment_control_boundaries_are_atomic(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    green_token,
    savings_green,
    ledger,
    credit_engine,
    switchboard,
    governance,
):
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()
    performDeposit(
        bob,
        100 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)

    borrow_amount = teller.borrow(50 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    green_token.approve(savings_green, borrow_amount, sender=bob)
    shares = savings_green.deposit(borrow_amount, bob, sender=bob)
    savings_green.approve(teller, shares, sender=bob)
    repay_shares = shares // 2

    def payment_state():
        return (
            savings_green.balanceOf(bob),
            savings_green.balanceOf(teller),
            savings_green.balanceOf(credit_engine),
            savings_green.totalSupply(),
            savings_green.allowance(bob, teller),
            savings_green.lastPricePerShare(),
            green_token.balanceOf(bob),
            green_token.balanceOf(teller),
            green_token.balanceOf(credit_engine),
            green_token.balanceOf(savings_green),
            ledger.userDebt(bob).amount,
        )

    with boa.env.anchor():
        savings_green.setBlacklist(bob, True, sender=switchboard.address)
        assert savings_green.blacklisted(bob)
        before = payment_state()
        with pytest.raises(boa.BoaError) as exc_info:
            teller.repay(repay_shares, bob, True, False, sender=bob)
        assert "sender blacklisted" in get_boa_dev_reasons(exc_info.value)
        assert payment_state() == before

    with boa.env.anchor():
        green_token.setBlacklist(credit_engine, True, sender=switchboard.address)
        assert green_token.blacklisted(credit_engine)
        assert not savings_green.blacklisted(credit_engine)
        before = payment_state()
        with pytest.raises(boa.BoaError) as exc_info:
            teller.repay(repay_shares, bob, True, False, sender=bob)
        assert "recipient blacklisted" in get_boa_dev_reasons(exc_info.value)
        assert payment_state() == before

    with boa.env.anchor():
        savings_green.pause(True, sender=governance.address)
        assert savings_green.isPaused()
        before = payment_state()
        with pytest.raises(boa.BoaError) as exc_info:
            teller.repay(repay_shares, bob, True, False, sender=bob)
        assert "token paused" in get_boa_dev_reasons(exc_info.value)
        assert payment_state() == before

    with boa.env.anchor():
        savings_green.setBlacklist(
            credit_engine,
            True,
            sender=switchboard.address,
        )
        assert savings_green.blacklisted(credit_engine)
        assert not green_token.blacklisted(credit_engine)
        debt_before = ledger.userDebt(bob).amount
        assert teller.repay(repay_shares, bob, True, False, sender=bob)
        assert savings_green.balanceOf(bob) == shares - repay_shares
        assert ledger.userDebt(bob).amount < debt_before
        assert green_token.balanceOf(credit_engine) == 0


def test_repay_with_savings_green_payment_max_amount(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    green_token,
    savings_green,
    ledger,
    credit_engine,
):
    """Test repaying max debt using Savings Green tokens"""
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()

    # deposit and borrow
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    borrow_amount = teller.borrow(MAX_UINT256, bob, False, sender=bob)

    # deposit all green tokens into savings green
    green_token.approve(savings_green, borrow_amount, sender=bob)
    savings_green.deposit(borrow_amount, bob, sender=bob)

    # approve teller to spend savings green tokens
    savings_green.approve(teller, MAX_UINT256, sender=bob)
    
    # repay max amount using savings green tokens
    assert teller.repay(
        MAX_UINT256,
        bob,
        True,   # _isPaymentSavingsGreen
        False,  # _shouldRefundSavingsGreen
        sender=bob
    )

    # verify debt is fully repaid
    assert ledger.userDebt(bob).amount == 0

    # verify all savings green tokens were used
    assert savings_green.balanceOf(bob) == 0

    # verify no regular green tokens remain with bob
    assert green_token.balanceOf(bob) == 0
    assert green_token.balanceOf(credit_engine) == 0


M3_REPAY_PRICE_DESK_SOURCE = """
# @version 0.4.3

unsafe_asset: immutable(address)

@deploy
def __init__(_unsafe_asset: address):
    unsafe_asset = _unsafe_asset

@view
@external
def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool) -> uint256:
    assert _asset != unsafe_asset, "unsafe price lookup"
    return _amount

@view
@external
def getAddr(_regId: uint256) -> address:
    return empty(address)
"""


def test_repay_uses_safe_collateral_without_pricing_zero_amount_position(
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
    teller,
    green_token,
    ledger,
    price_desk,
    rebase_erc20_vault,
    createDebtTerms,
):
    setGeneralConfig()
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=60_00,
        _liqThreshold=70_00,
        _liqFee=10_00,
        _borrowRate=5_00,
        _daowry=0,
    )
    setAssetConfig(alpha_token, _vaultIds=[3], _debtTerms=debt_terms)
    setAssetConfig(bravo_token, _vaultIds=[4], _debtTerms=debt_terms)
    setGeneralDebtConfig()

    safe_amount = 100 * EIGHTEEN_DECIMALS
    unsafe_nominal = 1 * EIGHTEEN_DECIMALS
    performDeposit(
        bob,
        safe_amount,
        alpha_token,
        alpha_token_whale,
    )
    performDeposit(
        bob,
        unsafe_nominal,
        bravo_token,
        bravo_token_whale,
        rebase_erc20_vault,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)

    debt_before = 40 * EIGHTEEN_DECIMALS
    assert teller.borrow(debt_before, bob, False, sender=bob) == debt_before

    # A total-loss SharesVault position remains `(asset, 0)`.
    bravo_token.transfer(
        bravo_token_whale,
        unsafe_nominal,
        sender=rebase_erc20_vault.address,
    )
    unsafe_asset, unsafe_amount = (
        rebase_erc20_vault.getUserAssetAndAmountAtIndex(bob, 1)
    )
    assert unsafe_asset == bravo_token.address
    assert unsafe_amount == 0

    # The replacement reverts for the unsafe asset. Successful preview, health,
    # and repayment therefore prove that CreditEngine never asks for its price.
    guarded_price_desk = boa.loads(
        M3_REPAY_PRICE_DESK_SOURCE,
        bravo_token.address,
        name="m3_repay_price_desk",
        override_address=boa.env.generate_address(),
    )
    boa.env.set_code(
        price_desk.address,
        boa.env.get_code(guarded_price_desk.address),
    )

    preview = credit_engine.getUserBorrowTerms(bob, True)
    assert preview.collateralVal == safe_amount
    assert preview.totalMaxDebt == safe_amount // 2
    assert preview.debtTerms.liqThreshold == 70_00
    assert credit_engine.hasGoodDebtHealth(bob)

    repay_amount = 10 * EIGHTEEN_DECIMALS
    assert green_token.approve(teller, repay_amount, sender=bob)
    assert teller.repay(repay_amount, bob, False, False, sender=bob)

    assert ledger.userDebt(bob).amount == debt_before - repay_amount
    repay_log = filter_logs(teller, "RepayDebt")[0]
    assert repay_log.outstandingUserDebt == debt_before - repay_amount
    assert repay_log.userCollateralVal == preview.collateralVal
    assert repay_log.maxUserDebt == preview.totalMaxDebt
    assert repay_log.hasGoodDebtHealth
