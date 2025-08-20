import boa
from constants import EIGHTEEN_DECIMALS, MAX_UINT256


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