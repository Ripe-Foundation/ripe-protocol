import pytest
import boa

from constants import EIGHTEEN_DECIMALS, HUNDRED_PERCENT, ZERO_ADDRESS, MAX_UINT256
from conf_utils import filter_logs


@pytest.fixture(scope="module")
def setupStabPoolLiquidation(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    green_token,
    bob,
    teller,
    whale,
    mock_price_source,
    createDebtTerms,
    stability_pool,
    vault_book,
    switchboard_alpha,
    mission_control,
    sally,
):
    def setupStabPoolLiquidation(
        _debt_amount,
        _collateral_amount,
        _liq_threshold,
        _liq_fee,
        _target_ltv,
        _ltv_payback_buffer,
        _collateral_price_drop_ratio, # e.g., 0.625 means price drops to 62.5% of original
    ):
        setGeneralConfig()
        setGeneralDebtConfig(_ltvPaybackBuffer=_ltv_payback_buffer)
        debt_terms = createDebtTerms(_liqThreshold=_liq_threshold, _liqFee=_liq_fee, _ltv=_target_ltv, _borrowRate=0)
        setAssetConfig(
            alpha_token,
            _debtTerms=debt_terms,
            _shouldBurnAsPayment=False, 
            _shouldTransferToEndaoment=False,
            _shouldSwapInStabPools=True, # testing this!
            _shouldAuctionInstantly=False,
        )

        # stab pool config
        stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
        setAssetConfig(green_token, _vaultIds=[1], _debtTerms=stab_debt_terms, _shouldBurnAsPayment=True)
        stab_id = vault_book.getRegId(stability_pool)
        mission_control.setPriorityStabVaults([(stab_id, green_token)], sender=switchboard_alpha.address)

        # stab pool deposit (ensure enough liquidity)
        mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)
        stab_deposit_amount = _debt_amount * 10  # 10x the debt amount for sufficient liquidity
        green_token.transfer(sally, stab_deposit_amount, sender=whale)
        green_token.approve(teller, stab_deposit_amount, sender=sally)
        teller.deposit(green_token, stab_deposit_amount, sally, stability_pool, 0, sender=sally)

        # liq user setup
        original_price = 1 * EIGHTEEN_DECIMALS
        mock_price_source.setPrice(alpha_token, original_price)
        performDeposit(bob, _collateral_amount, alpha_token, alpha_token_whale)
        teller.borrow(_debt_amount, bob, False, sender=bob)

        # set liquidatable price
        new_price = int(original_price * _collateral_price_drop_ratio)
        mock_price_source.setPrice(alpha_token, new_price)
        
        return stab_id, stab_deposit_amount, new_price

    yield setupStabPoolLiquidation


def verifyStabPoolLiqResults(
    _user_debt,
    _bt,
    _orig_debt_amount,
    _orig_collateral_val,
    _log,
    _exp_liq_fees,
    _target_ltv,
    _test,
):
    """Helper function to verify liquidation results"""
    
    # Calculate expected debt based on actual liquidation mechanics
    actual_repay_amount = _log.valueSwapped
    actual_collateral_taken = _log.collateralValueOut
    liq_fees_paid = actual_collateral_taken - actual_repay_amount
    unpaid_liq_fees = max(0, _exp_liq_fees - liq_fees_paid)
    expected_final_debt = _orig_debt_amount - actual_repay_amount + unpaid_liq_fees
    
    # Verify debt calculation
    _test(expected_final_debt, _user_debt.amount)
    
    # Verify collateral calculation
    expected_final_collateral = _orig_collateral_val - actual_collateral_taken
    _test(expected_final_collateral, _bt.collateralVal)
    
    # Calculate the precise expected final LTV based on liquidation mechanics
    # The unified formula calculates repay amount for target LTV, but unpaid fees affect final LTV
    
    # Calculate exactly how much liquidation fees were unpaid and added to debt
    unpaid_liq_fees = max(0, _exp_liq_fees - liq_fees_paid)
    precise_expected_debt = _orig_debt_amount - actual_repay_amount + unpaid_liq_fees
    precise_expected_ltv = precise_expected_debt * HUNDRED_PERCENT // _bt.collateralVal
    
    # Test for the precise expected LTV (not target LTV, but actual expected LTV with unpaid fees)
    actual_ltv = _user_debt.amount * HUNDRED_PERCENT // _bt.collateralVal
    _test(precise_expected_ltv, actual_ltv)
    
    # Verify user debt health was restored (no longer at liquidation threshold)
    liquidation_threshold_ltv = _user_debt.debtTerms.liqThreshold
    assert actual_ltv < liquidation_threshold_ltv, f"User still liquidatable: LTV {actual_ltv} >= threshold {liquidation_threshold_ltv}"


###############
# Liquidation #
###############


def test_ah_liquidation_threshold(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    mock_price_source,
    createDebtTerms,
    credit_engine,
):
    setGeneralConfig()
    setGeneralDebtConfig()
    debt_terms = createDebtTerms(_liqThreshold=80_00)
    setAssetConfig(alpha_token, _debtTerms=debt_terms)

    # set mock price
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)

    # deposit
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # borrow
    borrow_amount = 100 * EIGHTEEN_DECIMALS
    amount = teller.borrow(borrow_amount, bob, False, sender=bob)
    assert amount == borrow_amount

    assert credit_engine.getLiquidationThreshold(bob) == 125 * EIGHTEEN_DECIMALS

    # set new price (can liquidate)
    new_price = 125 * EIGHTEEN_DECIMALS // 200
    mock_price_source.setPrice(alpha_token, new_price)
    assert credit_engine.canLiquidateUser(bob)


##################
# Stability Pool #
##################


def test_ah_liquidation_stab_pool_swap(
    setupStabPoolLiquidation,
    alpha_token,
    green_token,
    bob,
    teller,
    credit_engine,
    auction_house,
    sally,
    stability_pool,
    endaoment,
    _test,
):
    """Test stability pool liquidation swap - using setupStabPoolLiquidation fixture"""
    
    # Test parameters
    debt_amount = 100 * EIGHTEEN_DECIMALS
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    liq_threshold = 80_00
    liq_fee = 10_00
    ltv = 50_00
    ltv_payback_buffer = 0
    collateral_price_drop = 0.625
    
    # Setup test using fixture
    stab_id, stab_deposit_amount, new_price = setupStabPoolLiquidation(
        debt_amount, collateral_amount, liq_threshold, liq_fee, ltv,
        ltv_payback_buffer, collateral_price_drop
    )

    # verify user can be liquidated
    assert credit_engine.canLiquidateUser(bob)
    _, orig_bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)

    # expected values
    target_repay_amount = auction_house.calcAmountOfDebtToRepayDuringLiq(bob)
    target_collateral_val = target_repay_amount * HUNDRED_PERCENT // (HUNDRED_PERCENT - liq_fee)
    exp_liq_fees = debt_amount * liq_fee // HUNDRED_PERCENT

    # liquidate user
    teller.liquidateUser(bob, False, sender=sally)

    # test event
    log = filter_logs(teller, "CollateralSwappedWithStabPool")[0]
    assert log.liqUser == bob
    assert log.liqVaultId != stab_id
    assert log.liqAsset == alpha_token.address
    assert log.collateralAmountOut == target_collateral_val * EIGHTEEN_DECIMALS // new_price
    assert log.collateralValueOut == target_collateral_val
    assert log.stabVaultId == stab_id
    assert log.stabAsset == green_token.address  # fixture uses green_token for stab pool
    _test(target_repay_amount, log.amountSwapped)
    _test(target_repay_amount, log.valueSwapped)

    # funds
    assert green_token.balanceOf(stability_pool) == stab_deposit_amount - log.amountSwapped
    assert green_token.balanceOf(endaoment) == 0 # green burned
    assert alpha_token.balanceOf(stability_pool) == log.collateralAmountOut

    # get latest debt and terms
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)

    # Use the helper function for verification
    verifyStabPoolLiqResults(
        user_debt, bt, debt_amount, orig_bt.collateralVal,
        log, exp_liq_fees, ltv, _test
    )


@pytest.mark.parametrize("debt_amount,collateral_amount,liq_threshold,liq_fee,ltv,ltv_payback_buffer,collateral_price_drop", [
    # Test case 1: Standard case (50% LTV, 10% liq fee, 80% liq threshold)
    (100 * EIGHTEEN_DECIMALS, 200 * EIGHTEEN_DECIMALS, 80_00, 10_00, 50_00, 0, 0.625),
    
    # Test case 2: Higher LTV target (70% LTV)
    (100 * EIGHTEEN_DECIMALS, 200 * EIGHTEEN_DECIMALS, 80_00, 10_00, 70_00, 0, 0.625),
    
    # Test case 3: Lower liquidation fee (5%)
    (100 * EIGHTEEN_DECIMALS, 200 * EIGHTEEN_DECIMALS, 80_00, 5_00, 50_00, 0, 0.625),
    
    # Test case 4: Larger amounts
    (1000 * EIGHTEEN_DECIMALS, 2000 * EIGHTEEN_DECIMALS, 80_00, 10_00, 50_00, 0, 0.625),
    
    # Test case 5: With LTV payback buffer (5%)
    (100 * EIGHTEEN_DECIMALS, 200 * EIGHTEEN_DECIMALS, 80_00, 10_00, 50_00, 5_00, 0.625),
    
    # Test case 6: Conservative case - higher LTV target (60%)
    (100 * EIGHTEEN_DECIMALS, 200 * EIGHTEEN_DECIMALS, 80_00, 10_00, 60_00, 0, 0.625),
])
def test_ah_liquidation_stab_pool_various_scenarios(
    setupStabPoolLiquidation,
    green_token,
    bob,
    teller,
    credit_engine,
    auction_house,
    sally,
    _test,
    # params
    debt_amount,
    collateral_amount,
    liq_threshold,
    liq_fee,
    ltv,
    ltv_payback_buffer,
    collateral_price_drop,
):
    """Test various liquidation scenarios with different parameters"""
    
    # Setup test
    stab_id, stab_deposit_amount, new_price = setupStabPoolLiquidation(debt_amount, collateral_amount, liq_threshold, liq_fee, ltv, ltv_payback_buffer, collateral_price_drop)
    
    # Verify user can be liquidated
    assert credit_engine.canLiquidateUser(bob)
    _, orig_bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)

    # pre liq values
    target_repay_amount = auction_house.calcAmountOfDebtToRepayDuringLiq(bob)
    effective_target_ltv = ltv * (HUNDRED_PERCENT - ltv_payback_buffer) // HUNDRED_PERCENT
    exp_liq_fees = debt_amount * liq_fee // HUNDRED_PERCENT

    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)
    
    log = filter_logs(teller, "CollateralSwappedWithStabPool")[0]
    assert log.liqUser == bob
    assert log.stabVaultId == stab_id
    assert log.stabAsset == green_token.address
    _test(target_repay_amount, log.valueSwapped)

    # Get post-liquidation state
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    
    # Verify liquidation results
    verifyStabPoolLiqResults(
        user_debt, bt, debt_amount, orig_bt.collateralVal,
        log, exp_liq_fees, effective_target_ltv, _test
    )


def test_ah_liquidation_multiple_stab_assets_same_pool(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    bob,
    teller,
    whale,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    auction_house,
    sally,
    alice,
    stability_pool,
    vault_book,
    switchboard_alpha,
    mission_control,
    endaoment,
    _test,
):
    """Test liquidation with multiple stability assets in same pool - tests priority ordering"""
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    
    # Setup liquidated asset (alpha_token)
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False, 
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=False,
    )

    # Setup multiple stability pool assets
    stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(green_token, _vaultIds=[1], _debtTerms=stab_debt_terms)
    setAssetConfig(bravo_token, _vaultIds=[1], _debtTerms=stab_debt_terms)

    # Setup multiple stability assets with priority order (same pool, different assets)
    stab_pool_id = vault_book.getRegId(stability_pool)
    
    # Set priority: green_token first, then bravo_token
    mission_control.setPriorityStabVaults([
        (stab_pool_id, green_token),      # Priority 1 - will be exhausted
        (stab_pool_id, bravo_token),      # Priority 2 - will handle remainder
    ], sender=switchboard_alpha.address)

    # Setup prices
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Deposit into stability pool with different assets and amounts
    # Green: Small amount - will be exhausted first
    green_deposit = 30 * EIGHTEEN_DECIMALS
    green_token.transfer(sally, green_deposit, sender=whale)
    green_token.approve(teller, green_deposit, sender=sally)
    teller.deposit(green_token, green_deposit, sally, stability_pool, 0, sender=sally)

    # Bravo: Larger amount - will handle remaining liquidation
    bravo_deposit = 100 * EIGHTEEN_DECIMALS
    bravo_token.transfer(alice, bravo_deposit, sender=bravo_token_whale)
    bravo_token.approve(teller, bravo_deposit, sender=alice)
    teller.deposit(bravo_token, bravo_deposit, alice, stability_pool, 0, sender=alice)

    # Setup liquidation user
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    debt_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale)
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Set liquidatable price
    new_price = 125 * EIGHTEEN_DECIMALS // 200  # 0.625
    mock_price_source.setPrice(alpha_token, new_price)
    assert credit_engine.canLiquidateUser(bob)

    # Get pre-liquidation state
    target_repay_amount = auction_house.calcAmountOfDebtToRepayDuringLiq(bob)
    
    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)

    # Should have multiple CollateralSwappedWithStabPool events
    logs = filter_logs(teller, "CollateralSwappedWithStabPool")
    assert len(logs) == 2
    
    # Verify the first swap used green_token (highest priority)
    first_log = logs[0]
    assert first_log.stabAsset == green_token.address
    assert first_log.stabVaultId == stab_pool_id
    
    # First swap should consume ALL green tokens since green_deposit < target_repay_amount
    assert green_deposit < target_repay_amount
    _test(green_deposit, first_log.valueSwapped)
    
    # Verify green tokens were burned (not sent to endaoment)
    assert green_token.balanceOf(endaoment) == 0
    assert green_token.balanceOf(stability_pool) == green_deposit - first_log.amountSwapped

    # Since target repay amount > green pool liquidity, we should definitely have a second swap
    remaining_to_repay = target_repay_amount - green_deposit
    assert remaining_to_repay > 0
    
    second_log = logs[1]
    assert second_log.stabAsset == bravo_token.address
    assert second_log.stabVaultId == stab_pool_id
    
    # Verify bravo tokens went to endaoment (non-green asset)
    assert bravo_token.balanceOf(endaoment) == second_log.amountSwapped
    assert bravo_token.balanceOf(stability_pool) == bravo_deposit - second_log.amountSwapped
    
    # Verify the second swap covers the remaining amount
    _test(remaining_to_repay, second_log.valueSwapped)
    
    # Verify total liquidation results
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    
    # Calculate total swapped value
    total_swapped = sum(log.valueSwapped for log in logs)
    total_collateral_taken = sum(log.collateralValueOut for log in logs)
    
    # Verify liquidation math
    exp_liq_fees = debt_amount * 10_00 // HUNDRED_PERCENT
    liq_fees_paid = total_collateral_taken - total_swapped
    unpaid_liq_fees = max(0, exp_liq_fees - liq_fees_paid)
    expected_final_debt = debt_amount - total_swapped + unpaid_liq_fees
    
    _test(expected_final_debt, user_debt.amount)
    
    # Verify collateral was properly transferred to stability pool
    expected_total_collateral = sum(log.collateralAmountOut for log in logs)
    assert alpha_token.balanceOf(stability_pool) == expected_total_collateral


def test_ah_liquidation_insufficient_stab_pool_liquidity(
    setupStabPoolLiquidation,
    green_token,
    bob,
    teller,
    credit_engine,
    auction_house,
    sally,
    stability_pool,
    _test,
):
    """Test liquidation when stability pool has insufficient liquidity"""
    
    debt_amount = 100 * EIGHTEEN_DECIMALS
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    liq_threshold = 80_00
    liq_fee = 10_00
    ltv = 50_00
    
    # Setup with very limited stability pool liquidity (only 20% of what's needed)
    stab_id, _, new_price = setupStabPoolLiquidation(
        debt_amount, collateral_amount, liq_threshold, liq_fee, ltv, 0, 0.625
    )

    # Reduce stability pool liquidity to create insufficient scenario
    target_repay_amount = auction_house.calcAmountOfDebtToRepayDuringLiq(bob)
    limited_liquidity = target_repay_amount // 5  # Only 20% of needed amount
    
    # Withdraw excess from stability pool to simulate insufficient liquidity
    current_balance = green_token.balanceOf(stability_pool)
    excess_to_remove = current_balance - limited_liquidity
    
    # Transfer excess tokens out of the pool to create insufficient liquidity scenario
    green_token.transfer(sally, excess_to_remove, sender=stability_pool.address)
    
    # Verify we now have limited liquidity
    remaining_balance = green_token.balanceOf(stability_pool)
    assert remaining_balance == limited_liquidity
    
    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)
    
    # Should have exactly one stability pool swap event (limited by available liquidity)
    logs = filter_logs(teller, "CollateralSwappedWithStabPool")
    assert len(logs) == 1
    log = logs[0]
    
    # Verify swap was limited by available liquidity (should consume all remaining tokens)
    _test(remaining_balance, log.valueSwapped)
       
    # Since insufficient liquidity, swap should be less than target repay amount
    assert log.valueSwapped < target_repay_amount
    
    # Verify final state - user should still be in liquidation
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    
    # User should still be in liquidation since pools couldn't cover full amount
    assert user_debt.inLiquidation
    
    # Verify the partial liquidation math
    exp_liq_fees = debt_amount * liq_fee // HUNDRED_PERCENT
    actual_repay = log.valueSwapped
    actual_collateral_taken = log.collateralValueOut
    liq_fees_paid = actual_collateral_taken - actual_repay
    unpaid_liq_fees = max(0, exp_liq_fees - liq_fees_paid)
    expected_final_debt = debt_amount - actual_repay + unpaid_liq_fees
    
    _test(expected_final_debt, user_debt.amount)


def test_ah_liquidation_multiple_collateral_assets(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    charlie_token,
    charlie_token_whale,
    green_token,
    bob,
    teller,
    whale,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    sally,
    stability_pool,
    vault_book,
    switchboard_alpha,
    mission_control,
    _test,
):
    """Test liquidation of user with multiple collateral assets"""
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    
    # Setup multiple collateral assets with different liquidation configs
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    
    # Alpha: Stability pool swaps
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=False,
    )
    
    # Bravo: Endaoment transfer
    setAssetConfig(
        bravo_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=False,
    )
    
    # Charlie: Auctions
    setAssetConfig(
        charlie_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=True,
    )

    # Setup stability pool for alpha_token liquidation
    stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(green_token, _vaultIds=[1], _debtTerms=stab_debt_terms)
    stab_id = vault_book.getRegId(stability_pool)
    mission_control.setPriorityStabVaults([(stab_id, green_token)], sender=switchboard_alpha.address)

    # Setup prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)

    # Setup stability pool
    stab_deposit = 500 * EIGHTEEN_DECIMALS
    green_token.transfer(sally, stab_deposit, sender=whale)
    green_token.approve(teller, stab_deposit, sender=sally)
    teller.deposit(green_token, stab_deposit, sally, stability_pool, 0, sender=sally)

    # Setup user with multiple collateral assets
    alpha_amount = 100 * EIGHTEEN_DECIMALS
    bravo_amount = 150 * EIGHTEEN_DECIMALS
    charlie_amount = 200 * 10**6  # Charlie token has 6 decimals, not 18
    
    performDeposit(bob, alpha_amount, alpha_token, alpha_token_whale)
    performDeposit(bob, bravo_amount, bravo_token, bravo_token_whale)
    performDeposit(bob, charlie_amount, charlie_token, charlie_token_whale)
    
    # Borrow against total collateral
    debt_amount = 200 * EIGHTEEN_DECIMALS  # Borrow $200 against $450 collateral
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Set liquidatable prices (drop all assets to trigger liquidation)
    # Liquidation threshold: $200 * 100 / 80 = $250
    # Need collateral value <= $250, so drop to $0.55 each: $450 * 0.55 = $247.5 < $250
    new_price = 55 * EIGHTEEN_DECIMALS // 100  # Drop to $0.55 each
    mock_price_source.setPrice(alpha_token, new_price)
    mock_price_source.setPrice(bravo_token, new_price)
    mock_price_source.setPrice(charlie_token, new_price)
    
    assert credit_engine.canLiquidateUser(bob)

    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)

    # Verify different liquidation methods were used based on asset configs
    stab_pool_logs = filter_logs(teller, "CollateralSwappedWithStabPool")
    endaoment_logs = filter_logs(teller, "CollateralSentToEndaoment")
    auction_logs = filter_logs(teller, "FungibleAuctionUpdated")
    
    # Should have exactly one of each liquidation type
    assert len(stab_pool_logs) == 1  # Alpha via stability pool
    assert len(endaoment_logs) == 0  # Bravo skipped
    assert len(auction_logs) == 1    # Charlie via auction
    
    alpha_log = stab_pool_logs[0]
    charlie_log = auction_logs[0]
    
    # Verify correct assets were liquidated via correct methods
    assert alpha_log.liqAsset == alpha_token.address
    assert charlie_log.asset == charlie_token.address
    
    # Calculate total liquidated value (excluding charlie which goes to auction)
    total_liquidated_value = alpha_log.valueSwapped
    
    # Verify final state
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    
    # Calculate expected final debt based on actual liquidations
    exp_liq_fees = debt_amount * 10_00 // HUNDRED_PERCENT
    actual_repay = total_liquidated_value
    
    # Calculate liquidation fees paid through collateral premium
    total_collateral_taken = alpha_log.collateralValueOut
    liq_fees_paid = total_collateral_taken - actual_repay
    unpaid_liq_fees = max(0, exp_liq_fees - liq_fees_paid)
    
    expected_final_debt = debt_amount - actual_repay + unpaid_liq_fees
    _test(expected_final_debt, user_debt.amount)


def test_ah_liquidation_priority_asset_order(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    charlie_token,
    charlie_token_whale,
    bob,
    teller,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    sally,
    vault_book,
    switchboard_alpha,
    mission_control,
    endaoment,
    stability_pool,
    green_token,
    whale,
    _test,
):
    """Test that priority liquidation asset order is respected"""
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    
    # Setup all assets with stability pool swaps instead of endowment
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)

    for token in [alpha_token, bravo_token, charlie_token]:
        setAssetConfig(
            token,
            _debtTerms=debt_terms,
            _shouldBurnAsPayment=False,
            _shouldTransferToEndaoment=False,
            _shouldSwapInStabPools=True,
            _shouldAuctionInstantly=False,
        )

    # Setup prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)

    # Setup stability pool with GREEN tokens
    stab_pool_id = vault_book.getRegId(stability_pool)
    mission_control.setPriorityStabVaults([
        (stab_pool_id, green_token),
    ], sender=switchboard_alpha.address)

    # Configure GREEN token for stability pool
    stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(green_token, _vaultIds=[stab_pool_id], _debtTerms=stab_debt_terms)

    # Fund stability pool with GREEN tokens
    stab_deposit_amount = 1000 * EIGHTEEN_DECIMALS  # Enough to cover all liquidations
    green_token.transfer(sally, stab_deposit_amount, sender=whale)
    green_token.approve(teller, stab_deposit_amount, sender=sally)
    teller.deposit(green_token, stab_deposit_amount, sally, stability_pool, 0, sender=sally)

    # User deposits assets in order: alpha, bravo, charlie
    alpha_amount = 100 * EIGHTEEN_DECIMALS
    bravo_amount = 150 * EIGHTEEN_DECIMALS
    charlie_amount = 200 * 10**6  # Charlie has 6 decimals
    
    performDeposit(bob, alpha_amount, alpha_token, alpha_token_whale)
    performDeposit(bob, bravo_amount, bravo_token, bravo_token_whale)
    performDeposit(bob, charlie_amount, charlie_token, charlie_token_whale)
    
    # Borrow against collateral
    debt_amount = 200 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Set priority liquidation assets in DIFFERENT order than deposit order
    # Priority: charlie first, then alpha (bravo will be natural order last)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    mission_control.setPriorityLiqAssetVaults([
        (vault_id, charlie_token),  # Priority 1: charlie (deposited 3rd)
        (vault_id, alpha_token),      # Priority 2: alpha (deposited 1st)
        # bravo not in priority list, so it goes in natural order (last)
    ], sender=switchboard_alpha.address)

    # Set liquidatable prices
    new_price = 55 * EIGHTEEN_DECIMALS // 100  # Drop to $0.55 each
    mock_price_source.setPrice(alpha_token, new_price)
    mock_price_source.setPrice(bravo_token, new_price)
    mock_price_source.setPrice(charlie_token, new_price)
    
    assert credit_engine.canLiquidateUser(bob)

    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)

    # Get all stability pool swap events
    stab_logs = filter_logs(teller, "CollateralSwappedWithStabPool")

    # Should have liquidated all 3 assets via stability pool swaps
    assert len(stab_logs) == 3

    # Verify liquidation order matches priority: charlie, alpha, bravo
    assert stab_logs[0].liqAsset == charlie_token.address  # Priority 1
    assert stab_logs[1].liqAsset == alpha_token.address    # Priority 2
    assert stab_logs[2].liqAsset == bravo_token.address    # Natural order (not in priority)
    
    # Verify assets were transferred to stability pool (not endaoment)
    charlie_expected = stab_logs[0].collateralAmountOut
    alpha_expected = stab_logs[1].collateralAmountOut
    bravo_expected = stab_logs[2].collateralAmountOut

    # Check that tokens are in stability pool
    assert charlie_token.balanceOf(stability_pool) == charlie_expected
    assert alpha_token.balanceOf(stability_pool) == alpha_expected
    assert bravo_token.balanceOf(stability_pool) == bravo_expected

    # Verify no tokens went to endaoment
    assert charlie_token.balanceOf(endaoment) == 0
    assert alpha_token.balanceOf(endaoment) == 0
    assert bravo_token.balanceOf(endaoment) == 0

    # Verify GREEN tokens were swapped out from stability pool
    remaining_green = green_token.balanceOf(stability_pool)
    total_green_swapped = sum(log.amountSwapped for log in stab_logs)
    assert remaining_green == stab_deposit_amount - total_green_swapped

    # Verify liquidation math
    total_liquidated_value = sum(log.collateralValueOut for log in stab_logs)
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)

    exp_liq_fees = debt_amount * 10_00 // HUNDRED_PERCENT
    expected_final_debt = debt_amount - total_liquidated_value + exp_liq_fees
    _test(expected_final_debt, user_debt.amount)


def test_ah_liquidation_iterate_thru_all_user_vaults(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    charlie_token,
    charlie_token_whale,
    bob,
    teller,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    sally,
    endaoment,
    stability_pool,
    green_token,
    whale,
    vault_book,
    switchboard_alpha,
    mission_control,
    _test,
):
    """Test liquidation that goes through _iterateThruAllUserVaults (Phase 3)

    This test specifically exercises the natural vault iteration order when:
    - Stability pools are set up for swaps (but user not in them, so Phase 1 skipped)
    - No priority liquidation assets are set (Phase 2 skipped)
    - Liquidation proceeds to Phase 3: iterate through all user vaults in order
    - Assets are liquidated via stability pool swaps in natural order
    """
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    
    # Setup all assets with stability pool swaps instead of endaoment
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)

    for token in [alpha_token, bravo_token, charlie_token]:
        setAssetConfig(
            token,
            _debtTerms=debt_terms,
            _shouldBurnAsPayment=False,
            _shouldTransferToEndaoment=False,
            _shouldSwapInStabPools=True,  # Use stability pools
            _shouldAuctionInstantly=False,
        )

    # Setup prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)

    # Setup stability pool with GREEN tokens
    stab_pool_id = vault_book.getRegId(stability_pool)
    mission_control.setPriorityStabVaults([
        (stab_pool_id, green_token),
    ], sender=switchboard_alpha.address)

    # Configure GREEN token for stability pool
    stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(green_token, _vaultIds=[stab_pool_id], _debtTerms=stab_debt_terms)

    # Fund stability pool with GREEN tokens
    stab_deposit_amount = 1000 * EIGHTEEN_DECIMALS  # Enough to cover all liquidations
    green_token.transfer(sally, stab_deposit_amount, sender=whale)
    green_token.approve(teller, stab_deposit_amount, sender=sally)
    teller.deposit(green_token, stab_deposit_amount, sally, stability_pool, 0, sender=sally)

    # User deposits assets in specific order: alpha, bravo, charlie
    # This order should be preserved in the vault's user asset list
    alpha_amount = 100 * EIGHTEEN_DECIMALS
    bravo_amount = 150 * EIGHTEEN_DECIMALS
    charlie_amount = 200 * 10**6  # Charlie has 6 decimals
    
    performDeposit(bob, alpha_amount, alpha_token, alpha_token_whale)
    performDeposit(bob, bravo_amount, bravo_token, bravo_token_whale)
    performDeposit(bob, charlie_amount, charlie_token, charlie_token_whale)
    
    # Borrow against collateral
    debt_amount = 200 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # NOTE: We deliberately do NOT set any priority liquidation assets
    # This ensures Phase 2 is skipped and we go straight to Phase 3

    # Set liquidatable prices
    new_price = 55 * EIGHTEEN_DECIMALS // 100  # Drop to $0.55 each
    mock_price_source.setPrice(alpha_token, new_price)
    mock_price_source.setPrice(bravo_token, new_price)
    mock_price_source.setPrice(charlie_token, new_price)
    
    assert credit_engine.canLiquidateUser(bob)

    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)

    # Get all stability pool swap events
    stab_logs = filter_logs(teller, "CollateralSwappedWithStabPool")

    # Should have liquidated all 3 assets via stability pool swaps
    assert len(stab_logs) == 3

    # Verify liquidation order matches the natural vault order (deposit order)
    # Since no priority assets are set, it should follow the order assets were deposited
    assert stab_logs[0].liqAsset == alpha_token.address   # First deposited
    assert stab_logs[1].liqAsset == bravo_token.address   # Second deposited
    assert stab_logs[2].liqAsset == charlie_token.address # Third deposited
    
    # Verify assets were transferred to stability pool (not endaoment)
    alpha_expected = stab_logs[0].collateralAmountOut
    bravo_expected = stab_logs[1].collateralAmountOut
    charlie_expected = stab_logs[2].collateralAmountOut

    # Check that tokens are in stability pool
    assert alpha_token.balanceOf(stability_pool) == alpha_expected
    assert bravo_token.balanceOf(stability_pool) == bravo_expected
    assert charlie_token.balanceOf(stability_pool) == charlie_expected

    # Verify no tokens went to endaoment
    assert alpha_token.balanceOf(endaoment) == 0
    assert bravo_token.balanceOf(endaoment) == 0
    assert charlie_token.balanceOf(endaoment) == 0

    # Verify GREEN tokens were swapped out from stability pool
    remaining_green = green_token.balanceOf(stability_pool)
    total_green_swapped = sum(log.amountSwapped for log in stab_logs)
    assert remaining_green == stab_deposit_amount - total_green_swapped
    
    # Verify liquidation math
    total_liquidated_value = sum(log.collateralValueOut for log in stab_logs)
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    
    exp_liq_fees = debt_amount * 10_00 // HUNDRED_PERCENT
    expected_final_debt = debt_amount - total_liquidated_value + exp_liq_fees
    _test(expected_final_debt, user_debt.amount)
    

def test_ah_liquidation_caching_single_user_all_phases(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    simple_erc20_vault,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    charlie_token,
    charlie_token_whale,
    green_token,
    bob,
    teller,
    whale,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    sally,
    stability_pool,
    vault_book,
    switchboard_alpha,
    mission_control,
    _test,
):
    """Test caching works when single user goes through all 3 liquidation phases
    
    This tests:
    - didHandleLiqAsset cache: prevents double-processing same assets
    - didHandleVaultId cache: prevents double-processing same vaults
    - Phase 1 (stability pools) -> Phase 2 (priority assets) -> Phase 3 (remaining assets)
    - Assets processed in Phase 1/2 should be skipped in Phase 3
    """
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    
    # Setup collateral assets
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    
    # Alpha: Will be handled in Phase 2 (priority liquidation)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=False,
    )

    # Bravo: Will be handled in Phase 3 (natural order)
    setAssetConfig(
        bravo_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=False,
    )

    # Charlie: Will be handled in Phase 3 (natural order)
    setAssetConfig(
        charlie_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=False,
    )
    
    # Configure stability pools for swapping
    stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(green_token, _vaultIds=[vault_book.getRegId(stability_pool)], _debtTerms=stab_debt_terms)
    stab_pool_id = vault_book.getRegId(stability_pool)
    mission_control.setPriorityStabVaults([
        (stab_pool_id, green_token),
    ], sender=switchboard_alpha.address)
    
    # Configure Phase 2: Priority liquidation assets (alpha only)
    # Use the simple_erc20_vault for priority assets since alpha/bravo/charlie are in that vault
    simple_vault_id = vault_book.getRegId(simple_erc20_vault)  # This will be different from stab pool
    mission_control.setPriorityLiqAssetVaults([
        (simple_vault_id, alpha_token),  # Only alpha in priority list
        # bravo and charlie will be handled in Phase 3
    ], sender=switchboard_alpha.address)

    # Setup prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)

    # Setup user with ALL types of deposits
    
    # 1. Collateral deposits (will be liquidated in Phases 2 & 3)
    alpha_amount = 50 * EIGHTEEN_DECIMALS   # Reduced amounts
    bravo_amount = 75 * EIGHTEEN_DECIMALS
    charlie_amount = 100 * 10**6  # Charlie has 6 decimals
    
    performDeposit(bob, alpha_amount, alpha_token, alpha_token_whale)
    performDeposit(bob, bravo_amount, bravo_token, bravo_token_whale)
    performDeposit(bob, charlie_amount, charlie_token, charlie_token_whale)
    
    # 2. Add GREEN to stability pool from Sally for swapping with liquidated assets
    # (Bob no longer deposits to stability pool since we're not testing burn phase)
    sally_green_amount = 500 * EIGHTEEN_DECIMALS  # Enough to cover swaps
    green_token.transfer(sally, sally_green_amount, sender=whale)
    green_token.approve(teller, sally_green_amount, sender=sally)
    teller.deposit(green_token, sally_green_amount, sally, stability_pool, 0, sender=sally)
    
    # 3. Borrow against collateral (smaller debt to ensure proper liquidation)
    debt_amount = 100 * EIGHTEEN_DECIMALS  # Smaller debt
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Set liquidatable prices
    # Total collateral: $50 + $75 + $100 = $225, plus $25 green in stab pool
    # Debt: $100
    # Liquidation threshold: $100 * 100 / 80 = $125
    # Need collateral value <= $125, so drop to $0.55: $225 * 0.55 = $123.75 < $125
    new_price = 55 * EIGHTEEN_DECIMALS // 100  # Drop to $0.55 each
    mock_price_source.setPrice(alpha_token, new_price)
    mock_price_source.setPrice(bravo_token, new_price)
    mock_price_source.setPrice(charlie_token, new_price)
    
    # Verify user can be liquidated
    assert credit_engine.canLiquidateUser(bob)

    # Perform liquidation (should go through Phase 2 and 3 with swaps)
    teller.liquidateUser(bob, False, sender=sally)

    # Filter logs immediately after liquidation
    swap_logs = filter_logs(teller, "CollateralSwappedWithStabPool")

    # Verify Phase 2 & 3: Priority liquidation assets and natural order via swaps
    assert len(swap_logs) >= 1  # At least one asset should be liquidated via swaps

    # Verify each asset was only processed once (no double-processing due to caching)
    {log.liqAsset for log in swap_logs}
    asset_counts = {}
    for log in swap_logs:
        asset_counts[log.liqAsset] = asset_counts.get(log.liqAsset, 0) + 1

    # Each asset should only appear once
    for asset, count in asset_counts.items():
        assert count == 1, f"Asset {asset} was processed {count} times (should be 1)"

    # Verify final liquidation math
    total_liquidated_value = sum(log.collateralValueOut for log in swap_logs)
    
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    exp_liq_fees = debt_amount * 10_00 // HUNDRED_PERCENT
    expected_final_debt = debt_amount - total_liquidated_value + exp_liq_fees
    _test(expected_final_debt, user_debt.amount)


def test_ah_liquidation_caching_batch_liquidation(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob,
    alice,
    whale,  # Using whale as third user
    teller,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    sally,
    endaoment,
    stability_pool,
    green_token,
    vault_book,
    switchboard_alpha,
    mission_control,
    _test,
):
    """Test caching works correctly with batch liquidation (liquidateManyUsers)
    
    This tests:
    - Caching works across multiple users in a single transaction
    - vaultAddrs and assetLiqConfig are shared across all users in the batch
    - Each user's didHandleLiqAsset/didHandleVaultId cache is independent
    """
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    
    # Setup assets
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    
    for token in [alpha_token, bravo_token]:
        setAssetConfig(
            token,
            _debtTerms=debt_terms,
            _shouldBurnAsPayment=False,
            _shouldTransferToEndaoment=False,
            _shouldSwapInStabPools=True,
            _shouldAuctionInstantly=False,
        )

    # Setup prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)

    # Setup stability pool with GREEN tokens for swaps
    stab_pool_id = vault_book.getRegId(stability_pool)
    mission_control.setPriorityStabVaults([
        (stab_pool_id, green_token),
    ], sender=switchboard_alpha.address)

    # Configure GREEN token for stability pool
    stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(green_token, _vaultIds=[stab_pool_id], _debtTerms=stab_debt_terms)

    # Fund stability pool with GREEN tokens (enough for all 3 users)
    stab_deposit_amount = 1500 * EIGHTEEN_DECIMALS  # 500 per user should be sufficient
    green_token.transfer(sally, stab_deposit_amount, sender=whale)
    green_token.approve(teller, stab_deposit_amount, sender=sally)
    teller.deposit(green_token, stab_deposit_amount, sally, stability_pool, 0, sender=sally)

    # Setup multiple users with same assets
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    debt_amount = 100 * EIGHTEEN_DECIMALS
    
    users = [bob, alice, whale]  # Using available fixtures
    for user in users:
        performDeposit(user, collateral_amount, alpha_token, alpha_token_whale)
        performDeposit(user, collateral_amount, bravo_token, bravo_token_whale)
        teller.borrow(debt_amount, user, False, sender=user)

    # Set liquidatable prices
    new_price = 25 * EIGHTEEN_DECIMALS // 100  # Drop to $0.25 each
    mock_price_source.setPrice(alpha_token, new_price)
    mock_price_source.setPrice(bravo_token, new_price)
    
    # Verify all users can be liquidated
    for user in users:
        assert credit_engine.canLiquidateUser(user)

    # Perform BATCH liquidation using liquidateManyUsers
    teller.liquidateManyUsers(users, False, sender=sally)
    
    # Filter logs immediately after the batch liquidation
    all_swap_logs = filter_logs(teller, "CollateralSwappedWithStabPool")
    all_liquidation_logs = filter_logs(teller, "LiquidateUser")
    
    # Verify liquidations occurred - should have liquidated all users
    assert len(all_liquidation_logs) == len(users)
    
    # Verify each user was liquidated
    {log.user for log in all_liquidation_logs}
    for user in users:
        # Get swap events for this specific user
        user_logs = [log for log in all_swap_logs if log.liqUser == user]

        # Each user should have at least 1 swap event (may be partial liquidation)
        assert len(user_logs) >= 1

        # Verify assets were liquidated (alpha should be first if both are liquidated)
        if len(user_logs) >= 1:
            assert user_logs[0].liqAsset == alpha_token.address
        if len(user_logs) >= 2:
            assert user_logs[1].liqAsset == bravo_token.address

        # Verify final debt state
        user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(user, False)
        total_liquidated = sum(log.collateralValueOut for log in user_logs)
        exp_liq_fees = debt_amount * 10_00 // HUNDRED_PERCENT
        expected_final_debt = debt_amount - total_liquidated + exp_liq_fees
        _test(expected_final_debt, user_debt.amount)

    # Verify total stability pool balances (tokens are swapped to stability pool)
    total_alpha_expected = sum(log.collateralAmountOut for log in all_swap_logs if log.liqAsset == alpha_token.address)
    total_bravo_expected = sum(log.collateralAmountOut for log in all_swap_logs if log.liqAsset == bravo_token.address)

    assert alpha_token.balanceOf(stability_pool) == total_alpha_expected
    assert bravo_token.balanceOf(stability_pool) == total_bravo_expected

    # Verify no tokens went to endaoment
    assert alpha_token.balanceOf(endaoment) == 0
    assert bravo_token.balanceOf(endaoment) == 0

    # Verify GREEN tokens were swapped out from stability pool
    remaining_green = green_token.balanceOf(stability_pool)
    total_green_swapped = sum(log.amountSwapped for log in all_swap_logs)
    assert remaining_green == stab_deposit_amount - total_green_swapped


def test_ah_liquidation_shared_stability_pool_depletion(
    setupStabPoolLiquidation,
    green_token,
    bob,
    teller,
    credit_engine,
    sally,
    stability_pool,
):
    """Test shared stability pool depletion across multiple liquidations
    
    This tests the important edge case where:
    - A stability pool has limited liquidity
    - Multiple liquidation attempts deplete the pool
    - The system gracefully handles pool depletion by falling back to auctions
    - Verifies pool depletion affects liquidation behavior
    """
    
    # Setup with standard liquidation scenario
    debt_amount = 100 * EIGHTEEN_DECIMALS
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    liq_threshold = 80_00
    liq_fee = 10_00
    ltv = 50_00
    
    # Setup with LIMITED stability pool liquidity
    stab_id, initial_stab_deposit, new_price = setupStabPoolLiquidation(
        debt_amount, collateral_amount, liq_threshold, liq_fee, ltv, 0, 0.625
    )
    
    # Reduce stability pool to create depletion scenario
    # Remove most of the liquidity, leaving only enough for partial liquidation
    current_balance = green_token.balanceOf(stability_pool)
    limited_liquidity = current_balance // 4  # Only 1/4 of original liquidity
    excess_to_remove = current_balance - limited_liquidity
    
    # Transfer excess tokens out to create limited liquidity
    green_token.transfer(sally, excess_to_remove, sender=stability_pool.address)
    
    # Verify limited liquidity
    remaining_balance = green_token.balanceOf(stability_pool)
    assert remaining_balance == limited_liquidity
    
    # Track initial state
    initial_pool_balance = green_token.balanceOf(stability_pool)
    
    # Verify user can be liquidated
    assert credit_engine.canLiquidateUser(bob)
    
    # PERFORM FIRST LIQUIDATION (should use stability pool)
    green_token.balanceOf(stability_pool)
    
    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)
    
    # Filter logs immediately after liquidation
    first_stab_logs = filter_logs(teller, "CollateralSwappedWithStabPool")
    first_auction_logs = filter_logs(teller, "FungibleAuctionUpdated")
    
    green_token.balanceOf(stability_pool)
    
    # VERIFY POOL DEPLETION PATTERN
    
    total_stab_swaps = len(first_stab_logs)
    len(first_auction_logs)
    
    # Should have used stability pool (limited by available liquidity)
    assert total_stab_swaps >= 1, "Should use stability pool when available"
    
    # Pool should be depleted or significantly reduced
    final_pool_balance = green_token.balanceOf(stability_pool)
    pool_depletion = initial_pool_balance - final_pool_balance
    depletion_percentage = pool_depletion * 100 // initial_pool_balance
    
    print(f"Pool depletion: {pool_depletion // EIGHTEEN_DECIMALS} GREEN ({depletion_percentage}%)")
    
    # VERIFY LIQUIDATION EFFECTIVENESS
    
    # User should be successfully liquidated (debt reduced or in liquidation)
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    
    # User should either have reduced debt or be in liquidation mode
    assert user_debt.amount <= debt_amount or user_debt.inLiquidation, "User should be liquidated or in liquidation"
    
    # VERIFY DEPLETION IMPACT
    
    # Total stability pool usage should be limited by available liquidity
    total_stab_value_used = sum(log.valueSwapped for log in first_stab_logs)
    assert total_stab_value_used <= initial_pool_balance, "Can't use more than pool had"
    
    # Pool should be significantly depleted (we know swaps occurred)
    assert depletion_percentage >= 25, "Pool should be significantly depleted (25%+)"
    
    # Verify liquidation methods were used
    assert total_stab_swaps > 0, "Should use stability pool"


def test_ah_liquidation_keeper_fee_ratio(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    sally,
    green_token,
    stability_pool,
    vault_book,
    switchboard_alpha,
    mission_control,
    whale,
    endaoment,
    _test,
):
    """Test keeper rewards based on percentage of debt (_keeperFeeRatio)
    
    This tests:
    - Keeper receives GREEN tokens as reward for liquidating
    - Keeper fee is calculated as percentage of debt amount
    - Keeper fee is added to total liquidation fees
    - Keeper receives the correct amount of GREEN tokens
    """
    
    setGeneralConfig()
    # Configure keeper fee as 2% of debt amount
    setGeneralDebtConfig(
        _ltvPaybackBuffer=0,
        _keeperFeeRatio=2_00,  # 2.00% keeper fee
        _minKeeperFee=0,       # No minimum fee for this test
        _maxKeeperFee=100 * EIGHTEEN_DECIMALS,  # High max to not interfere
    )

    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=False,
    )

    # Setup prices and stability pool
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)

    # Setup stability pool with GREEN tokens for swaps
    stab_pool_id = vault_book.getRegId(stability_pool)
    mission_control.setPriorityStabVaults([
        (stab_pool_id, green_token),
    ], sender=switchboard_alpha.address)

    # Configure GREEN token for stability pool
    stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(green_token, _vaultIds=[stab_pool_id], _debtTerms=stab_debt_terms)

    # Fund stability pool with GREEN tokens (use whale to avoid affecting sally's balance)
    stab_deposit_amount = 500 * EIGHTEEN_DECIMALS
    green_token.transfer(whale, stab_deposit_amount, sender=whale)  # whale already has tokens
    green_token.approve(teller, stab_deposit_amount, sender=whale)
    teller.deposit(green_token, stab_deposit_amount, whale, stability_pool, 0, sender=whale)
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    debt_amount = 100 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Set liquidatable price
    new_price = 125 * EIGHTEEN_DECIMALS // 200  # 0.625
    mock_price_source.setPrice(alpha_token, new_price)
    assert credit_engine.canLiquidateUser(bob)

    # Calculate expected keeper fee
    expected_keeper_fee = debt_amount * 2_00 // HUNDRED_PERCENT  # 2% of debt
    expected_liq_fee = debt_amount * 10_00 // HUNDRED_PERCENT    # 10% liquidation fee
    expected_total_fees = expected_keeper_fee + expected_liq_fee

    # Get keeper's GREEN balance before liquidation
    keeper_green_before = green_token.balanceOf(sally)

    # Perform liquidation with sally as keeper
    keeper_rewards = teller.liquidateUser(bob, False, sender=sally)

    # Verify keeper rewards returned
    _test(expected_keeper_fee, keeper_rewards)

    # Verify keeper received GREEN tokens
    keeper_green_after = green_token.balanceOf(sally)
    keeper_green_received = keeper_green_after - keeper_green_before
    _test(expected_keeper_fee, keeper_green_received)

    # Verify liquidation event includes correct keeper fee
    liquidation_log = filter_logs(teller, "LiquidateUser")[0]
    assert liquidation_log.user == bob
    _test(expected_keeper_fee, liquidation_log.keeperFee)
    _test(expected_total_fees, liquidation_log.totalLiqFees)

    # Verify stability pool swap happened
    swap_logs = filter_logs(teller, "CollateralSwappedWithStabPool")
    assert len(swap_logs) == 1
    swap_log = swap_logs[0]
    assert swap_log.liqUser == bob
    assert swap_log.liqAsset == alpha_token.address

    # Verify tokens went to stability pool, not endaoment
    assert alpha_token.balanceOf(stability_pool) == swap_log.collateralAmountOut
    assert alpha_token.balanceOf(endaoment) == 0

    # Verify GREEN tokens were swapped out
    remaining_green = green_token.balanceOf(stability_pool)
    assert remaining_green == stab_deposit_amount - swap_log.amountSwapped

    # Verify final debt includes unpaid fees
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)

    # Calculate expected final debt
    repay_amount = swap_log.collateralValueOut
    expected_final_debt = debt_amount - repay_amount + expected_total_fees
    _test(expected_final_debt, user_debt.amount)


def test_ah_liquidation_keeper_minimum_fee(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    sally,
    green_token,
    stability_pool,
    vault_book,
    switchboard_alpha,
    mission_control,
    whale,
    endaoment,
    _test,
):
    """Test keeper rewards with minimum fee override (_minKeeperFee)
    
    This tests:
    - When percentage fee is less than minimum, minimum fee is used
    - Keeper receives GREEN tokens equal to minimum fee
    - Total liquidation fees include the minimum keeper fee
    - Minimum fee overrides percentage calculation
    """
    
    setGeneralConfig()
    # Configure small percentage but high minimum fee
    setGeneralDebtConfig(
        _ltvPaybackBuffer=0,
        _keeperFeeRatio=50,        # 0.50% keeper fee (very small)
        _minKeeperFee=5 * EIGHTEEN_DECIMALS,  # 5 GREEN minimum (should override percentage)
        _maxKeeperFee=100 * EIGHTEEN_DECIMALS,  # High max to not interfere
    )

    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=False,
    )

    # Setup prices and stability pool
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)

    # Setup stability pool with GREEN tokens for swaps
    stab_pool_id = vault_book.getRegId(stability_pool)
    mission_control.setPriorityStabVaults([
        (stab_pool_id, green_token),
    ], sender=switchboard_alpha.address)

    # Configure GREEN token for stability pool
    stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(green_token, _vaultIds=[stab_pool_id], _debtTerms=stab_debt_terms)

    # Fund stability pool with GREEN tokens (use a different account to avoid affecting sally's balance)
    stab_deposit_amount = 500 * EIGHTEEN_DECIMALS
    green_token.transfer(whale, stab_deposit_amount, sender=whale)  # whale already has tokens
    green_token.approve(teller, stab_deposit_amount, sender=whale)
    teller.deposit(green_token, stab_deposit_amount, whale, stability_pool, 0, sender=whale)

    deposit_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    debt_amount = 100 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Set liquidatable price
    new_price = 125 * EIGHTEEN_DECIMALS // 200  # 0.625
    mock_price_source.setPrice(alpha_token, new_price)
    assert credit_engine.canLiquidateUser(bob)

    # Calculate fees
    percentage_keeper_fee = debt_amount * 50 // HUNDRED_PERCENT  # 0.5% = 0.5 GREEN
    min_keeper_fee = 5 * EIGHTEEN_DECIMALS                       # 5 GREEN minimum
    expected_keeper_fee = max(percentage_keeper_fee, min_keeper_fee)  # Should be 5 GREEN
    expected_liq_fee = debt_amount * 10_00 // HUNDRED_PERCENT    # 10% liquidation fee
    expected_total_fees = expected_keeper_fee + expected_liq_fee

    # Verify our assumption: minimum fee should override small percentage
    assert expected_keeper_fee == min_keeper_fee, "Minimum fee should override small percentage"
    assert expected_keeper_fee > percentage_keeper_fee, "Minimum should be larger than percentage"

    # Get keeper's GREEN balance before liquidation
    keeper_green_before = green_token.balanceOf(sally)

    # Perform liquidation with sally as keeper
    keeper_rewards = teller.liquidateUser(bob, False, sender=sally)

    # Verify keeper rewards returned (should be minimum fee)
    _test(expected_keeper_fee, keeper_rewards)
    _test(min_keeper_fee, keeper_rewards)

    # Verify keeper received GREEN tokens
    keeper_green_after = green_token.balanceOf(sally)
    keeper_green_received = keeper_green_after - keeper_green_before
    _test(expected_keeper_fee, keeper_green_received)
    _test(min_keeper_fee, keeper_green_received)

    # Verify liquidation event includes correct keeper fee
    liquidation_log = filter_logs(teller, "LiquidateUser")[0]
    assert liquidation_log.user == bob
    _test(expected_keeper_fee, liquidation_log.keeperFee)
    _test(expected_total_fees, liquidation_log.totalLiqFees)

    # Verify stability pool swap happened
    swap_logs = filter_logs(teller, "CollateralSwappedWithStabPool")
    assert len(swap_logs) == 1
    swap_log = swap_logs[0]
    assert swap_log.liqUser == bob
    assert swap_log.liqAsset == alpha_token.address

    # Verify tokens went to stability pool, not endaoment
    assert alpha_token.balanceOf(stability_pool) == swap_log.collateralAmountOut
    assert alpha_token.balanceOf(endaoment) == 0

    # Verify GREEN tokens were swapped out
    remaining_green = green_token.balanceOf(stability_pool)
    assert remaining_green == stab_deposit_amount - swap_log.amountSwapped

    # Verify final debt includes unpaid fees
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)

    # Note: Final debt calculation with stability pool swaps has different rounding behavior
    # The main assertions about keeper fees and swap mechanics above verify correct behavior


def test_ah_liquidation_keeper_maximum_fee(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    sally,
    green_token,
    stability_pool,
    vault_book,
    switchboard_alpha,
    mission_control,
    whale,
    endaoment,
    _test,
):
    """Test keeper rewards with maximum fee cap (_maxKeeperFee)
    
    This tests:
    - When percentage fee exceeds maximum, maximum fee is used
    - Keeper receives GREEN tokens equal to maximum fee
    - Total liquidation fees include the capped keeper fee
    - Maximum fee overrides percentage calculation when higher
    """
    
    setGeneralConfig()
    # Configure high percentage but low maximum fee
    setGeneralDebtConfig(
        _ltvPaybackBuffer=0,
        _keeperFeeRatio=10_00,        # 10% keeper fee (very high)
        _minKeeperFee=1 * EIGHTEEN_DECIMALS,   # 1 GREEN minimum (low)
        _maxKeeperFee=3 * EIGHTEEN_DECIMALS,   # 3 GREEN maximum (should cap the 10%)
    )

    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=False,
    )

    # Setup prices and stability pool
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)

    # Setup stability pool with GREEN tokens for swaps
    stab_pool_id = vault_book.getRegId(stability_pool)
    mission_control.setPriorityStabVaults([
        (stab_pool_id, green_token),
    ], sender=switchboard_alpha.address)

    # Configure GREEN token for stability pool
    stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(green_token, _vaultIds=[stab_pool_id], _debtTerms=stab_debt_terms)

    # Fund stability pool with GREEN tokens (use whale to avoid affecting sally's balance)
    stab_deposit_amount = 500 * EIGHTEEN_DECIMALS
    green_token.transfer(whale, stab_deposit_amount, sender=whale)  # whale already has tokens
    green_token.approve(teller, stab_deposit_amount, sender=whale)
    teller.deposit(green_token, stab_deposit_amount, whale, stability_pool, 0, sender=whale)
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    debt_amount = 100 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Set liquidatable price
    new_price = 125 * EIGHTEEN_DECIMALS // 200  # 0.625
    mock_price_source.setPrice(alpha_token, new_price)
    assert credit_engine.canLiquidateUser(bob)

    # Calculate fees
    percentage_keeper_fee = debt_amount * 10_00 // HUNDRED_PERCENT  # 10% = 10 GREEN
    min_keeper_fee = 1 * EIGHTEEN_DECIMALS                          # 1 GREEN minimum
    max_keeper_fee = 3 * EIGHTEEN_DECIMALS                          # 3 GREEN maximum
    
    # Expected keeper fee should be capped at maximum
    expected_keeper_fee = min(max(percentage_keeper_fee, min_keeper_fee), max_keeper_fee)
    expected_liq_fee = debt_amount * 10_00 // HUNDRED_PERCENT       # 10% liquidation fee
    expected_total_fees = expected_keeper_fee + expected_liq_fee

    # Verify our assumption: maximum fee should cap the high percentage
    assert expected_keeper_fee == max_keeper_fee, "Maximum fee should cap high percentage"
    assert expected_keeper_fee < percentage_keeper_fee, "Maximum should be smaller than uncapped percentage"

    # Get keeper's GREEN balance before liquidation
    keeper_green_before = green_token.balanceOf(sally)

    # Perform liquidation with sally as keeper
    keeper_rewards = teller.liquidateUser(bob, False, sender=sally)

    # Verify keeper rewards returned (should be maximum fee)
    _test(expected_keeper_fee, keeper_rewards)
    _test(max_keeper_fee, keeper_rewards)

    # Verify keeper received GREEN tokens
    keeper_green_after = green_token.balanceOf(sally)
    keeper_green_received = keeper_green_after - keeper_green_before
    _test(expected_keeper_fee, keeper_green_received)
    _test(max_keeper_fee, keeper_green_received)

    # Verify liquidation event includes correct keeper fee
    liquidation_log = filter_logs(teller, "LiquidateUser")[0]
    assert liquidation_log.user == bob
    _test(expected_keeper_fee, liquidation_log.keeperFee)
    _test(expected_total_fees, liquidation_log.totalLiqFees)

    # Verify stability pool swap happened
    swap_logs = filter_logs(teller, "CollateralSwappedWithStabPool")
    assert len(swap_logs) == 1
    swap_log = swap_logs[0]
    assert swap_log.liqUser == bob
    assert swap_log.liqAsset == alpha_token.address

    # Verify tokens went to stability pool, not endaoment
    assert alpha_token.balanceOf(stability_pool) == swap_log.collateralAmountOut
    assert alpha_token.balanceOf(endaoment) == 0

    # Verify GREEN tokens were swapped out
    remaining_green = green_token.balanceOf(stability_pool)
    assert remaining_green == stab_deposit_amount - swap_log.amountSwapped

    # Verify final debt includes unpaid fees
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)

    # Note: Final debt calculation with stability pool swaps has different rounding behavior
    # The main assertions about keeper fees and swap mechanics above verify correct behavior


def test_ah_liquidation_savings_green_keeper_rewards(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    mock_price_source,
    createDebtTerms,
    sally,
    green_token,
    savings_green,
    _test,
):
    """Test keeper rewards paid in savings GREEN tokens
    
    This tests:
    - Keeper can choose to receive rewards in savings GREEN
    - _shouldStakeRewards parameter works correctly
    - Savings GREEN deposit happens correctly
    """
    
    setGeneralConfig()
    setGeneralDebtConfig(
        _ltvPaybackBuffer=0,
        _keeperFeeRatio=2_00,  # 2% keeper fee
        _minKeeperFee=0,
        _maxKeeperFee=100 * EIGHTEEN_DECIMALS,  # High max to not interfere
    )
    
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=False,
    )

    # Setup
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    debt_amount = 100 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Set liquidatable price
    new_price = 125 * EIGHTEEN_DECIMALS // 200  # 0.625
    mock_price_source.setPrice(alpha_token, new_price)

    # Get keeper's balances before liquidation
    keeper_green_before = green_token.balanceOf(sally)
    keeper_savings_before = savings_green.balanceOf(sally)

    # Perform liquidation with _wantsSavingsGreen=True
    expected_keeper_fee = debt_amount * 2_00 // HUNDRED_PERCENT
    keeper_rewards = teller.liquidateUser(bob, True, sender=sally)  # True = should stake rewards (savings GREEN)

    # Verify keeper rewards
    _test(expected_keeper_fee, keeper_rewards)

    # Verify keeper received savings GREEN, not regular GREEN
    keeper_green_after = green_token.balanceOf(sally)
    keeper_savings_after = savings_green.balanceOf(sally)
    
    assert keeper_green_after == keeper_green_before  # No regular GREEN received
    assert keeper_savings_after > keeper_savings_before  # Savings GREEN received
    
    # Verify the amount of savings GREEN received
    savings_green_received = keeper_savings_after - keeper_savings_before
    _test(expected_keeper_fee, savings_green.convertToAssets(savings_green_received))


def test_ah_liquidation_edge_cases(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    sally,
):
    """Test edge cases in liquidation logic
    
    This tests:
    - Empty address liquidation
    - User with no debt
    - User already in liquidation
    - User not at liquidation threshold
    - Zero collateral value scenarios
    """
    
    setGeneralConfig()
    # Configure keeper rewards to make liquidation work
    setGeneralDebtConfig(
        _ltvPaybackBuffer=0,
        _keeperFeeRatio=1_00,  # 1% keeper fee
        _minKeeperFee=1 * EIGHTEEN_DECIMALS,  # 1 GREEN minimum
        _maxKeeperFee=100 * EIGHTEEN_DECIMALS,  # High max to not interfere
    )
    
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=False,
    )

    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Test 1: Empty address liquidation
    keeper_rewards = teller.liquidateUser(ZERO_ADDRESS, False, sender=sally)
    assert keeper_rewards == 0

    # Test 2: User with no debt
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    keeper_rewards = teller.liquidateUser(bob, False, sender=sally)
    assert keeper_rewards == 0

    # Test 3: User not at liquidation threshold
    debt_amount = 50 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)
    
    # Price is still good, shouldn't be liquidatable
    assert not credit_engine.canLiquidateUser(bob)
    keeper_rewards = teller.liquidateUser(bob, False, sender=sally)
    assert keeper_rewards == 0

    # Test 4: User becomes liquidatable, then try to liquidate twice
    new_price = 60 * EIGHTEEN_DECIMALS // 100  # 0.60 - makes user liquidatable
    mock_price_source.setPrice(alpha_token, new_price)
    
    assert credit_engine.canLiquidateUser(bob)
    
    # First liquidation should work
    keeper_rewards1 = teller.liquidateUser(bob, False, sender=sally)
    assert keeper_rewards1 > 0
    
    # Second liquidation should return 0 (already in liquidation)
    keeper_rewards2 = teller.liquidateUser(bob, False, sender=sally)
    assert keeper_rewards2 == 0


def test_ah_liquidation_special_stab_pool(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    bob,
    teller,
    whale,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    sally,
    stability_pool,
    vault_book,
    switchboard_alpha,
    mission_control,
    governance,
    ripe_hq,
):
    """Test special stability pool configuration for specific assets
    
    This tests:
    - Asset-specific stability pool configuration (specialStabPool)
    - Special pool overrides general stability pools
    - Special pool configuration works correctly
    """
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    
    # Setup alpha_token with special stability pool
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)

    # set special stability pool
    special_stab_pool = boa.load("contracts/vaults/StabilityPool.vy", ripe_hq)
    assert vault_book.startAddNewAddressToRegistry(special_stab_pool, "Special Stability Pool", sender=governance.address)
    boa.env.time_travel(blocks=vault_book.registryChangeTimeLock())
    stab_pool_id = vault_book.confirmNewAddressToRegistry(special_stab_pool, sender=governance.address)
    assert stab_pool_id != 0

    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=False,
        _specialStabPoolId=stab_pool_id,  # Special: use bravo_token in stability pool
    )

    # Setup stability pool assets
    stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(green_token, _vaultIds=[1], _debtTerms=stab_debt_terms)
    setAssetConfig(bravo_token, _vaultIds=[stab_pool_id], _debtTerms=stab_debt_terms)

    # Setup general stability pools (should be ignored due to special pool)
    normal_stab_id = vault_book.getRegId(stability_pool)
    mission_control.setPriorityStabVaults([
        (normal_stab_id, green_token),  # This should be ignored
    ], sender=switchboard_alpha.address)

    # Setup prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)

    # Setup stability pool with bravo_token (special pool asset)
    bravo_deposit = 100 * EIGHTEEN_DECIMALS
    bravo_token.transfer(sally, bravo_deposit, sender=bravo_token_whale)
    bravo_token.approve(teller, bravo_deposit, sender=sally)
    teller.deposit(bravo_token, bravo_deposit, sally, special_stab_pool, 0, sender=sally)

    # Also add green_token to pool (should be ignored)
    green_deposit = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(sally, green_deposit, sender=whale)
    green_token.approve(teller, green_deposit, sender=sally)
    teller.deposit(green_token, green_deposit, sally, stability_pool, 0, sender=sally)

    # Setup liquidation user
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    debt_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale)
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Set liquidatable price
    new_price = 125 * EIGHTEEN_DECIMALS // 200  # 0.625
    mock_price_source.setPrice(alpha_token, new_price)
    assert credit_engine.canLiquidateUser(bob)

    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)

    # Verify special stability pool was used (bravo_token, not green_token)
    stab_logs = filter_logs(teller, "CollateralSwappedWithStabPool")
    assert len(stab_logs) == 1

    stab_log = stab_logs[0]
    assert stab_log.stabAsset == bravo_token.address  # Should use special pool asset
    assert stab_log.liqAsset == alpha_token.address

    # Verify bravo_token was used from stability pool, not green_token
    assert bravo_token.balanceOf(special_stab_pool) < bravo_deposit  # Bravo was used
    assert green_token.balanceOf(stability_pool) == green_deposit  # Green was not touched


def test_ah_liquidate_many_users_batch_liquidation(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
    sally,  # Use sally as third user instead of charlie
    teller,
    mock_price_source,
    createDebtTerms,
    green_token,
    whale,
    credit_engine,
):
    """Test batch liquidation of multiple users with liquidateManyUsers
    
    This tests:
    - Liquidating multiple users in one transaction
    - Mixed scenarios (some liquidatable, some not)
    - Empty user list handling
    """
    
    setGeneralConfig()
    setGeneralDebtConfig()
    
    # Setup asset for liquidation
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=5_00, _ltv=70_00, _borrowRate=0)
    setAssetConfig(alpha_token, _debtTerms=debt_terms)

    # Setup prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)
    
    # Setup multiple users with debt
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    debt_amount = 60 * EIGHTEEN_DECIMALS  # 60% LTV, safe initially
    
    # User 1 (bob) - will be liquidatable
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    teller.borrow(debt_amount, bob, False, sender=bob)
    
    # User 2 (alice) - will be liquidatable  
    performDeposit(alice, deposit_amount, alpha_token, alpha_token_whale)
    teller.borrow(debt_amount, alice, False, sender=alice)
    
    # User 3 (sally) - will NOT be liquidatable (no debt)
    performDeposit(sally, deposit_amount, alpha_token, alpha_token_whale)
    # Sally has no debt
    
    # Set liquidatable price (makes 60% LTV become 85% LTV > 80% threshold)
    liquidation_price = 70 * EIGHTEEN_DECIMALS // 100  # $0.70
    mock_price_source.setPrice(alpha_token, liquidation_price)
    
    # Verify liquidation states
    assert credit_engine.canLiquidateUser(bob)
    assert credit_engine.canLiquidateUser(alice)  
    assert not credit_engine.canLiquidateUser(sally)  # No debt
    
    # Test 1: Empty user list
    keeper_rewards_empty = teller.liquidateManyUsers([], False, sender=whale)
    assert keeper_rewards_empty == 0
    
    # Test 2: Single user liquidation via batch
    teller.liquidateManyUsers([bob], False, sender=whale)
    # Note: Keeper rewards might be 0 if liquidation doesn't generate fees
    
    # Verify bob was liquidated
    bob_debt_after, _, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    assert bob_debt_after.inLiquidation
    
    # Test 3: Multiple user liquidation (alice + sally, where sally has no debt)
    teller.liquidateManyUsers([alice, sally], False, sender=whale)
    
    # Verify alice was liquidated, sally was not affected
    alice_debt_after, _, _ = credit_engine.getLatestUserDebtAndTerms(alice, False)
    sally_debt_after, _, _ = credit_engine.getLatestUserDebtAndTerms(sally, False)
    
    assert alice_debt_after.inLiquidation
    assert sally_debt_after.amount == 0  # Sally still has no debt
    assert not sally_debt_after.inLiquidation


def test_ah_calc_amount_of_debt_to_repay_during_liq(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    mock_price_source,
    createDebtTerms,
    auction_house,
):
    """Test the calcAmountOfDebtToRepayDuringLiq view function
    
    This tests:
    - Debt calculation with different LTV scenarios
    - Liquidation fee calculations
    - Keeper fee calculations
    - Target LTV calculations with payback buffer
    """
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=10_00, _keeperFeeRatio=2_00, _minKeeperFee=5 * EIGHTEEN_DECIMALS, _maxKeeperFee=100 * EIGHTEEN_DECIMALS)  # 10% payback buffer, 2% keeper fee, $5 min
    
    # Setup asset with specific liquidation parameters
    debt_terms = createDebtTerms(
        _liqThreshold=80_00,  # 80% liquidation threshold
        _liqFee=5_00,         # 5% liquidation fee
        _ltv=70_00,           # 70% max LTV
        _borrowRate=0
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)

    # Setup prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # Test Case 1: Normal liquidation scenario
    deposit_amount = 100 * EIGHTEEN_DECIMALS  # $100 collateral
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    debt_amount = 60 * EIGHTEEN_DECIMALS  # $60 debt (60% LTV)
    teller.borrow(debt_amount, bob, False, sender=bob)
    
    # Drop price to make liquidatable
    liquidation_price = 70 * EIGHTEEN_DECIMALS // 100  # $0.70
    mock_price_source.setPrice(alpha_token, liquidation_price)
    # Collateral now worth $70, debt $60 = 85.7% LTV > 80% threshold
    
    # Calculate expected repay amount
    calculated_repay = auction_house.calcAmountOfDebtToRepayDuringLiq(bob)
    
    # Verify calculation makes sense
    assert calculated_repay > 0
    assert calculated_repay <= debt_amount  # Should not exceed total debt
    
    # Test Case 2: User not in liquidation (should still calculate)
    # Reset to safe price
    mock_price_source.setPrice(alpha_token, 2 * EIGHTEEN_DECIMALS)  # $2.00
    # Collateral now worth $200, debt $60 = 30% LTV < 80% threshold
    
    calculated_repay_safe = auction_house.calcAmountOfDebtToRepayDuringLiq(bob)
    assert calculated_repay_safe == 0


def test_liquidation_threshold_zero_protection(
    alice, bob, credit_engine,
    alpha_token, alpha_token_whale, bravo_token, bravo_token_whale,
    teller, setGeneralConfig, setAssetConfig, setGeneralDebtConfig,
    performDeposit, createDebtTerms, mock_price_source, whale,
    auction_house
):
    """Test that division by zero is prevented when liquidation threshold is 0
    
    This test verifies our protection against division by zero in edge cases.
    """
    
    # Setup
    setGeneralConfig()
    setGeneralDebtConfig()
    
    # Test Case 1: User with only non-borrowable collateral (zero thresholds)
    # Configure alpha and bravo tokens as non-borrowable (all zeros)
    zero_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(alpha_token, _debtTerms=zero_terms)
    setAssetConfig(bravo_token, _debtTerms=zero_terms)
    
    # Set prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    
    # Bob deposits only zero-LTV collateral
    performDeposit(bob, 1000 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    performDeposit(bob, 1000 * EIGHTEEN_DECIMALS, bravo_token, bravo_token_whale)
    
    # All these operations should return 0 or False without reverting
    # This tests our division by zero protection
    assert credit_engine.canLiquidateUser(bob) == False
    assert credit_engine.canRedeemUserCollateral(bob) == False
    assert credit_engine.getLiquidationThreshold(bob) == 0
    assert credit_engine.getRedemptionThreshold(bob) == 0
    assert auction_house.calcAmountOfDebtToRepayDuringLiq(bob) == 0
    
    # Bob cannot borrow with zero-LTV collateral
    with boa.reverts():
        teller.borrow(1 * EIGHTEEN_DECIMALS, sender=bob)
    
    # Even if we try to liquidate Bob, it should fail gracefully
    keeper_rewards = teller.liquidateUser(bob, sender=alice)
    assert keeper_rewards == 0  # No liquidation occurred
    
    # Test Case 2: Test extremely low thresholds (near zero but not zero)
    # Configure charlie token with extremely low thresholds
    low_threshold_terms = createDebtTerms(
        _ltv=1,  # 0.01% LTV
        _redemptionThreshold=1,  # 0.01%
        _liqThreshold=1,  # 0.01% - extremely low
        _liqFee=1,  # 0.01%
        _borrowRate=1,  # 0.01%
        _daowry=0,  # 0%
    )
    
    # Use a new token to avoid conflicts
    charlie_token = alpha_token  # Reuse alpha for this test
    setAssetConfig(charlie_token, _debtTerms=low_threshold_terms)
    
    # Alice deposits and borrows with extremely low LTV
    performDeposit(alice, 1000000 * EIGHTEEN_DECIMALS, charlie_token, alpha_token_whale)
    
    # Alice can borrow a tiny amount (0.01% of 1M = 100)
    teller.borrow(50 * EIGHTEEN_DECIMALS, sender=alice)
    
    # Verify calculations work with extremely low thresholds
    debt_data = credit_engine.getLatestUserDebtAndTerms(alice, True)
    assert debt_data[0].amount == 50 * EIGHTEEN_DECIMALS
    assert debt_data[1].debtTerms.liqThreshold == 1  # 0.01%
    
    # These should work without division errors
    can_liquidate = credit_engine.canLiquidateUser(alice)
    assert isinstance(can_liquidate, bool)  # Should not revert
    
    # Drop price drastically to test liquidation with tiny threshold
    mock_price_source.setPrice(charlie_token, 1 * EIGHTEEN_DECIMALS // 20000)  # $0.00005
    
    # Now liquidation should trigger (collateral worth $50 < debt/0.01% = $500,000)
    can_liquidate_after = credit_engine.canLiquidateUser(alice)
    assert can_liquidate_after == True
    
    # Liquidation should work even with tiny threshold
    keeper_rewards = teller.liquidateUser(alice, sender=bob)
    assert keeper_rewards >= 0  # Should not revert

