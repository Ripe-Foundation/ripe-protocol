import boa

from constants import EIGHTEEN_DECIMALS
from conf_utils import filter_logs


def test_buyback_default_behavior_no_split(
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
    ripe_hq,
    credit_engine,
    createDebtTerms,
):
    """Test that with buybackRatio = 0 (default), all revenue goes to Savings Green"""
    # Verify default buyback ratio is 0
    assert credit_engine.buybackRatio() == 0

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

    # Get governance wallet address
    gov_wallet = ripe_hq.governance()

    # Verify initial balances
    assert green_token.balanceOf(savings_green) == 0
    assert green_token.balanceOf(gov_wallet) == 0

    # Borrow
    borrow_amount = 50 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    # Calculate expected daowry
    expected_daowry = borrow_amount * 5_00 // 100_00

    # Verify all revenue went to Savings Green (no split)
    assert green_token.balanceOf(savings_green) == expected_daowry
    assert green_token.balanceOf(gov_wallet) == 0


def test_buyback_basic_revenue_split(
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
    ripe_hq,
    credit_engine,
    switchboard_alpha,
    createDebtTerms,
):
    """Test basic revenue split with buyback ratio set to 20%"""
    # Set buyback ratio to 20%
    credit_engine.setBuybackRatio(20_00, sender=switchboard_alpha.address)
    assert credit_engine.buybackRatio() == 20_00

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

    # Get governance wallet address
    gov_wallet = ripe_hq.governance()

    # Verify initial balances
    assert green_token.balanceOf(savings_green) == 0
    assert green_token.balanceOf(gov_wallet) == 0

    # Borrow
    borrow_amount = 50 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    # Calculate expected amounts
    expected_daowry = borrow_amount * 5_00 // 100_00
    expected_for_gov = expected_daowry * 20_00 // 100_00
    expected_for_savings = expected_daowry - expected_for_gov

    # Verify split
    assert green_token.balanceOf(gov_wallet) == expected_for_gov
    assert green_token.balanceOf(savings_green) == expected_for_savings


def test_buyback_50_percent_split(
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
    ripe_hq,
    credit_engine,
    switchboard_alpha,
    createDebtTerms,
):
    """Test 50/50 revenue split"""
    # Set buyback ratio to 50%
    credit_engine.setBuybackRatio(50_00, sender=switchboard_alpha.address)

    # Setup with daowry enabled
    setGeneralConfig()
    debt_terms = createDebtTerms(_daowry=10_00)  # 10% origination fee
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig(_isDaowryEnabled=True)

    # Deposit collateral
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # Set prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # Get governance wallet address
    gov_wallet = ripe_hq.governance()

    # Borrow - with 50% LTV and 100 collateral, max borrow is 50 GREEN
    borrow_amount = 50 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    # Calculate expected amounts
    expected_daowry = borrow_amount * 10_00 // 100_00  # 5 GREEN
    expected_for_gov = expected_daowry * 50_00 // 100_00  # 2.5 GREEN
    expected_for_savings = expected_daowry - expected_for_gov  # 2.5 GREEN

    # Verify 50/50 split
    assert green_token.balanceOf(gov_wallet) == expected_for_gov
    assert green_token.balanceOf(savings_green) == expected_for_savings
    assert green_token.balanceOf(gov_wallet) == green_token.balanceOf(savings_green)


def test_buyback_100_percent_all_to_governance(
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
    ripe_hq,
    credit_engine,
    switchboard_alpha,
    createDebtTerms,
):
    """Test that 100% ratio sends all revenue to governance"""
    # Set buyback ratio to 100%
    credit_engine.setBuybackRatio(100_00, sender=switchboard_alpha.address)

    # Setup with daowry enabled
    setGeneralConfig()
    debt_terms = createDebtTerms(_daowry=5_00)
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig(_isDaowryEnabled=True)

    # Deposit collateral
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # Set prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # Get governance wallet address
    gov_wallet = ripe_hq.governance()

    # Borrow
    borrow_amount = 50 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    # Calculate expected amounts
    expected_daowry = borrow_amount * 5_00 // 100_00

    # Verify all revenue went to governance
    assert green_token.balanceOf(gov_wallet) == expected_daowry
    assert green_token.balanceOf(savings_green) == 0


def test_buyback_with_unrealized_yield(
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
    ripe_hq,
    credit_engine,
    switchboard_alpha,
    ledger,
    createDebtTerms,
):
    """Test that buyback ratio applies to both daowry and unrealized yield"""
    # Set buyback ratio to 30%
    credit_engine.setBuybackRatio(30_00, sender=switchboard_alpha.address)

    # Setup with daowry enabled
    setGeneralConfig()
    debt_terms = createDebtTerms(_daowry=5_00)
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig(_isDaowryEnabled=True)

    # Deposit collateral
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # Set prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # Set up unrealized yield in ledger
    user_debt = (0, 0, debt_terms, 0, False)
    unrealized_yield = 10 * EIGHTEEN_DECIMALS
    ledger.setUserDebt(sally, user_debt, unrealized_yield, (0, 0), sender=credit_engine.address)
    assert ledger.unrealizedYield() == unrealized_yield

    # Record balances before borrow
    gov_wallet = ripe_hq.governance()
    assert green_token.balanceOf(savings_green) == 0
    assert green_token.balanceOf(gov_wallet) == 0

    # Borrow - this will flush unrealized yield
    borrow_amount = 25 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    # Get the borrow log to see unrealized yield
    log = filter_logs(teller, "NewBorrow")[0]
    assert log.globalYieldRealized == unrealized_yield

    # Calculate expected amounts
    expected_daowry = borrow_amount * 5_00 // 100_00
    total_revenue = expected_daowry + unrealized_yield
    expected_for_gov = total_revenue * 30_00 // 100_00
    expected_for_savings = total_revenue - expected_for_gov

    # Verify split includes unrealized yield
    assert green_token.balanceOf(gov_wallet) == expected_for_gov
    assert green_token.balanceOf(savings_green) == expected_for_savings
    # Verify unrealized yield was flushed
    assert ledger.unrealizedYield() == 0


def test_buyback_no_daowry_only_unrealized_yield(
    alpha_token,
    alpha_token_whale,
    bob,
    charlie,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    green_token,
    savings_green,
    ripe_hq,
    credit_engine,
    switchboard_alpha,
    createDebtTerms,
):
    """Test buyback split when there's no daowry but there is unrealized yield"""
    # Set buyback ratio to 40%
    credit_engine.setBuybackRatio(40_00, sender=switchboard_alpha.address)

    # Setup with daowry DISABLED
    setGeneralConfig()
    debt_terms = createDebtTerms(_borrowRate=10_00)
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig(_isDaowryEnabled=False)

    # Deposit collateral
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # Set prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # First borrow to generate debt
    borrow_amount = 25 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    # Advance time to accrue interest
    boa.env.time_travel(seconds=365 * 24 * 60 * 60)  # 1 year

    # Record balances before second borrow
    gov_wallet = ripe_hq.governance()
    savings_balance_before = green_token.balanceOf(savings_green)
    gov_balance_before = green_token.balanceOf(gov_wallet)

    # Use different user for second borrow to avoid hitting per-user debt limit
    performDeposit(charlie, deposit_amount, alpha_token, alpha_token_whale)

    # Second borrow - this will flush unrealized yield
    teller.borrow(borrow_amount, charlie, False, sender=charlie)

    # Get the borrow log
    log = filter_logs(teller, "NewBorrow")[0]
    unrealized_yield = log.globalYieldRealized
    assert log.daowry == 0  # No daowry

    # Calculate expected amounts (only unrealized yield, no daowry)
    expected_for_gov = unrealized_yield * 40_00 // 100_00
    expected_for_savings = unrealized_yield - expected_for_gov

    # Verify split
    gov_balance_after = green_token.balanceOf(gov_wallet)
    savings_balance_after = green_token.balanceOf(savings_green)

    gov_received = gov_balance_after - gov_balance_before
    savings_received = savings_balance_after - savings_balance_before

    assert gov_received == expected_for_gov
    assert savings_received == expected_for_savings


def test_buyback_multiple_borrows_accumulate(
    alpha_token,
    alpha_token_whale,
    bob,
    charlie,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    green_token,
    savings_green,
    ripe_hq,
    credit_engine,
    switchboard_alpha,
    createDebtTerms,
):
    """Test that multiple borrows accumulate revenue in governance wallet"""
    # Set buyback ratio to 25%
    credit_engine.setBuybackRatio(25_00, sender=switchboard_alpha.address)

    # Setup with daowry enabled
    setGeneralConfig()
    debt_terms = createDebtTerms(_daowry=4_00)  # 4% origination fee
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig(_isDaowryEnabled=True)

    # Set prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # Get governance wallet address
    gov_wallet = ripe_hq.governance()

    # Deposit for bob
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # First borrow (bob)
    borrow_amount = 30 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    daowry1 = borrow_amount * 4_00 // 100_00
    expected_gov1 = daowry1 * 25_00 // 100_00
    expected_savings1 = daowry1 - expected_gov1

    # Verify first borrow split
    assert green_token.balanceOf(gov_wallet) == expected_gov1
    assert green_token.balanceOf(savings_green) == expected_savings1

    # Deposit for charlie
    performDeposit(charlie, deposit_amount, alpha_token, alpha_token_whale)

    # Second borrow (charlie)
    teller.borrow(borrow_amount, charlie, False, sender=charlie)

    daowry2 = borrow_amount * 4_00 // 100_00
    expected_gov2 = daowry2 * 25_00 // 100_00
    expected_savings2 = daowry2 - expected_gov2

    # Verify accumulated amounts
    assert green_token.balanceOf(gov_wallet) == expected_gov1 + expected_gov2
    assert green_token.balanceOf(savings_green) == expected_savings1 + expected_savings2


def test_buyback_ratio_can_be_changed_dynamically(
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
    ripe_hq,
    credit_engine,
    switchboard_alpha,
    createDebtTerms,
):
    """Test that buyback ratio can be changed between borrows"""
    # Setup
    setGeneralConfig()
    debt_terms = createDebtTerms(_daowry=10_00)
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig(_isDaowryEnabled=True)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    gov_wallet = ripe_hq.governance()
    borrow_amount = 20 * EIGHTEEN_DECIMALS

    # First borrow with 20% ratio
    credit_engine.setBuybackRatio(20_00, sender=switchboard_alpha.address)
    teller.borrow(borrow_amount, bob, False, sender=bob)

    daowry = borrow_amount * 10_00 // 100_00
    expected_gov1 = daowry * 20_00 // 100_00

    gov_balance1 = green_token.balanceOf(gov_wallet)
    assert gov_balance1 == expected_gov1

    # Change ratio to 50%
    credit_engine.setBuybackRatio(50_00, sender=switchboard_alpha.address)

    # Second borrow with new 50% ratio
    teller.borrow(borrow_amount, bob, False, sender=bob)

    expected_gov2 = daowry * 50_00 // 100_00

    # Verify new split is applied
    gov_balance2 = green_token.balanceOf(gov_wallet)
    assert gov_balance2 == expected_gov1 + expected_gov2


def test_set_buyback_ratio_permissions_and_validation(
    credit_engine,
    switchboard_alpha,
    bob,
):
    """Test setBuybackRatio permissions and validation"""
    # Non-switchboard cannot set ratio
    with boa.reverts("only switchboard allowed"):
        credit_engine.setBuybackRatio(50_00, sender=bob)

    # Ratio > 100% should fail
    with boa.reverts("invalid ratio"):
        credit_engine.setBuybackRatio(100_01, sender=switchboard_alpha.address)

    # Valid ratio should succeed
    credit_engine.setBuybackRatio(25_00, sender=switchboard_alpha.address)
    assert credit_engine.buybackRatio() == 25_00

    # 100% ratio (max) should succeed
    credit_engine.setBuybackRatio(100_00, sender=switchboard_alpha.address)
    assert credit_engine.buybackRatio() == 100_00

    # 0% ratio should succeed (disables buyback)
    credit_engine.setBuybackRatio(0, sender=switchboard_alpha.address)
    assert credit_engine.buybackRatio() == 0


def test_set_buyback_ratio_emits_event(
    credit_engine,
    switchboard_alpha,
):
    """Test that setBuybackRatio emits BuybackRatioSet event"""
    # Set ratio and check event
    credit_engine.setBuybackRatio(30_00, sender=switchboard_alpha.address)

    logs = filter_logs(credit_engine, "BuybackRatioSet")
    assert len(logs) == 1
    assert logs[0].ratio == 30_00

    # Change ratio and verify new event
    credit_engine.setBuybackRatio(75_00, sender=switchboard_alpha.address)

    logs = filter_logs(credit_engine, "BuybackRatioSet")
    assert len(logs) == 1  # filter_logs returns most recent tx only
    assert logs[0].ratio == 75_00


def test_set_buyback_ratio_cannot_be_called_when_paused(
    credit_engine,
    switchboard_alpha,
):
    """Test that setBuybackRatio cannot be called when contract is paused"""
    # Pause the credit engine directly
    credit_engine.pause(True, sender=switchboard_alpha.address)
    assert credit_engine.isPaused()

    # Attempt to set ratio should fail
    with boa.reverts("contract paused"):
        credit_engine.setBuybackRatio(30_00, sender=switchboard_alpha.address)

    # Unpause
    credit_engine.pause(False, sender=switchboard_alpha.address)

    # Should succeed now
    credit_engine.setBuybackRatio(30_00, sender=switchboard_alpha.address)
    assert credit_engine.buybackRatio() == 30_00


def test_buyback_ratio_initialized_to_zero(
    credit_engine,
):
    """Test that buybackRatio is initialized to 0 (disabled by default)"""
    assert credit_engine.buybackRatio() == 0


def test_buyback_small_amounts_precision(
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
    ripe_hq,
    credit_engine,
    switchboard_alpha,
    createDebtTerms,
):
    """Test that buyback split works correctly with small amounts"""
    # Set buyback ratio to 33.33%
    credit_engine.setBuybackRatio(33_33, sender=switchboard_alpha.address)

    # Setup with small daowry
    setGeneralConfig()
    debt_terms = createDebtTerms(_daowry=1_00)  # 1% origination fee
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig(_isDaowryEnabled=True)

    # Deposit collateral
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # Set prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # Get governance wallet address
    gov_wallet = ripe_hq.governance()

    # Small borrow
    borrow_amount = 1 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    # Calculate expected amounts
    expected_daowry = borrow_amount * 1_00 // 100_00  # 0.01 GREEN
    expected_for_gov = expected_daowry * 33_33 // 100_00
    expected_for_savings = expected_daowry - expected_for_gov

    # Verify split (accounting for precision)
    gov_balance = green_token.balanceOf(gov_wallet)
    savings_balance = green_token.balanceOf(savings_green)

    assert gov_balance == expected_for_gov
    assert savings_balance == expected_for_savings
    # Verify total adds up
    assert gov_balance + savings_balance == expected_daowry


def test_buyback_with_underscore_vault_no_daowry(
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
    ripe_hq,
    credit_engine,
    switchboard_alpha,
    mission_control,
    mock_undy_v2,
    ledger,
    createDebtTerms,
):
    """Test that underscore vaults don't pay daowry, so buyback only applies to unrealized yield"""
    # Set buyback ratio to 30%
    credit_engine.setBuybackRatio(30_00, sender=switchboard_alpha.address)

    # Setup underscore registry
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)

    # Setup with daowry enabled
    setGeneralConfig()
    debt_terms = createDebtTerms(_daowry=5_00)
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig(_isDaowryEnabled=True)

    # Deposit collateral
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # Set prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # Set up unrealized yield in ledger
    user_debt = (0, 0, debt_terms, 0, False)
    unrealized_yield = 8 * EIGHTEEN_DECIMALS
    ledger.setUserDebt(sally, user_debt, unrealized_yield, (0, 0), sender=credit_engine.address)
    assert ledger.unrealizedYield() == unrealized_yield

    # Get governance wallet address
    gov_wallet = ripe_hq.governance()

    # Verify initial balances
    assert green_token.balanceOf(savings_green) == 0
    assert green_token.balanceOf(gov_wallet) == 0

    # Borrow - this will flush unrealized yield
    borrow_amount = 25 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    # Verify no daowry was charged for underscore vault
    log = filter_logs(teller, "NewBorrow")[0]
    assert log.daowry == 0
    assert log.globalYieldRealized == unrealized_yield

    # Calculate expected split (only unrealized yield, no daowry)
    expected_for_gov = unrealized_yield * 30_00 // 100_00
    expected_for_savings = unrealized_yield - expected_for_gov

    # Verify split
    assert green_token.balanceOf(gov_wallet) == expected_for_gov
    assert green_token.balanceOf(savings_green) == expected_for_savings
    # Verify unrealized yield was flushed
    assert ledger.unrealizedYield() == 0
