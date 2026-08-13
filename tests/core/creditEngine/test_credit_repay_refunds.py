import boa
import pytest
from constants import EIGHTEEN_DECIMALS, MAX_UINT256
from conf_utils import filter_logs, get_boa_dev_reasons


def _open_standard_debt(
    *,
    user,
    debt_amount,
    alpha_token,
    alpha_token_whale,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    debt_terms=None,
):
    setGeneralConfig()
    if debt_terms is None:
        setAssetConfig(alpha_token)
    else:
        setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()
    performDeposit(
        user,
        100 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    assert teller.borrow(debt_amount, user, False, sender=user) == debt_amount


def test_repay_overpayment_with_green_refund(
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
    whale,
):
    """Test that overpaying debt returns the excess GREEN tokens to user"""
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()

    # deposit and borrow
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # borrow 50 GREEN
    borrow_amount = teller.borrow(MAX_UINT256, bob, False, sender=bob)
    assert borrow_amount == 50 * EIGHTEEN_DECIMALS
    
    # give bob extra GREEN tokens (total 100 GREEN)
    extra_green = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, extra_green, sender=whale)
    assert green_token.balanceOf(bob) == 100 * EIGHTEEN_DECIMALS
    
    # approve teller for all tokens
    green_token.approve(teller, MAX_UINT256, sender=bob)
    
    # repay with MAX_UINT256 (should use all 100 GREEN, but only need 50)
    assert teller.repay(MAX_UINT256, bob, False, False, sender=bob)
    
    # verify debt is fully paid
    assert ledger.userDebt(bob).amount == 0
    
    # CRITICAL: verify refund was issued
    # bob should have 50 GREEN refunded (100 - 50 debt)
    assert green_token.balanceOf(bob) == 50 * EIGHTEEN_DECIMALS
    
    # credit engine should have 0 GREEN (all burned or refunded)
    assert green_token.balanceOf(credit_engine) == 0

    repay_log = filter_logs(teller, "RepayDebt")[0]
    assert repay_log.user == bob
    assert repay_log.repayValue == borrow_amount
    assert repay_log.refundAmount == extra_green
    assert not repay_log.refundWasSavingsGreen


def test_repay_exact_overpayment_amount(
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
    whale,
):
    """Test overpaying with a specific amount greater than debt"""
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()

    # deposit and borrow
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # borrow 30 GREEN
    borrow_amount = 30 * EIGHTEEN_DECIMALS
    actual_borrow = teller.borrow(borrow_amount, bob, False, sender=bob)
    assert actual_borrow == borrow_amount
    
    # give bob extra GREEN (total 50 GREEN)
    extra_green = 20 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, extra_green, sender=whale)
    assert green_token.balanceOf(bob) == 50 * EIGHTEEN_DECIMALS
    
    # approve and repay 50 GREEN (20 more than needed)
    repay_amount = 50 * EIGHTEEN_DECIMALS
    green_token.approve(teller, repay_amount, sender=bob)
    assert teller.repay(repay_amount, bob, False, False, sender=bob)
    
    # verify debt is cleared
    assert ledger.userDebt(bob).amount == 0
    
    # verify refund: should get back 20 GREEN
    assert green_token.balanceOf(bob) == 20 * EIGHTEEN_DECIMALS
    
    # credit engine should be empty
    assert green_token.balanceOf(credit_engine) == 0


def test_repay_overpayment_with_savings_green_refund(
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
    whale,
):
    """Test that overpaying debt with request for sGREEN refund works correctly"""
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()

    # deposit and borrow
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # borrow 25 GREEN
    borrow_amount = 25 * EIGHTEEN_DECIMALS
    actual_borrow = teller.borrow(borrow_amount, bob, False, sender=bob)
    assert actual_borrow == borrow_amount
    
    # give bob extra GREEN (total 75 GREEN)
    extra_green = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, extra_green, sender=whale)
    assert green_token.balanceOf(bob) == 75 * EIGHTEEN_DECIMALS
    
    # approve and repay all GREEN, requesting sGREEN refund
    green_token.approve(teller, MAX_UINT256, sender=bob)
    assert teller.repay(
        MAX_UINT256, 
        bob, 
        False,  # not paying with sGREEN
        True,   # want sGREEN refund
        sender=bob
    )
    
    # verify debt is cleared
    assert ledger.userDebt(bob).amount == 0
    
    # verify GREEN is gone
    assert green_token.balanceOf(bob) == 0
    
    # verify sGREEN refund received (50 GREEN worth)
    sgreen_balance = savings_green.balanceOf(bob)
    assert sgreen_balance > 0
    # should be able to redeem for approximately 50 GREEN
    redeemable = savings_green.convertToAssets(sgreen_balance)
    assert redeemable >= 49 * EIGHTEEN_DECIMALS  # allowing for rounding
    assert redeemable <= 51 * EIGHTEEN_DECIMALS
    
    # credit engine should be empty
    assert green_token.balanceOf(credit_engine) == 0


def test_repay_small_overpayment(
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
    whale,
):
    """Test overpaying by a small amount (edge case for dust)"""
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()

    # deposit and borrow
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # borrow specific amount
    borrow_amount = 10 * EIGHTEEN_DECIMALS
    actual_borrow = teller.borrow(borrow_amount, bob, False, sender=bob)
    assert actual_borrow == borrow_amount
    
    # give bob 1 wei extra
    extra_green = 1
    green_token.transfer(bob, extra_green, sender=whale)
    total_balance = borrow_amount + extra_green
    assert green_token.balanceOf(bob) == total_balance
    
    # repay all (1 wei overpayment)
    green_token.approve(teller, MAX_UINT256, sender=bob)
    assert teller.repay(MAX_UINT256, bob, False, False, sender=bob)
    
    # verify debt is cleared
    assert ledger.userDebt(bob).amount == 0
    
    # verify 1 wei refund
    assert green_token.balanceOf(bob) == 1
    
    # credit engine should be empty
    assert green_token.balanceOf(credit_engine) == 0


def test_repay_massive_overpayment(
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
    whale,
):
    """Test overpaying by 10x the debt amount"""
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()

    # deposit and borrow
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # borrow 10 GREEN
    borrow_amount = 10 * EIGHTEEN_DECIMALS
    actual_borrow = teller.borrow(borrow_amount, bob, False, sender=bob)
    assert actual_borrow == borrow_amount
    
    # give bob 10x the debt amount (100 GREEN total)
    extra_green = 90 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, extra_green, sender=whale)
    assert green_token.balanceOf(bob) == 100 * EIGHTEEN_DECIMALS
    
    # repay with all tokens
    green_token.approve(teller, MAX_UINT256, sender=bob)
    assert teller.repay(MAX_UINT256, bob, False, False, sender=bob)
    
    # verify debt is cleared
    assert ledger.userDebt(bob).amount == 0
    
    # verify 90 GREEN refund
    assert green_token.balanceOf(bob) == 90 * EIGHTEEN_DECIMALS
    
    # credit engine should be empty
    assert green_token.balanceOf(credit_engine) == 0


def test_repay_with_interest_overpayment(
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
    """Test overpaying when debt has accrued interest"""
    # setup with high interest rate
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
    assert borrow_amount == 50 * EIGHTEEN_DECIMALS

    # time travel 1 year to accrue 100% interest
    boa.env.time_travel(seconds=31536000)
    credit_engine.updateDebtForUser(bob, sender=credit_engine.address)
    
    # debt should now be 100 GREEN (50 principal + 50 interest)
    user_debt = ledger.userDebt(bob)
    assert user_debt.amount == 100 * EIGHTEEN_DECIMALS
    
    # give bob 120 GREEN (20 more than needed)
    green_token.transfer(bob, 70 * EIGHTEEN_DECIMALS, sender=whale)
    assert green_token.balanceOf(bob) == 120 * EIGHTEEN_DECIMALS
    
    # repay all
    green_token.approve(teller, MAX_UINT256, sender=bob)
    assert teller.repay(MAX_UINT256, bob, False, False, sender=bob)
    
    # verify debt is cleared
    assert ledger.userDebt(bob).amount == 0
    
    # verify 20 GREEN refund
    assert green_token.balanceOf(bob) == 20 * EIGHTEEN_DECIMALS
    
    # credit engine should be empty
    assert green_token.balanceOf(credit_engine) == 0


def test_multiple_users_overpaying_simultaneously(
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
    ledger,
    credit_engine,
    whale,
):
    """Test that multiple users can overpay and get refunds correctly"""
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()

    # both users deposit and borrow
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    performDeposit(sally, deposit_amount, alpha_token, alpha_token_whale)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # bob borrows 30, sally borrows 40
    bob_borrow = 30 * EIGHTEEN_DECIMALS
    sally_borrow = 40 * EIGHTEEN_DECIMALS
    assert teller.borrow(bob_borrow, bob, False, sender=bob) == bob_borrow
    assert teller.borrow(sally_borrow, sally, False, sender=sally) == sally_borrow
    
    # give them extra GREEN
    green_token.transfer(bob, 20 * EIGHTEEN_DECIMALS, sender=whale)  # bob has 50 total
    green_token.transfer(sally, 10 * EIGHTEEN_DECIMALS, sender=whale)  # sally has 50 total
    
    # both repay with MAX_UINT256
    green_token.approve(teller, MAX_UINT256, sender=bob)
    green_token.approve(teller, MAX_UINT256, sender=sally)
    
    assert teller.repay(MAX_UINT256, bob, False, False, sender=bob)
    assert teller.repay(MAX_UINT256, sally, False, False, sender=sally)
    
    # verify both debts cleared
    assert ledger.userDebt(bob).amount == 0
    assert ledger.userDebt(sally).amount == 0
    
    # verify refunds
    assert green_token.balanceOf(bob) == 20 * EIGHTEEN_DECIMALS  # 50 - 30 debt
    assert green_token.balanceOf(sally) == 10 * EIGHTEEN_DECIMALS  # 50 - 40 debt
    
    # credit engine should be empty
    assert green_token.balanceOf(credit_engine) == 0


def test_no_refund_when_exact_payment(
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
):
    """Test that exact payment results in no refund"""
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
    
    # repay exact amount
    green_token.approve(teller, borrow_amount, sender=bob)
    assert teller.repay(borrow_amount, bob, False, False, sender=bob)
    
    # verify debt is cleared
    assert ledger.userDebt(bob).amount == 0
    
    # verify no refund (balance should be 0)
    assert green_token.balanceOf(bob) == 0
    
    # credit engine should be empty
    assert green_token.balanceOf(credit_engine) == 0


def test_repay_amount_is_capped_by_credit_engine_balance(
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
):
    """The declared amount cannot make CreditEngine burn tokens it did not receive."""
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
    debt = 50 * EIGHTEEN_DECIMALS
    teller.borrow(debt, bob, False, sender=bob)

    received = 10 * EIGHTEEN_DECIMALS
    green_token.transfer(credit_engine, received, sender=bob)
    assert credit_engine.repayForUser(
        bob,
        debt,
        False,
        bob,
        sender=teller.address,
    )

    log = filter_logs(credit_engine, "RepayDebt")[0]
    assert log.repayValue == received
    assert log.refundAmount == 0
    assert ledger.userDebt(bob).amount == debt - received
    assert green_token.balanceOf(credit_engine) == 0


def test_repay_amount_is_capped_by_declared_amount(
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
    whale,
):
    """Unrelated GREEN already held by CreditEngine is not consumed or refunded."""
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
    debt = 50 * EIGHTEEN_DECIMALS
    teller.borrow(debt, bob, False, sender=bob)

    held = 20 * EIGHTEEN_DECIMALS
    declared = 10 * EIGHTEEN_DECIMALS
    green_token.transfer(credit_engine, held, sender=whale)
    assert credit_engine.repayForUser(
        bob,
        declared,
        False,
        bob,
        sender=teller.address,
    )

    log = filter_logs(credit_engine, "RepayDebt")[0]
    assert log.repayValue == declared
    assert log.refundAmount == 0
    assert ledger.userDebt(bob).amount == debt - declared
    assert green_token.balanceOf(credit_engine) == held - declared


def test_paying_with_savings_green_overpayment(
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
    """Test overpaying when paying with sGREEN tokens directly"""
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()

    # deposit and borrow
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # borrow 30 GREEN
    borrow_amount = 30 * EIGHTEEN_DECIMALS
    actual_borrow = teller.borrow(borrow_amount, bob, False, sender=bob)
    assert actual_borrow == borrow_amount
    
    # convert all GREEN to sGREEN (30 GREEN worth)
    green_token.approve(savings_green, borrow_amount, sender=bob)
    shares = savings_green.deposit(borrow_amount, bob, sender=bob)
    
    # now bob has sGREEN worth 30 GREEN but owes 30 GREEN
    assert green_token.balanceOf(bob) == 0
    assert savings_green.balanceOf(bob) == shares
    
    # approve and repay with all sGREEN
    savings_green.approve(teller, MAX_UINT256, sender=bob)
    assert teller.repay(
        MAX_UINT256,
        bob,
        True,   # paying with sGREEN
        True,   # want sGREEN refund
        sender=bob
    )
    
    # verify debt is cleared
    assert ledger.userDebt(bob).amount == 0
    
    # verify no tokens remain (exact payment scenario)
    assert green_token.balanceOf(bob) == 0
    assert savings_green.balanceOf(bob) == 0
    
    # credit engine should be empty
    assert green_token.balanceOf(credit_engine) == 0


@pytest.mark.parametrize(
    ("surplus", "use_max_sentinel"),
    [
        pytest.param(0, False, id="exact"),
        pytest.param(1, False, id="one-unit-overpayment"),
        pytest.param(90 * EIGHTEEN_DECIMALS, False, id="material-overpayment"),
        pytest.param(40 * EIGHTEEN_DECIMALS, True, id="maximum-sentinel"),
    ],
)
def test_third_party_green_repayment_refunds_only_the_payer(
    surplus,
    use_max_sentinel,
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
    savings_green,
    ledger,
    credit_engine,
    whale,
):
    debt = 10 * EIGHTEEN_DECIMALS
    _open_standard_debt(
        user=bob,
        debt_amount=debt,
        alpha_token=alpha_token,
        alpha_token_whale=alpha_token_whale,
        setGeneralConfig=setGeneralConfig,
        setAssetConfig=setAssetConfig,
        setGeneralDebtConfig=setGeneralDebtConfig,
        performDeposit=performDeposit,
        mock_price_source=mock_price_source,
        teller=teller,
    )

    # Calling the convenience function with defaults opens third-party repayment.
    assert teller.setUserConfig(sender=bob)
    payment = debt + surplus
    green_token.transfer(sally, payment, sender=whale)
    green_token.approve(teller, MAX_UINT256, sender=sally)

    debtor_green_before = green_token.balanceOf(bob)
    debtor_sgreen_before = savings_green.balanceOf(bob)
    supply_before = green_token.totalSupply()
    requested_payment = MAX_UINT256 if use_max_sentinel else payment
    assert teller.repay(
        requested_payment,
        bob,
        False,
        False,
        sender=sally,
    )

    assert ledger.userDebt(bob).amount == 0
    assert green_token.totalSupply() == supply_before - debt
    assert green_token.balanceOf(sally) == surplus
    assert savings_green.balanceOf(sally) == 0
    assert green_token.balanceOf(bob) == debtor_green_before
    assert savings_green.balanceOf(bob) == debtor_sgreen_before
    assert green_token.balanceOf(credit_engine) == 0

    logs = filter_logs(teller, "RepayDebt")
    assert len(logs) == 1
    assert logs[0].user == bob
    assert logs[0].repayValue == debt
    assert logs[0].refundAmount == surplus
    assert not logs[0].refundWasSavingsGreen


def test_third_party_sgreen_payment_refunds_green_to_the_payer(
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
    savings_green,
    ledger,
    whale,
):
    debt = 30 * EIGHTEEN_DECIMALS
    _open_standard_debt(
        user=bob,
        debt_amount=debt,
        alpha_token=alpha_token,
        alpha_token_whale=alpha_token_whale,
        setGeneralConfig=setGeneralConfig,
        setAssetConfig=setAssetConfig,
        setGeneralDebtConfig=setGeneralDebtConfig,
        performDeposit=performDeposit,
        mock_price_source=mock_price_source,
        teller=teller,
    )
    teller.setUserConfig(sender=bob)

    payment_assets = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(sally, payment_assets, sender=whale)
    green_token.approve(savings_green, payment_assets, sender=sally)
    payment_shares = savings_green.deposit(payment_assets, sally, sender=sally)
    redeemed_assets = savings_green.previewRedeem(payment_shares)
    assert redeemed_assets > debt
    refund = redeemed_assets - debt
    savings_green.approve(teller, MAX_UINT256, sender=sally)

    debtor_green_before = green_token.balanceOf(bob)
    debtor_sgreen_before = savings_green.balanceOf(bob)
    assert teller.repay(MAX_UINT256, bob, True, False, sender=sally)

    assert ledger.userDebt(bob).amount == 0
    assert savings_green.balanceOf(sally) == 0
    assert green_token.balanceOf(sally) == refund
    assert green_token.balanceOf(bob) == debtor_green_before
    assert savings_green.balanceOf(bob) == debtor_sgreen_before

    repay_log = filter_logs(teller, "RepayDebt")[0]
    assert repay_log.user == bob
    assert repay_log.repayValue == debt
    assert repay_log.refundAmount == refund
    assert not repay_log.refundWasSavingsGreen


def test_third_party_green_overpayment_refunds_sgreen_to_the_payer(
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
    savings_green,
    ledger,
    whale,
):
    debt = 30 * EIGHTEEN_DECIMALS
    surplus = 20 * EIGHTEEN_DECIMALS
    _open_standard_debt(
        user=bob,
        debt_amount=debt,
        alpha_token=alpha_token,
        alpha_token_whale=alpha_token_whale,
        setGeneralConfig=setGeneralConfig,
        setAssetConfig=setAssetConfig,
        setGeneralDebtConfig=setGeneralDebtConfig,
        performDeposit=performDeposit,
        mock_price_source=mock_price_source,
        teller=teller,
    )
    teller.setUserConfig(sender=bob)

    payment = debt + surplus
    green_token.transfer(sally, payment, sender=whale)
    green_token.approve(teller, payment, sender=sally)
    expected_shares = savings_green.previewDeposit(surplus)
    payer_sgreen_before = savings_green.balanceOf(sally)
    debtor_green_before = green_token.balanceOf(bob)
    debtor_sgreen_before = savings_green.balanceOf(bob)
    savings_assets_before = green_token.balanceOf(savings_green)

    assert teller.repay(payment, bob, False, True, sender=sally)

    assert ledger.userDebt(bob).amount == 0
    assert green_token.balanceOf(sally) == 0
    assert savings_green.balanceOf(sally) - payer_sgreen_before == expected_shares
    assert green_token.balanceOf(savings_green) - savings_assets_before == surplus
    assert green_token.balanceOf(bob) == debtor_green_before
    assert savings_green.balanceOf(bob) == debtor_sgreen_before

    repay_log = filter_logs(teller, "RepayDebt")[0]
    assert repay_log.user == bob
    assert repay_log.repayValue == debt
    assert repay_log.refundAmount == surplus
    assert repay_log.refundWasSavingsGreen


def test_third_party_interest_overpayment_refunds_only_true_surplus(
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
    savings_green,
    ledger,
    credit_engine,
    createDebtTerms,
    whale,
):
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=60_00,
        _liqThreshold=70_00,
        _liqFee=10_00,
        _borrowRate=100_00,
        _daowry=1_00,
    )
    principal = 50 * EIGHTEEN_DECIMALS
    _open_standard_debt(
        user=bob,
        debt_amount=principal,
        alpha_token=alpha_token,
        alpha_token_whale=alpha_token_whale,
        setGeneralConfig=setGeneralConfig,
        setAssetConfig=setAssetConfig,
        setGeneralDebtConfig=setGeneralDebtConfig,
        performDeposit=performDeposit,
        mock_price_source=mock_price_source,
        teller=teller,
        debt_terms=debt_terms,
    )
    teller.setUserConfig(sender=bob)

    boa.env.time_travel(seconds=31_536_000)
    current_debt, _, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    current_debt = current_debt.amount
    assert current_debt > principal
    assert ledger.userDebt(bob).amount == principal
    surplus = 7 * EIGHTEEN_DECIMALS
    payment = current_debt + surplus
    green_token.transfer(sally, payment, sender=whale)
    green_token.approve(teller, payment, sender=sally)
    debtor_green_before = green_token.balanceOf(bob)
    debtor_sgreen_before = savings_green.balanceOf(bob)

    assert teller.repay(payment, bob, False, False, sender=sally)

    assert ledger.userDebt(bob).amount == 0
    assert green_token.balanceOf(sally) == surplus
    assert green_token.balanceOf(bob) == debtor_green_before
    assert savings_green.balanceOf(bob) == debtor_sgreen_before
    repay_log = filter_logs(teller, "RepayDebt")[0]
    assert repay_log.repayValue == current_debt
    assert repay_log.refundAmount == surplus


def test_third_party_repay_permissions_remain_closed_or_default_open(
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
    mission_control,
    green_token,
    savings_green,
    ledger,
    whale,
):
    debt = 20 * EIGHTEEN_DECIMALS
    surplus = 5 * EIGHTEEN_DECIMALS
    _open_standard_debt(
        user=bob,
        debt_amount=debt,
        alpha_token=alpha_token,
        alpha_token_whale=alpha_token_whale,
        setGeneralConfig=setGeneralConfig,
        setAssetConfig=setAssetConfig,
        setGeneralDebtConfig=setGeneralDebtConfig,
        performDeposit=performDeposit,
        mock_price_source=mock_price_source,
        teller=teller,
    )
    payment = debt + surplus
    green_token.transfer(sally, payment, sender=whale)
    green_token.approve(teller, payment, sender=sally)

    assert teller.setUserConfig(bob, True, False, True, sender=bob)
    assert not mission_control.getRepayConfig(bob).canAnyoneRepayDebt
    closed_state = (
        ledger.userDebt(bob),
        green_token.balanceOf(sally),
        green_token.allowance(sally, teller),
    )
    with boa.reverts("not allowed to repay for user"):
        teller.repay(payment, bob, False, False, sender=sally)
    assert (
        ledger.userDebt(bob),
        green_token.balanceOf(sally),
        green_token.allowance(sally, teller),
    ) == closed_state

    # The convenience call's defaults explicitly make third-party repay open.
    assert teller.setUserConfig(sender=bob)
    assert mission_control.getRepayConfig(bob).canAnyoneRepayDebt
    debtor_green_before = green_token.balanceOf(bob)
    debtor_sgreen_before = savings_green.balanceOf(bob)
    assert teller.repay(payment, bob, False, False, sender=sally)
    assert ledger.userDebt(bob).amount == 0
    assert green_token.balanceOf(sally) == surplus
    assert green_token.balanceOf(bob) == debtor_green_before
    assert savings_green.balanceOf(bob) == debtor_sgreen_before


def test_underscore_owner_can_repay_closed_wallet_and_receives_refund(
    alpha_token,
    alpha_token_whale,
    sally,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    mission_control,
    switchboard_alpha,
    mock_undy_v2,
    green_token,
    savings_green,
    ledger,
    whale,
):
    wallet_config = boa.loads(
        """
# @version 0.4.3
owner: public(address)

@deploy
def __init__(_owner: address):
    self.owner = _owner
""",
        sally,
        name="repay_wallet_config",
    )
    wallet = boa.loads(
        """
# @version 0.4.3
walletConfig: public(address)

@deploy
def __init__(_walletConfig: address):
    self.walletConfig = _walletConfig
""",
        wallet_config,
        name="repay_wallet",
    )
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_undy_v2.setAllAddressesAreVaults(False)
    mock_undy_v2.setIsUserWallet(True)

    debt = 20 * EIGHTEEN_DECIMALS
    surplus = 3 * EIGHTEEN_DECIMALS
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()
    performDeposit(
        wallet.address,
        100 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    assert teller.borrow(debt, wallet.address, False, sender=sally) == debt
    assert teller.setUserConfig(
        wallet.address,
        True,
        False,
        True,
        sender=sally,
    )
    assert not mission_control.getRepayConfig(wallet.address).canAnyoneRepayDebt

    payment = debt + surplus
    green_token.transfer(sally, payment, sender=whale)
    green_token.approve(teller, payment, sender=sally)
    wallet_green_before = green_token.balanceOf(wallet)
    wallet_sgreen_before = savings_green.balanceOf(wallet)
    assert teller.repay(payment, wallet.address, False, False, sender=sally)

    assert ledger.userDebt(wallet.address).amount == 0
    assert green_token.balanceOf(sally) == surplus
    assert green_token.balanceOf(wallet) == wallet_green_before
    assert savings_green.balanceOf(wallet) == wallet_sgreen_before
    repay_log = filter_logs(teller, "RepayDebt")[0]
    assert repay_log.user == wallet.address
    assert repay_log.refundAmount == surplus


def test_sgreen_refund_failure_rolls_back_complete_third_party_repayment(
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
    savings_green,
    ledger,
    credit_engine,
    governance,
    whale,
):
    debt = 30 * EIGHTEEN_DECIMALS
    surplus = 20 * EIGHTEEN_DECIMALS
    payment = debt + surplus
    _open_standard_debt(
        user=bob,
        debt_amount=debt,
        alpha_token=alpha_token,
        alpha_token_whale=alpha_token_whale,
        setGeneralConfig=setGeneralConfig,
        setAssetConfig=setAssetConfig,
        setGeneralDebtConfig=setGeneralDebtConfig,
        performDeposit=performDeposit,
        mock_price_source=mock_price_source,
        teller=teller,
    )
    teller.setUserConfig(sender=bob)
    green_token.transfer(sally, payment, sender=whale)
    green_token.approve(teller, payment, sender=sally)

    savings_green.pause(True, sender=governance.address)
    assert savings_green.isPaused()
    assert not green_token.isPaused()

    def repayment_state():
        return (
            ledger.userDebt(bob),
            ledger.totalDebt(),
            ledger.borrowIntervals(bob),
            ledger.numBorrowers(),
            ledger.indexOfBorrower(bob),
            ledger.unrealizedYield(),
            ledger.userBorrowPoints(bob),
            ledger.globalBorrowPoints(),
            ledger.ripeRewards(),
            ledger.ripeAvailForRewards(),
            green_token.totalSupply(),
            green_token.balanceOf(sally),
            green_token.balanceOf(bob),
            green_token.balanceOf(teller),
            green_token.balanceOf(credit_engine),
            green_token.balanceOf(savings_green),
            green_token.allowance(sally, teller),
            green_token.allowance(credit_engine, savings_green),
            savings_green.totalSupply(),
            savings_green.balanceOf(sally),
            savings_green.balanceOf(bob),
            savings_green.balanceOf(credit_engine),
            savings_green.lastPricePerShare(),
        )

    before = repayment_state()
    with pytest.raises(boa.BoaError) as exc_info:
        teller.repay(payment, bob, False, True, sender=sally)
    assert "token paused" in get_boa_dev_reasons(exc_info.value)
    assert repayment_state() == before
