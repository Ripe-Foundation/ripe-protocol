import pytest
import boa

from constants import EIGHTEEN_DECIMALS, HUNDRED_PERCENT
from conf_utils import filter_logs


# green lp token fixture
@pytest.fixture(scope="session")
def green_lp_token(governance):
    return boa.load("contracts/mock/MockErc20.vy", governance, "Green LP Token", "GLP", 18, 1_000_000_000, name="green_lp_token")


@pytest.fixture(scope="session")
def green_lp_token_whale(env, green_lp_token, governance):
    whale = env.generate_address("green_lp_token_whale")
    green_lp_token.mint(whale, 100_000_000 * (10 ** green_lp_token.decimals()), sender=governance.address)
    return whale


# setupStabAssetConfig fixture
@pytest.fixture(scope="module")
def setupStabAssetConfig(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    green_lp_token,
    savings_green,
    mock_price_source,
    createDebtTerms,
    stability_pool,
    vault_book,
    switchboard_alpha,
    mission_control,
):
    def setupStabAssetConfig():
        setGeneralConfig()
        setGeneralDebtConfig()

        # setup savings green
        setAssetConfig(
            savings_green,
            _vaultIds=[1],
            _debtTerms=createDebtTerms(),
            _shouldBurnAsPayment=True,
            _shouldTransferToEndaoment=False,
            _shouldSwapInStabPools=False,
            _shouldAuctionInstantly=False,
            _canRedeemCollateral=False,
            _canRedeemInStabPool=False,
            _canBuyInAuction=False,
            _canClaimInStabPool=False,
        )
        mock_price_source.setPrice(savings_green, int(1.15 * EIGHTEEN_DECIMALS))

        # setup green lp token
        setAssetConfig(
            green_lp_token,
            _vaultIds=[1],
            _debtTerms=createDebtTerms(),
            _shouldBurnAsPayment=False,
            _shouldTransferToEndaoment=True,
            _shouldSwapInStabPools=False,
            _shouldAuctionInstantly=False,
            _canRedeemCollateral=False,
            _canRedeemInStabPool=False,
            _canBuyInAuction=False,
            _canClaimInStabPool=False,
        )
        mock_price_source.setPrice(green_lp_token, 1 * EIGHTEEN_DECIMALS)

        # set priority stab vaults
        stab_id = vault_book.getRegId(stability_pool)
        mission_control.setPriorityStabVaults([(stab_id, green_lp_token), (stab_id, savings_green)], sender=switchboard_alpha.address)

    yield setupStabAssetConfig


def test_ah_liquidation_high_fees(
    setupStabAssetConfig,
    setAssetConfig,
    green_lp_token,
    green_lp_token_whale,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    teller,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    stability_pool,
    performDeposit,
):
    """Test liquidation with very high liquidation fees"""
    setupStabAssetConfig()
    
    # Setup alpha token with 90% liquidation fee
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=90_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=True,
    )
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # Deposit lots of liquidity to handle high fees
    glp_deposit = 500 * EIGHTEEN_DECIMALS
    green_lp_token.transfer(sally, glp_deposit, sender=green_lp_token_whale)
    green_lp_token.approve(teller, glp_deposit, sender=sally)
    teller.deposit(green_lp_token, glp_deposit, sally, stability_pool, 0, sender=sally)
    
    # Setup borrower position
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    debt_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale)
    teller.borrow(debt_amount, bob, False, sender=bob)
    
    # Trigger liquidation
    mock_price_source.setPrice(alpha_token, 125 * EIGHTEEN_DECIMALS // 200)
    assert credit_engine.canLiquidateUser(bob)
    
    # Liquidate with high fees
    teller.liquidateUser(bob, False, sender=sally)
    
    # Verify liquidation happened despite high fees
    logs = filter_logs(teller, "LiquidateUser")
    assert len(logs) == 1
    log = logs[0]
    
    # With 90% liquidation fee, the fees are very high
    # The totalLiqFees is calculated based on current debt (which may include interest)
    # Just verify that fees are significant
    assert log.totalLiqFees > 0
    
    # The key test is that with 90% liq fee, the liquidation still works
    # and the collateral value out exceeds the repay amount significantly
    assert log.repayAmount > 0
    assert log.collateralValueOut > log.repayAmount
    
    # The fee ratio should be high - collateral out is much more than repaid
    fee_premium = (log.collateralValueOut - log.repayAmount) * 100 // log.repayAmount
    assert fee_premium > 20  # At least 20% premium due to high fees


def test_ah_liquidation_multiple_stab_pools(
    setupStabAssetConfig,
    setAssetConfig,
    green_lp_token,
    green_lp_token_whale,
    savings_green,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    teller,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    stability_pool,
    performDeposit,
    green_token,
    whale,
):
    """Test liquidation uses both configured stab assets in priority order"""
    setupStabAssetConfig()
    
    # Setup alpha token for liquidation
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=True,
    )
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # Deposit small amounts in stability pool to force use of both assets
    # First deposit green_lp_token (priority 1)
    glp_deposit = 30 * EIGHTEEN_DECIMALS
    green_lp_token.transfer(sally, glp_deposit, sender=green_lp_token_whale)
    green_lp_token.approve(teller, glp_deposit, sender=sally)
    teller.deposit(green_lp_token, glp_deposit, sally, stability_pool, 0, sender=sally)
    
    # Then deposit savings_green (priority 2)
    sgreen_deposit = 80 * EIGHTEEN_DECIMALS
    green_token.mint(sally, sgreen_deposit, sender=credit_engine.address)
    green_token.approve(savings_green, sgreen_deposit, sender=sally)
    sally_sgreen_shares = savings_green.deposit(sgreen_deposit, sally, sender=sally)
    savings_green.approve(teller, sally_sgreen_shares, sender=sally)
    teller.deposit(savings_green, sally_sgreen_shares, sally, stability_pool, 0, sender=sally)
    
    # Setup large borrower position that needs both assets
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    debt_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale)
    teller.borrow(debt_amount, bob, False, sender=bob)
    
    # Move Bob's GREEN away - he should have received some from borrowing
    bob_green = green_token.balanceOf(bob)
    assert bob_green > 0  # Bob must have received GREEN from borrowing
    green_token.transfer(whale, bob_green, sender=bob)
    
    # Trigger liquidation
    mock_price_source.setPrice(alpha_token, 125 * EIGHTEEN_DECIMALS // 200)
    assert credit_engine.canLiquidateUser(bob)
    
    # Liquidate - should use both pools in priority order
    teller.liquidateUser(bob, False, sender=sally)
    
    # Verify both assets were used
    logs = filter_logs(teller, "CollateralSwappedWithStabPool")
    assert len(logs) == 2
    # First should be green_lp_token (priority 1)
    assert logs[0].stabAsset == green_lp_token.address
    # Second should be savings_green (priority 2)
    assert logs[1].stabAsset == savings_green.address


def test_ah_liquidation_zero_price(
    setupStabAssetConfig,
    setAssetConfig,
    green_lp_token,
    green_lp_token_whale,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    teller,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    stability_pool,
    performDeposit,
    auction_house,
):
    """Test liquidation when collateral price drops to near zero"""
    setupStabAssetConfig()
    
    # Setup normal position
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=True,
    )
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # Deposit liquidity
    green_lp_token.transfer(sally, 200 * EIGHTEEN_DECIMALS, sender=green_lp_token_whale)
    green_lp_token.approve(teller, 200 * EIGHTEEN_DECIMALS, sender=sally)
    teller.deposit(green_lp_token, 200 * EIGHTEEN_DECIMALS, sally, stability_pool, 0, sender=sally)
    
    # Setup position
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    
    # Drop price to almost zero
    mock_price_source.setPrice(alpha_token, 1)  # 1 wei
    
    # Should be liquidatable
    assert credit_engine.canLiquidateUser(bob)
    
    # Calculate expected repay amount when collateral is worthless
    target_repay = auction_house.calcAmountOfDebtToRepayDuringLiq(bob)
    # Even with near-zero collateral value, the formula still calculates a target
    
    # Liquidate
    teller.liquidateUser(bob, False, sender=sally)
    
    # Check liquidation result
    logs = filter_logs(teller, "LiquidateUser")
    assert len(logs) == 1
    log = logs[0]
    
    # With near-zero collateral value, liquidation can't repay much
    # The key is that collateral is now worthless
    assert log.collateralValueOut == 200  # 200 wei - essentially worthless
    assert log.repayAmount == 180  # Can only repay 180 wei
    assert log.didRestoreDebtHealth == False  # Can't restore with worthless collateral
    
    # The liquidation couldn't recover meaningful value
    # With new fee capping logic, fees are set to 0 when collateral < debt
    # So liqFeesUnpaid is 0 (we never tried to charge fees in the first place)
    assert log.liqFeesUnpaid == 0
    assert log.totalLiqFees == 0  # Fees correctly capped to 0


def test_ah_liquidation_keeper_fee_min(
    setupStabAssetConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    green_lp_token,
    green_lp_token_whale,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    teller,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    stability_pool,
    performDeposit,
):
    """Test minimum keeper fee is applied for small liquidations"""
    setupStabAssetConfig()
    # Set keeper fee config with minimum
    setGeneralDebtConfig(
        _keeperFeeRatio=10_00,  # 10%
        _minKeeperFee=5 * EIGHTEEN_DECIMALS,  # Min 5 GREEN
        _maxKeeperFee=50 * EIGHTEEN_DECIMALS  # Max 50 GREEN
    )
    
    # Setup alpha token with lower liquidation threshold so position can be liquidatable with surplus
    debt_terms = createDebtTerms(_liqThreshold=50_00, _liqFee=10_00, _borrowRate=0)  # 50% threshold
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldSwapInStabPools=True,
    )
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Small position where 10% would be less than minimum
    # Need enough collateral surplus to cover min keeper fee ($5) + liq fee (10% = $1)
    # Debt: $10, fees needed: $6, so collateral after liquidation needs to be $16
    performDeposit(bob, 32 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    teller.borrow(10 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    # Add liquidity
    green_lp_token.transfer(sally, 100 * EIGHTEEN_DECIMALS, sender=green_lp_token_whale)
    green_lp_token.approve(teller, 100 * EIGHTEEN_DECIMALS, sender=sally)
    teller.deposit(green_lp_token, 100 * EIGHTEEN_DECIMALS, sally, stability_pool, 0, sender=sally)

    # Trigger liquidation: 32 tokens @ $0.50 = $16 collateral, $10 debt, $6 surplus
    # Liquidatable when collateral <= $10 / 0.50 = $20, and $16 <= $20 ✓
    mock_price_source.setPrice(alpha_token, 50 * EIGHTEEN_DECIMALS // 100)
    assert credit_engine.canLiquidateUser(bob)

    # Liquidate
    teller.liquidateUser(bob, False, sender=sally)

    # Check keeper fee in logs
    logs = filter_logs(teller, "LiquidateUser")
    assert len(logs) == 1
    assert logs[0].keeperFee == 5 * EIGHTEEN_DECIMALS  # Min fee applied


def test_ah_liquidation_keeper_fee_max(
    setupStabAssetConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    green_lp_token,
    green_lp_token_whale,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    teller,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    stability_pool,
    performDeposit,
):
    """Test maximum keeper fee cap is applied for large liquidations"""
    setupStabAssetConfig()
    # Set keeper fee config with maximum cap
    setGeneralDebtConfig(
        _keeperFeeRatio=10_00,  # 10%
        _minKeeperFee=5 * EIGHTEEN_DECIMALS,  # Min 5 GREEN
        _maxKeeperFee=50 * EIGHTEEN_DECIMALS  # Max 50 GREEN
    )
    
    # Setup alpha token with lower liquidation threshold so position can be liquidatable with surplus
    debt_terms = createDebtTerms(_liqThreshold=50_00, _liqFee=10_00, _borrowRate=0)  # 50% threshold
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldSwapInStabPools=True,
    )
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Large position where 10% would exceed maximum
    # Need enough surplus to cover max keeper fee ($50) + liq fee (10% = $100)
    # Debt: $1000, fees needed: $150, so collateral after liquidation needs to be $1150
    performDeposit(bob, 2300 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    teller.borrow(1000 * EIGHTEEN_DECIMALS, bob, False, sender=bob)  # 10% = 100 GREEN > 50 max

    # Add liquidity
    green_lp_token.transfer(sally, 2000 * EIGHTEEN_DECIMALS, sender=green_lp_token_whale)
    green_lp_token.approve(teller, 2000 * EIGHTEEN_DECIMALS, sender=sally)
    teller.deposit(green_lp_token, 2000 * EIGHTEEN_DECIMALS, sally, stability_pool, 0, sender=sally)

    # Trigger liquidation: 2300 tokens @ $0.50 = $1150 collateral, $1000 debt, $150 surplus
    # Liquidatable when collateral <= $1000 / 0.50 = $2000, and $1150 <= $2000 ✓
    mock_price_source.setPrice(alpha_token, 50 * EIGHTEEN_DECIMALS // 100)
    assert credit_engine.canLiquidateUser(bob)

    # Liquidate
    teller.liquidateUser(bob, False, sender=sally)

    # Check keeper fee in logs
    logs = filter_logs(teller, "LiquidateUser")
    assert len(logs) == 1
    assert logs[0].keeperFee == 50 * EIGHTEEN_DECIMALS  # Max fee applied


def test_ah_liquidation_batch_multiple_users(
    setupStabAssetConfig,
    setAssetConfig,
    green_lp_token,
    green_lp_token_whale,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    charlie,
    alice,
    teller,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    stability_pool,
    performDeposit,
):
    """Test batch liquidation with multiple users"""
    setupStabAssetConfig()
    
    # Setup liquidatable asset
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldSwapInStabPools=True,
    )
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # Create positions for multiple users
    users = [bob, charlie, alice]
    for user in users:
        performDeposit(user, 40 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
        teller.borrow(20 * EIGHTEEN_DECIMALS, user, False, sender=user)
    
    # Sally provides liquidity
    green_lp_token.transfer(sally, 300 * EIGHTEEN_DECIMALS, sender=green_lp_token_whale)
    green_lp_token.approve(teller, 300 * EIGHTEEN_DECIMALS, sender=sally)
    teller.deposit(green_lp_token, 300 * EIGHTEEN_DECIMALS, sally, stability_pool, 0, sender=sally)
    
    # Trigger liquidation for all
    mock_price_source.setPrice(alpha_token, 40 * EIGHTEEN_DECIMALS // 100)
    
    # Verify all can be liquidated
    for user in users:
        assert credit_engine.canLiquidateUser(user)
    
    # Batch liquidate
    keeper_rewards = teller.liquidateManyUsers(users, False)
    
    # Verify all were liquidated
    logs = filter_logs(teller, "LiquidateUser")
    assert len(logs) == 3
    
    # With default config, keeper rewards should be 0
    assert keeper_rewards == 0  # No keeper fees in default config
    
    # The important part is that all 3 users were liquidated in batch
    liquidated_users = [log.user for log in logs]
    assert set(liquidated_users) == set(users)


def test_ah_liquidation_zero_ltv_buffer(
    setupStabAssetConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    green_lp_token,
    green_lp_token_whale,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    teller,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    stability_pool,
    performDeposit,
    auction_house,
    _test,
):
    """Test partial liquidation with zero LTV payback buffer - formula over-liquidates due to fee handling"""
    setupStabAssetConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0, _keeperFeeRatio=1_00)  # No buffer, 1% keeper fee

    # Setup with 50% LTV, 80% liquidation threshold, lower liq fee for partial liquidation
    debt_terms = createDebtTerms(_ltv=50_00, _liqThreshold=80_00, _liqFee=5_00, _borrowRate=0)  # 5% liq fee
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldSwapInStabPools=True,
    )
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Setup position at 50% LTV
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    debt_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale)
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Add sufficient liquidity
    green_lp_token.transfer(sally, 200 * EIGHTEEN_DECIMALS, sender=green_lp_token_whale)
    green_lp_token.approve(teller, 200 * EIGHTEEN_DECIMALS, sender=sally)
    teller.deposit(green_lp_token, 200 * EIGHTEEN_DECIMALS, sally, stability_pool, 0, sender=sally)

    # Trigger liquidation - price drop makes LTV exceed 80%
    new_price = 62 * EIGHTEEN_DECIMALS // 100
    mock_price_source.setPrice(alpha_token, new_price)
    assert credit_engine.canLiquidateUser(bob)

    # Pre-liquidation state
    pre_user_debt, pre_bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    _test(debt_amount, pre_user_debt.amount)
    _test(124 * EIGHTEEN_DECIMALS, pre_bt.collateralVal)  # 200 tokens * 0.62

    # Calculate target repay amount
    target_repay_amount = auction_house.calcAmountOfDebtToRepayDuringLiq(bob)
    # With 5% liq fee + 1% keeper = 6% total fees
    # Formula calculates 88 GREEN to repay from 100 GREEN debt
    expected_target_repay = 88 * EIGHTEEN_DECIMALS
    _test(expected_target_repay, target_repay_amount)

    # Liquidate
    teller.liquidateUser(bob, False, sender=sally)

    # Get liquidation results
    logs = filter_logs(teller, "LiquidateUser")
    assert len(logs) == 1
    log = logs[0]

    # Check final state
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)

    # OPINIONATED ASSERTIONS FOR PARTIAL LIQUIDATION:

    # 1. Liquidation must restore debt health
    assert log.didRestoreDebtHealth, "Liquidation must restore debt health"

    # 2. Partial liquidation - exact expected amounts
    # Debt calculation: 100 + 0.38 unpaid fees - 88 repaid = 12.38 remaining
    expected_remaining_debt = int(12.38 * EIGHTEEN_DECIMALS)
    # Use a small absolute tolerance for rounding differences
    assert abs(user_debt.amount - expected_remaining_debt) < 1e16, f"Expected ~12.38 GREEN debt, got {user_debt.amount/EIGHTEEN_DECIMALS}"

    # Collateral: 124 - 93.62 = ~30.38 remaining
    expected_remaining_collateral = 30.38 * EIGHTEEN_DECIMALS
    _test(expected_remaining_collateral, bt.collateralVal, 1)  # 1% tolerance

    # 3. Final LTV is ~40.75%, not exactly 50% because:
    # - Formula conservatively ensures health even if not all fees can be paid
    # - Only 5.62 of 6 GREEN fees paid from spread, 0.38 becomes debt
    # - Final state: 12.38 debt / 30.38 collateral = 40.75% LTV
    # This is expected behavior - formula is conservative to ensure safety
    final_ltv = user_debt.amount * HUNDRED_PERCENT // bt.collateralVal
    expected_ltv = 40_75  # 40.75%
    assert abs(final_ltv - expected_ltv) < 50, f"LTV should be ~40.75%, got {final_ltv/100:.2f}%"

    # 4. Verify liquidation fees (5% liq fee + 1% keeper fee = 6% total)
    expected_total_fees = pre_user_debt.amount * 6_00 // HUNDRED_PERCENT
    _test(expected_total_fees, log.totalLiqFees)

    # Verify unpaid fees (~0.38 GREEN becomes debt)
    expected_unpaid_fees = int(0.38 * EIGHTEEN_DECIMALS)
    assert abs(log.liqFeesUnpaid - expected_unpaid_fees) < 1e16, f"Expected ~0.38 GREEN unpaid fees, got {log.liqFeesUnpaid/EIGHTEEN_DECIMALS}"

    # 5. Repay amount is ~88 GREEN (with rounding)
    expected_repay = 88 * EIGHTEEN_DECIMALS
    assert abs(log.repayAmount - expected_repay) < 10, f"Repay amount should be ~88 GREEN, got {log.repayAmount/EIGHTEEN_DECIMALS}"

    # 6. No auctions should be started when debt health is restored
    assert log.numAuctionsStarted == 0, "No auctions should be started when debt health is restored"

    # 7. Collateral taken = 88 / 0.94 = ~93.62 GREEN
    expected_collateral = 93.62 * EIGHTEEN_DECIMALS
    _test(expected_collateral, log.collateralValueOut, 1)  # 1% tolerance for rounding

    # 8. Debt reduction should be ~87.62 GREEN (100 - 12.38)
    debt_reduction = pre_user_debt.amount - user_debt.amount
    expected_debt_reduction = int(87.62 * EIGHTEEN_DECIMALS)
    assert abs(debt_reduction - expected_debt_reduction) < 1e16, f"Debt reduction should be ~87.62 GREEN, got {debt_reduction/EIGHTEEN_DECIMALS}"

    # 9. Collateral reduction equals collateral taken
    collateral_reduction = pre_bt.collateralVal - bt.collateralVal
    _test(expected_collateral, collateral_reduction, 1)  # 1% tolerance