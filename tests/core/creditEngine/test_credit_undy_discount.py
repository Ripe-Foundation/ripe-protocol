import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS
from conf_utils import filter_logs


def test_undy_vault_waives_daowry(
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
    mission_control,
    switchboard_alpha,
    mock_undy_v2,
    createDebtTerms,
):
    """Test that Underscore vaults don't pay daowry while regular users do"""
    # Setup with daowry enabled
    setGeneralConfig()
    debt_terms = createDebtTerms(_daowry=5_00)  # 5% origination fee
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig(_isDaowryEnabled=True)

    # Deposit collateral
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # Set prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # Verify initial balances
    assert green_token.balanceOf(savings_green) == 0
    assert green_token.balanceOf(bob) == 0

    # Test 1: WITHOUT underscore registry - regular user behavior (pays daowry)
    borrow_amount = 25 * EIGHTEEN_DECIMALS
    regular_amount = teller.borrow(borrow_amount, bob, False, sender=bob)

    regular_log = filter_logs(teller, "NewBorrow")[0]
    expected_daowry = borrow_amount * 5_00 // 100_00
    expected_regular_amount = borrow_amount - expected_daowry

    assert regular_log.user == bob
    assert regular_log.daowry == expected_daowry
    assert regular_log.newLoan == expected_regular_amount
    assert regular_log.outstandingUserDebt == borrow_amount
    assert regular_amount == expected_regular_amount
    assert green_token.balanceOf(savings_green) == expected_daowry

    # Test 2: WITH underscore registry - Underscore vault behavior (NO daowry)
    # Setup underscore registry - bob will now be treated as Underscore vault
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)

    # Bob borrows again - should NOT pay daowry this time
    vault_amount = teller.borrow(borrow_amount, bob, False, sender=bob)

    vault_log = filter_logs(teller, "NewBorrow")[0]  # Gets log from most recent tx
    assert vault_log.user == bob
    assert vault_log.daowry == 0  # NO DAOWRY
    assert vault_log.newLoan == borrow_amount  # FULL AMOUNT
    assert vault_log.outstandingUserDebt == borrow_amount + borrow_amount  # Total from both borrows
    assert vault_amount == borrow_amount
    # savings_green balance unchanged (no new daowry)
    assert green_token.balanceOf(savings_green) == expected_daowry


def test_undy_vault_gets_interest_rate_discount(
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
    green_token,
    mission_control,
    switchboard_alpha,
    mock_undy_v2,
    credit_engine,
    createDebtTerms,
):
    """Test that Underscore vaults get interest rate discount while regular users don't"""
    # Set discount to 50%
    credit_engine.setUnderscoreVaultDiscount(50_00, sender=switchboard_alpha.address)

    # Setup with 10% borrow rate
    setGeneralConfig()
    debt_terms = createDebtTerms(_borrowRate=10_00)  # 10% annual interest
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    # Deposit collateral
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # Set prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # Test 1: WITHOUT underscore registry - regular user behavior (full rate)
    borrow_amount = 25 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    regular_debt = ledger.userDebt(bob)
    assert regular_debt.debtTerms.borrowRate == 10_00  # Full rate, no discount

    # Repay the debt to clear it
    green_token.approve(teller.address, borrow_amount, sender=bob)
    teller.repay(borrow_amount, bob, sender=bob)

    # Test 2: WITH underscore registry - Underscore vault behavior (discounted rate)
    # Setup underscore registry
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)

    # Bob borrows again - should have discounted rate
    teller.borrow(borrow_amount, bob, False, sender=bob)

    vault_debt = ledger.userDebt(bob)
    expected_discounted_rate = 10_00 * 50_00 // 100_00
    assert vault_debt.debtTerms.borrowRate == expected_discounted_rate  # 5% (50% discount)
    assert vault_debt.debtTerms.borrowRate == 5_00


def test_discount_persists_through_repay(
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
    green_token,
    mission_control,
    switchboard_alpha,
    mock_undy_v2,
    credit_engine,
    createDebtTerms,
):
    """Test that interest rate discount persists through repayment"""
    # Setup underscore registry
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    credit_engine.setUnderscoreVaultDiscount(50_00, sender=switchboard_alpha.address)

    # Setup with 10% borrow rate
    setGeneralConfig()
    debt_terms = createDebtTerms(_borrowRate=10_00)
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    # Deposit and borrow
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    borrow_amount = 50 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    # Verify discount applied on borrow
    bob_debt_before = ledger.userDebt(bob)
    assert bob_debt_before.debtTerms.borrowRate == 5_00  # 50% discount

    # Partial repayment
    repay_amount = 20 * EIGHTEEN_DECIMALS
    green_token.approve(teller.address, repay_amount, sender=bob)
    teller.repay(repay_amount, bob, sender=bob)

    # Verify discount still applied after repay
    bob_debt_after = ledger.userDebt(bob)
    assert bob_debt_after.debtTerms.borrowRate == 5_00  # Discount persists
    assert bob_debt_after.amount < bob_debt_before.amount  # Debt reduced


def test_discount_persists_through_update_debt(
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
    mission_control,
    switchboard_alpha,
    mock_undy_v2,
    createDebtTerms,
):
    """Test that interest rate discount persists through updateDebtForUser"""
    # Setup underscore registry
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    credit_engine.setUnderscoreVaultDiscount(50_00, sender=switchboard_alpha.address)

    # Setup with 10% borrow rate
    setGeneralConfig()
    debt_terms = createDebtTerms(_borrowRate=10_00)
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    # Deposit and borrow
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    borrow_amount = 50 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    # Verify discount applied on borrow
    bob_debt_before = ledger.userDebt(bob)
    assert bob_debt_before.debtTerms.borrowRate == 5_00  # 50% discount

    # Advance time to accrue some interest
    boa.env.time_travel(seconds=365 * 24 * 60 * 60 // 2)  # 6 months

    # Update debt (must call from authorized address)
    credit_engine.updateDebtForUser(bob, sender=credit_engine.address)

    # Verify discount still applied after update
    bob_debt_after = ledger.userDebt(bob)
    assert bob_debt_after.debtTerms.borrowRate == 5_00  # Discount persists
    assert bob_debt_after.amount > bob_debt_before.amount  # Interest accrued


def test_no_discount_when_registry_not_set(
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
    green_token,
    savings_green,
    mission_control,
    credit_engine,
    switchboard_alpha,
    createDebtTerms,
):
    """Test that without underscore registry set, user is treated as regular user"""
    # Do NOT set underscore registry - it should be ZERO_ADDRESS by default
    assert mission_control.underscoreRegistry() == ZERO_ADDRESS

    # Set discount in credit engine (but it won't apply without registry)
    credit_engine.setUnderscoreVaultDiscount(50_00, sender=switchboard_alpha.address)

    # Setup with daowry enabled and 10% borrow rate
    setGeneralConfig()
    debt_terms = createDebtTerms(_borrowRate=10_00, _daowry=5_00)
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig(_isDaowryEnabled=True)

    # Deposit and borrow
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # Verify initial balances
    assert green_token.balanceOf(savings_green) == 0
    assert green_token.balanceOf(bob) == 0

    # Bob borrows - should be treated as regular user
    borrow_amount = 50 * EIGHTEEN_DECIMALS
    bob_amount = teller.borrow(borrow_amount, bob, False, sender=bob)

    # Verify daowry was charged (no waiver)
    bob_log = filter_logs(teller, "NewBorrow")[0]
    expected_daowry = borrow_amount * 5_00 // 100_00
    assert bob_log.daowry == expected_daowry  # Daowry charged
    assert bob_amount == borrow_amount - expected_daowry

    # Verify full interest rate (no discount)
    bob_debt = ledger.userDebt(bob)
    assert bob_debt.debtTerms.borrowRate == 10_00  # Full rate, no discount


def test_interest_accrual_with_discount(
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
    mission_control,
    switchboard_alpha,
    mock_undy_v2,
    createDebtTerms,
):
    """Test that interest accrues at discounted rate over time for Underscore vaults"""
    credit_engine.setUnderscoreVaultDiscount(50_00, sender=switchboard_alpha.address)

    # Setup with 10% borrow rate
    setGeneralConfig()
    debt_terms = createDebtTerms(_borrowRate=10_00)  # 10% annual
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    # Deposit collateral
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # Set prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # Setup underscore registry first
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)

    # Borrow as Underscore vault (with 50% discount, so 5% effective rate)
    borrow_amount = 25 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    # Verify discounted rate was applied
    vault_debt = ledger.userDebt(bob)
    assert vault_debt.debtTerms.borrowRate == 5_00  # 50% discount on 10% = 5%

    # Advance time by 1 year
    boa.env.time_travel(seconds=365 * 24 * 60 * 60)

    # Update debt
    credit_engine.updateDebtForUser(bob, sender=credit_engine.address)

    # Get updated debt
    vault_debt_after = ledger.userDebt(bob)
    vault_interest = vault_debt_after.amount - borrow_amount

    # With 5% rate, interest on 25e18 for 1 year should be approximately 1.25e18
    # Allow some margin for rounding
    expected_min_interest = (borrow_amount * 4_50) // 100_00  # 4.5%
    expected_max_interest = (borrow_amount * 5_50) // 100_00  # 5.5%
    assert vault_interest >= expected_min_interest
    assert vault_interest <= expected_max_interest


def test_set_discount_permissions_and_validation(
    credit_engine,
    switchboard_alpha,
    bob,
):
    """Test setUnderscoreVaultDiscount permissions and validation"""
    # Non-switchboard cannot set discount
    with boa.reverts("only switchboard allowed"):
        credit_engine.setUnderscoreVaultDiscount(50_00, sender=bob)

    # Discount > 100% should fail
    with boa.reverts("invalid discount"):
        credit_engine.setUnderscoreVaultDiscount(100_01, sender=switchboard_alpha.address)

    # Valid discount should succeed
    credit_engine.setUnderscoreVaultDiscount(25_00, sender=switchboard_alpha.address)
    assert credit_engine.undyVaulDiscount() == 25_00

    # 100% discount (max) should succeed
    credit_engine.setUnderscoreVaultDiscount(100_00, sender=switchboard_alpha.address)
    assert credit_engine.undyVaulDiscount() == 100_00

    # 0% discount should succeed (disables discount)
    credit_engine.setUnderscoreVaultDiscount(0, sender=switchboard_alpha.address)
    assert credit_engine.undyVaulDiscount() == 0


def test_view_functions_return_discounted_rate(
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
    mission_control,
    switchboard_alpha,
    mock_undy_v2,
    createDebtTerms,
):
    """Test that getUserBorrowTerms() and getLatestUserDebtAndTerms() return discounted rates for underscore vaults"""
    # Setup underscore registry and discount
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    credit_engine.setUnderscoreVaultDiscount(50_00, sender=switchboard_alpha.address)

    # Setup with 10% borrow rate
    setGeneralConfig()
    debt_terms = createDebtTerms(_borrowRate=10_00)
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    # Deposit collateral
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # Test getUserBorrowTerms() returns discounted rate BEFORE borrowing
    terms_before_borrow = credit_engine.getUserBorrowTerms(bob, True)
    assert terms_before_borrow.debtTerms.borrowRate == 5_00  # 50% discount on 10%

    # Borrow
    borrow_amount = 25 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    # Test getUserBorrowTerms() returns discounted rate AFTER borrowing
    terms_after_borrow = credit_engine.getUserBorrowTerms(bob, True)
    assert terms_after_borrow.debtTerms.borrowRate == 5_00  # 50% discount on 10%

    # Test getLatestUserDebtAndTerms() returns discounted rate in bt
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, True)
    assert bt.debtTerms.borrowRate == 5_00  # 50% discount on 10%
    assert user_debt.debtTerms.borrowRate == 5_00  # Stored debt also has discount


def test_discount_with_multiple_collateral_assets(
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
    ledger,
    credit_engine,
    mission_control,
    switchboard_alpha,
    mock_undy_v2,
    createDebtTerms,
):
    """Test that discount applies correctly to weighted average rate across multiple assets"""
    # Setup underscore registry and discount
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    credit_engine.setUnderscoreVaultDiscount(50_00, sender=switchboard_alpha.address)

    setGeneralConfig()

    # Setup alpha with 10% rate, bravo with 20% rate
    alpha_debt_terms = createDebtTerms(_borrowRate=10_00)
    bravo_debt_terms = createDebtTerms(_borrowRate=20_00)
    setAssetConfig(alpha_token, _debtTerms=alpha_debt_terms)
    setAssetConfig(bravo_token, _debtTerms=bravo_debt_terms)
    setGeneralDebtConfig()

    # Deposit equal amounts of both tokens
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    performDeposit(bob, deposit_amount, bravo_token, bravo_token_whale)

    # Set equal prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    bravo_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)
    mock_price_source.setPrice(bravo_token, bravo_price)

    # Borrow
    borrow_amount = 25 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    # Weighted average of 10% and 20% with equal weights = 15%
    # With 50% discount = 7.5% = 7_50
    bob_debt = ledger.userDebt(bob)
    expected_weighted_rate = 15_00  # (10 + 20) / 2
    expected_discounted_rate = expected_weighted_rate * 50_00 // 100_00  # 7_50
    assert bob_debt.debtTerms.borrowRate == expected_discounted_rate


def test_100_percent_discount_results_in_zero_rate(
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
    mission_control,
    switchboard_alpha,
    mock_undy_v2,
    createDebtTerms,
):
    """Test that 100% discount results in 0% borrow rate"""
    # Setup underscore registry and 100% discount
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    credit_engine.setUnderscoreVaultDiscount(100_00, sender=switchboard_alpha.address)

    # Setup with 10% borrow rate
    setGeneralConfig()
    debt_terms = createDebtTerms(_borrowRate=10_00)
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    # Deposit collateral
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # Borrow
    borrow_amount = 25 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    # Verify 0% rate
    bob_debt = ledger.userDebt(bob)
    assert bob_debt.debtTerms.borrowRate == 0  # 100% discount = 0% rate

    # Verify no interest accrues over time
    initial_amount = bob_debt.amount

    # Advance time by 1 year
    boa.env.time_travel(seconds=365 * 24 * 60 * 60)

    # Update debt
    credit_engine.updateDebtForUser(bob, sender=credit_engine.address)

    # Verify no interest accrued
    bob_debt_after = ledger.userDebt(bob)
    assert bob_debt_after.amount == initial_amount  # No interest with 0% rate


def test_0_percent_discount_has_no_effect(
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    ledger,
    credit_engine,
    mission_control,
    switchboard_alpha,
    mock_undy_v2,
    createDebtTerms,
):
    """Test that 0% discount doesn't change rates (same as regular user)"""
    # Setup underscore registry but 0% discount
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    credit_engine.setUnderscoreVaultDiscount(0, sender=switchboard_alpha.address)

    # Setup with 10% borrow rate
    setGeneralConfig()
    debt_terms = createDebtTerms(_borrowRate=10_00)
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    # Deposit collateral for both users
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    performDeposit(alice, deposit_amount, alpha_token, alpha_token_whale)

    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # Bob is underscore vault, alice is not (remove registry temporarily for alice)
    borrow_amount = 25 * EIGHTEEN_DECIMALS

    # Bob borrows (underscore vault with 0% discount)
    teller.borrow(borrow_amount, bob, False, sender=bob)
    bob_debt = ledger.userDebt(bob)

    # Remove registry so alice is regular user
    mission_control.setUnderscoreRegistry(ZERO_ADDRESS, sender=switchboard_alpha.address)

    # Alice borrows (regular user)
    teller.borrow(borrow_amount, alice, False, sender=alice)
    alice_debt = ledger.userDebt(alice)

    # Both should have same rate (0% discount = no effect)
    assert bob_debt.debtTerms.borrowRate == 10_00
    assert alice_debt.debtTerms.borrowRate == 10_00
    assert bob_debt.debtTerms.borrowRate == alice_debt.debtTerms.borrowRate
