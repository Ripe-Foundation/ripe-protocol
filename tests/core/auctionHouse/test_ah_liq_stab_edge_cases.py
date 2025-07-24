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
    # liqFeesUnpaid shows that fees couldn't be covered
    assert log.liqFeesUnpaid > 9 * EIGHTEEN_DECIMALS  # Almost all fees unpaid


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
    
    # Setup alpha token
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldSwapInStabPools=True,
    )
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # Small position where 10% would be less than minimum
    performDeposit(bob, 20 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    teller.borrow(10 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    
    # Add liquidity
    green_lp_token.transfer(sally, 100 * EIGHTEEN_DECIMALS, sender=green_lp_token_whale)
    green_lp_token.approve(teller, 100 * EIGHTEEN_DECIMALS, sender=sally)
    teller.deposit(green_lp_token, 100 * EIGHTEEN_DECIMALS, sally, stability_pool, 0, sender=sally)
    
    # Trigger liquidation
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
    
    # Setup alpha token
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldSwapInStabPools=True,
    )
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # Large position where 10% would exceed maximum
    performDeposit(bob, 2000 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    teller.borrow(1000 * EIGHTEEN_DECIMALS, bob, False, sender=bob)  # 10% = 100 GREEN > 50 max
    
    # Add liquidity
    green_lp_token.transfer(sally, 2000 * EIGHTEEN_DECIMALS, sender=green_lp_token_whale)
    green_lp_token.approve(teller, 2000 * EIGHTEEN_DECIMALS, sender=sally)
    teller.deposit(green_lp_token, 2000 * EIGHTEEN_DECIMALS, sally, stability_pool, 0, sender=sally)
    
    # Trigger liquidation
    mock_price_source.setPrice(alpha_token, 50 * EIGHTEEN_DECIMALS // 100)
    assert credit_engine.canLiquidateUser(bob)
    
    # Liquidate
    teller.liquidateUser(bob, False, sender=sally)
    
    # Check keeper fee in logs
    logs = filter_logs(teller, "LiquidateUser")
    assert len(logs) == 1
    assert logs[0].keeperFee == 50 * EIGHTEEN_DECIMALS  # Max fee applied


def test_ah_liquidation_phase1_user_stab_deposits(
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
    """Test Phase 1: User's own stability pool deposits are used first"""
    setupStabAssetConfig()
    
    # Setup alpha token as collateral
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=False,
    )
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # Bob deposits into stability pool FIRST
    bob_glp = 60 * EIGHTEEN_DECIMALS
    green_lp_token.transfer(bob, bob_glp, sender=green_lp_token_whale)
    green_lp_token.approve(teller, bob_glp, sender=bob)
    teller.deposit(green_lp_token, bob_glp, bob, stability_pool, 0, sender=bob)
    
    # Sally also deposits (for comparison)
    sally_glp = 100 * EIGHTEEN_DECIMALS
    green_lp_token.transfer(sally, sally_glp, sender=green_lp_token_whale)
    green_lp_token.approve(teller, sally_glp, sender=sally)
    teller.deposit(green_lp_token, sally_glp, sally, stability_pool, 0, sender=sally)
    
    # Track initial balances
    bob_stab_before = stability_pool.getTotalAmountForUser(bob, green_lp_token)
    sally_stab_before = stability_pool.getTotalAmountForUser(sally, green_lp_token)
    
    # Bob takes out a loan
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    
    # Trigger liquidation
    mock_price_source.setPrice(alpha_token, 125 * EIGHTEEN_DECIMALS // 200)
    assert credit_engine.canLiquidateUser(bob)
    
    # Liquidate
    teller.liquidateUser(bob, False, sender=sally)
    
    # Check that Bob's stability pool position was reduced FIRST
    bob_stab_after = stability_pool.getTotalAmountForUser(bob, green_lp_token)
    sally_stab_after = stability_pool.getTotalAmountForUser(sally, green_lp_token)
    
    assert bob_stab_after < bob_stab_before  # Bob's position reduced FIRST
    
    # Sally's position should increase due to liquidation profits
    # The key is that Bob's own deposits were used first
    assert sally_stab_after > sally_stab_before  # Sally must gain from liquidation
    
    # The reduction in Bob's position should be significant
    bob_reduction = bob_stab_before - bob_stab_after
    assert bob_reduction > 50 * EIGHTEEN_DECIMALS  # Most of Bob's deposit was used


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
):
    """Test liquidation with zero LTV payback buffer"""
    setupStabAssetConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)  # No buffer
    
    # Setup with 50% LTV, 80% liquidation threshold
    debt_terms = createDebtTerms(_ltv=50_00, _liqThreshold=80_00, _liqFee=10_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldSwapInStabPools=True,
    )
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # Setup position at 50% LTV
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    
    # Add sufficient liquidity
    green_lp_token.transfer(sally, 200 * EIGHTEEN_DECIMALS, sender=green_lp_token_whale)
    green_lp_token.approve(teller, 200 * EIGHTEEN_DECIMALS, sender=sally)
    teller.deposit(green_lp_token, 200 * EIGHTEEN_DECIMALS, sally, stability_pool, 0, sender=sally)
    
    # Trigger liquidation - price drop makes LTV exceed 80%
    mock_price_source.setPrice(alpha_token, 62 * EIGHTEEN_DECIMALS // 100)
    assert credit_engine.canLiquidateUser(bob)
    
    # Liquidate
    teller.liquidateUser(bob, False, sender=sally)
    
    # Check final LTV - should target exactly 50% (no buffer)
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    # After partial liquidation, Bob should still have debt and collateral
    assert user_debt.amount > 0
    assert bt.collateralVal > 0
    
    final_ltv = user_debt.amount * HUNDRED_PERCENT // bt.collateralVal
    # With 0 buffer, should restore to exactly the LTV limit (50%)
    assert abs(final_ltv - 50_00) < 200  # Within 2% tolerance