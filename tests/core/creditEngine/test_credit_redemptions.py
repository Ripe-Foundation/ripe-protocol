import pytest
import boa

from constants import EIGHTEEN_DECIMALS, HUNDRED_PERCENT, ZERO_ADDRESS
from conf_utils import filter_logs


def test_credit_redemption_basic(
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
    green_token,
    whale,
    credit_engine,
    simple_erc20_vault,
    vault_book,
    createDebtTerms,
):
    """Test basic collateral redemption flow"""
    setGeneralConfig()
    
    # Setup asset with redemption threshold
    debt_terms = createDebtTerms(
        _ltv=50_00,  # 50% LTV
        _redemptionThreshold=70_00,  # 70% redemption threshold
        _liqThreshold=80_00,  # 80% liquidation threshold
        _liqFee=10_00,
        _borrowRate=0,
        _daowry=0,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    # Set initial price
    initial_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, initial_price)

    # Bob deposits collateral and borrows
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale)
    
    debt_amount = 100 * EIGHTEEN_DECIMALS  # 50% LTV
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Initially should not be redeemable
    assert not credit_engine.canRedeemUserCollateral(bob)

    # Drop price to trigger redemption threshold
    # Need debt/collateral > 70%
    # With debt = 100 and threshold = 70%, need collateral < 142.86
    # So price needs to be < 0.714
    new_price = 70 * EIGHTEEN_DECIMALS // 100  # 0.70
    mock_price_source.setPrice(alpha_token, new_price)
    
    # Now collateral = 200 * 0.70 = 140
    # Ratio = 100 / 140 = 71.4% > 70% threshold
    assert credit_engine.canRedeemUserCollateral(bob)

    # Alice prepares to redeem
    green_amount = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)

    # Get vault ID
    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Alice redeems collateral
    green_spent = teller.redeemCollateral(bob, vault_id, alpha_token, green_amount, sender=alice)
    
    # Verify redemption occurred
    assert green_spent > 0
    assert green_spent == green_amount

    # Check CollateralRedeemed event
    logs = filter_logs(teller, "CollateralRedeemed")
    assert len(logs) == 1
    log = logs[0]
    assert log.user == bob
    assert log.vaultId == vault_id
    assert log.asset == alpha_token.address
    assert log.redeemer == alice
    assert log.repayValue == green_spent
    
    # Alice should have received collateral
    assert alpha_token.balanceOf(alice) == log.amount

    # Bob's debt should be reduced
    user_debt, _, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    assert user_debt.amount == debt_amount - green_spent


def test_credit_redemption_validation(
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
    green_token,
    whale,
    simple_erc20_vault,
    vault_book,
    createDebtTerms,
    control_room,
):
    """Test validation logic for redemptions"""
    setGeneralConfig()
    
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=70_00,
        _liqThreshold=80_00,
        _liqFee=10_00,
        _borrowRate=0,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    # Set price
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Setup Bob with collateral and debt
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale)
    debt_amount = 100 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Make redeemable
    mock_price_source.setPrice(alpha_token, 70 * EIGHTEEN_DECIMALS // 100)
    
    vault_id = vault_book.getRegId(simple_erc20_vault)
    green_amount = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)

    # Test paused state
    teller.pause(True, sender=control_room.address)
    with boa.reverts("contract paused"):
        teller.redeemCollateral(bob, vault_id, alpha_token, green_amount, sender=alice)
    teller.pause(False, sender=control_room.address)

    # Test zero address user
    with boa.reverts("no redemptions occurred"):
        teller.redeemCollateral(ZERO_ADDRESS, vault_id, alpha_token, green_amount, sender=alice)

    # Test invalid vault ID
    with boa.reverts("no redemptions occurred"):
        teller.redeemCollateral(bob, 999999, alpha_token, green_amount, sender=alice)

    # Test zero address asset
    with boa.reverts("no redemptions occurred"):
        teller.redeemCollateral(bob, vault_id, ZERO_ADDRESS, green_amount, sender=alice)

    # Test zero green amount
    with boa.reverts("cannot transfer 0 amount"):
        teller.redeemCollateral(bob, vault_id, alpha_token, 0, sender=alice)


def test_credit_redemption_user_no_debt(
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
    green_token,
    whale,
    simple_erc20_vault,
    vault_book,
    createDebtTerms,
):
    """Test redemption when user has no debt"""
    setGeneralConfig()
    
    debt_terms = createDebtTerms(_ltv=50_00, _redemptionThreshold=70_00)
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Bob deposits but doesn't borrow
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale)

    # Alice tries to redeem
    vault_id = vault_book.getRegId(simple_erc20_vault)
    green_amount = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)

    # Should not be able to redeem from user with no debt
    with boa.reverts("no redemptions occurred"):
        teller.redeemCollateral(bob, vault_id, alpha_token, green_amount, sender=alice)


def test_credit_redemption_user_in_liquidation(
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
    green_token,
    whale,
    credit_engine,
    simple_erc20_vault,
    vault_book,
    createDebtTerms,
    ledger,
):
    """Test redemption when user is in liquidation"""
    setGeneralConfig()
    
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=70_00,
        _liqThreshold=80_00,
        _liqFee=10_00,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Setup Bob with collateral and debt
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale)
    debt_amount = 100 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Put user in liquidation
    user_debt = ledger.userDebt(bob)
    user_debt = list(user_debt)
    user_debt[4] = True  # inLiquidation = True
    ledger.setUserDebt(bob, tuple(user_debt), 0, (0, 0), sender=credit_engine.address)

    # Make price trigger redemption threshold
    mock_price_source.setPrice(alpha_token, 70 * EIGHTEEN_DECIMALS // 100)

    # Alice tries to redeem
    vault_id = vault_book.getRegId(simple_erc20_vault)
    green_amount = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)

    # Should not be able to redeem from user in liquidation
    with boa.reverts("no redemptions occurred"):
        teller.redeemCollateral(bob, vault_id, alpha_token, green_amount, sender=alice)


def test_credit_redemption_below_threshold(
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
    green_token,
    whale,
    credit_engine,
    simple_erc20_vault,
    vault_book,
    createDebtTerms,
):
    """Test redemption when user is below redemption threshold"""
    setGeneralConfig()
    
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=70_00,
        _liqThreshold=80_00,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Setup Bob with safe collateral ratio
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale)
    debt_amount = 100 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Price drop but not enough to trigger redemption
    # Need debt/collateral <= 70%
    # With debt = 100, collateral = 200 * 0.75 = 150
    # Ratio = 100 / 150 = 66.7% < 70% threshold
    mock_price_source.setPrice(alpha_token, 75 * EIGHTEEN_DECIMALS // 100)
    
    assert not credit_engine.canRedeemUserCollateral(bob)

    # Alice tries to redeem
    vault_id = vault_book.getRegId(simple_erc20_vault)
    green_amount = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)

    with boa.reverts("no redemptions occurred"):
        teller.redeemCollateral(bob, vault_id, alpha_token, green_amount, sender=alice)


def test_credit_redemption_config_disabled(
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
    green_token,
    whale,
    credit_engine,
    simple_erc20_vault,
    vault_book,
    createDebtTerms,
):
    """Test redemption when config is disabled"""
    setGeneralConfig()
    
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=70_00,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Setup Bob with redeemable position
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale)
    debt_amount = 100 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Make redeemable
    mock_price_source.setPrice(alpha_token, 70 * EIGHTEEN_DECIMALS // 100)
    assert credit_engine.canRedeemUserCollateral(bob)

    # Prepare redemption
    vault_id = vault_book.getRegId(simple_erc20_vault)
    green_amount = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)

    # Test 1: Disable general redemption config
    setGeneralConfig(_canRedeemCollateral=False)
    with boa.reverts("no redemptions occurred"):
        teller.redeemCollateral(bob, vault_id, alpha_token, green_amount, sender=alice)

    # Re-enable general config
    setGeneralConfig()

    # Test 2: Disable asset-specific redemption config
    setAssetConfig(alpha_token, _debtTerms=debt_terms, _canRedeemCollateral=False)
    with boa.reverts("no redemptions occurred"):
        teller.redeemCollateral(bob, vault_id, alpha_token, green_amount, sender=alice)

    # Re-enable and verify it works
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    green_spent = teller.redeemCollateral(bob, vault_id, alpha_token, green_amount, sender=alice)
    assert green_spent > 0


def test_credit_redemption_ltv_payback_buffer(
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
    green_token,
    whale,
    credit_engine,
    simple_erc20_vault,
    vault_book,
    createDebtTerms,
):
    """Test redemption with LTV payback buffer"""
    setGeneralConfig()
    
    debt_terms = createDebtTerms(
        _ltv=60_00,  # 60% LTV
        _redemptionThreshold=70_00,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    
    # Set 10% payback buffer
    setGeneralDebtConfig(_ltvPaybackBuffer=10_00)  # 10%

    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Setup Bob
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale)
    debt_amount = 100 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Make redeemable
    mock_price_source.setPrice(alpha_token, 70 * EIGHTEEN_DECIMALS // 100)

    # Prepare large redemption
    vault_id = vault_book.getRegId(simple_erc20_vault)
    green_amount = 200 * EIGHTEEN_DECIMALS  # Large amount
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)

    # Redeem
    teller.redeemCollateral(bob, vault_id, alpha_token, green_amount, sender=alice)

    # Check that redemption targets LTV with buffer
    # Target LTV = 60% * (100% - 10%) = 54%
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    
    actual_ltv = user_debt.amount * HUNDRED_PERCENT // bt.collateralVal
    # Should be close to 54% (allowing for rounding)
    assert abs(actual_ltv - 54_00) < 100  # Within 1%


def test_credit_redemption_partial(
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
    green_token,
    whale,
    credit_engine,
    simple_erc20_vault,
    vault_book,
    createDebtTerms,
    _test,
):
    """Test partial redemption when green amount is less than needed"""
    setGeneralConfig()
    
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=70_00,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Setup Bob
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale)
    debt_amount = 100 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Make redeemable - price drops to 0.70
    # Collateral value = 200 * 0.70 = 140
    # Debt = 100
    # Ratio = 100/140 = 71.4% > 70% threshold
    mock_price_source.setPrice(alpha_token, 70 * EIGHTEEN_DECIMALS // 100)
    
    # Verify Bob is redeemable
    assert credit_engine.canRedeemUserCollateral(bob)

    # Small redemption amount
    vault_id = vault_book.getRegId(simple_erc20_vault)
    green_amount = 10 * EIGHTEEN_DECIMALS  # Small amount
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)

    # Get initial debt
    initial_debt, bt_initial, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)

    # Redeem
    green_spent = teller.redeemCollateral(bob, vault_id, alpha_token, green_amount, sender=alice)
    
    # Should use all the green
    _test(green_amount, green_spent)

    # Debt should be reduced by green_spent
    final_debt, bt_final, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    _test(initial_debt.amount - green_spent, final_debt.amount)
    
    # After small redemption:
    # New debt = 100 - 10 = 90
    # Collateral taken = approximately 10 (since green = $1)
    # New collateral value = 140 - 10 = 130
    # New ratio = 90/130 = 69.2% < 70% threshold
    # So Bob should no longer be redeemable
    
    # Verify Bob is no longer redeemable after this redemption
    assert not credit_engine.canRedeemUserCollateral(bob)


def test_credit_redemption_multiple_assets(
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob,
    alice,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    green_token,
    whale,
    credit_engine,
    simple_erc20_vault,
    vault_book,
    createDebtTerms,
    _test,
):
    """Test redemption when user has multiple collateral assets"""
    setGeneralConfig()
    
    # Setup both assets with same terms
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=70_00,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setAssetConfig(bravo_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    # Set initial prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)

    # Bob deposits both assets
    alpha_amount = 100 * EIGHTEEN_DECIMALS
    bravo_amount = 50 * EIGHTEEN_DECIMALS
    performDeposit(bob, alpha_amount, alpha_token, alpha_token_whale)
    performDeposit(bob, bravo_amount, bravo_token, bravo_token_whale)

    # Total collateral value = 100 * 1 + 50 * 2 = 200
    # Borrow at 50% LTV
    debt_amount = 100 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Drop both prices to trigger redemption
    mock_price_source.setPrice(alpha_token, 70 * EIGHTEEN_DECIMALS // 100)
    mock_price_source.setPrice(bravo_token, 140 * EIGHTEEN_DECIMALS // 100)
    
    assert credit_engine.canRedeemUserCollateral(bob)

    vault_id = vault_book.getRegId(simple_erc20_vault)
    green_amount = 30 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)

    # Redeem from alpha token
    green_spent = teller.redeemCollateral(bob, vault_id, alpha_token, green_amount, sender=alice)
    assert green_spent > 0
    assert alpha_token.balanceOf(alice) > 0

    # After first redemption of 30 GREEN:
    # - Debt reduced from 100 to 70
    # - Collateral value reduced by ~30 (at price 0.70)
    # - New collateral ≈ 110 (140 - 30)
    # - New ratio = 70/110 = 63.6% < 70% threshold
    # Bob should no longer be redeemable
    assert not credit_engine.canRedeemUserCollateral(bob)
    
    # Second redemption attempt should fail
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)
    with boa.reverts("no redemptions occurred"):
        teller.redeemCollateral(bob, vault_id, bravo_token, green_amount, sender=alice)


def test_credit_redeem_many_basic(
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob,
    sally,
    alice,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    green_token,
    whale,
    simple_erc20_vault,
    vault_book,
    createDebtTerms,
):
    """Test redeemCollateralFromMany with multiple redemptions"""
    setGeneralConfig()
    
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=70_00,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setAssetConfig(bravo_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    # Set prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Setup Bob with alpha token
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    # Setup Sally with bravo token  
    performDeposit(sally, 200 * EIGHTEEN_DECIMALS, bravo_token, bravo_token_whale)
    teller.borrow(100 * EIGHTEEN_DECIMALS, sally, False, sender=sally)

    # Make both redeemable
    mock_price_source.setPrice(alpha_token, 70 * EIGHTEEN_DECIMALS // 100)
    mock_price_source.setPrice(bravo_token, 70 * EIGHTEEN_DECIMALS // 100)

    # Prepare redemptions
    redemptions = [
        (bob, vault_id, alpha_token.address, 30 * EIGHTEEN_DECIMALS),
        (sally, vault_id, bravo_token.address, 40 * EIGHTEEN_DECIMALS),
    ]

    green_amount = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)

    # Redeem from many
    total_green_spent = teller.redeemCollateralFromMany(redemptions, green_amount, sender=alice)

    # Check results
    assert total_green_spent == 70 * EIGHTEEN_DECIMALS  # 30 + 40
    assert alpha_token.balanceOf(alice) > 0
    assert bravo_token.balanceOf(alice) > 0

    # Check events
    logs = filter_logs(teller, "CollateralRedeemed")
    assert len(logs) == 2
    
    # First redemption (Bob's alpha)
    assert logs[0].user == bob
    assert logs[0].asset == alpha_token.address
    assert logs[0].repayValue == 30 * EIGHTEEN_DECIMALS
    
    # Second redemption (Sally's bravo)
    assert logs[1].user == sally
    assert logs[1].asset == bravo_token.address
    assert logs[1].repayValue == 40 * EIGHTEEN_DECIMALS


def test_credit_redeem_many_insufficient_green(
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    alice,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    green_token,
    whale,
    simple_erc20_vault,
    vault_book,
    createDebtTerms,
    _test,
):
    """Test redeemCollateralFromMany when green runs out"""
    setGeneralConfig()
    
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=70_00,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Setup two users
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    
    performDeposit(sally, 200 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    teller.borrow(100 * EIGHTEEN_DECIMALS, sally, False, sender=sally)

    # Make redeemable
    mock_price_source.setPrice(alpha_token, 70 * EIGHTEEN_DECIMALS // 100)

    # Redemptions that would require more green than available
    redemptions = [
        (bob, vault_id, alpha_token.address, 50 * EIGHTEEN_DECIMALS),
        (sally, vault_id, alpha_token.address, 50 * EIGHTEEN_DECIMALS),
    ]

    # Only provide 60 GREEN (less than 100 requested)
    green_amount = 60 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)

    # Redeem
    total_green_spent = teller.redeemCollateralFromMany(redemptions, green_amount, sender=alice)

    # Should have used all available green
    _test(green_amount, total_green_spent)

    # Check events - should have redeemed from Bob fully and Sally partially
    logs = filter_logs(teller, "CollateralRedeemed")
    assert len(logs) == 2
    assert logs[0].repayValue == 50 * EIGHTEEN_DECIMALS  # Bob got full amount
    assert logs[1].repayValue == 10 * EIGHTEEN_DECIMALS  # Sally got remainder


def test_credit_redeem_many_empty_array(
    alice,
    teller,
    green_token,
    whale,
):
    """Test redeemCollateralFromMany with empty array"""
    green_amount = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)

    # Empty redemptions array should revert
    with boa.reverts("no redemptions occurred"):
        teller.redeemCollateralFromMany([], green_amount, sender=alice)


def test_credit_redeem_many_invalid_entries(
    alpha_token,
    alice,
    teller,
    green_token,
    whale,
    simple_erc20_vault,
    vault_book,
):
    """Test redeemCollateralFromMany with invalid entries"""
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # All invalid redemptions
    redemptions = [
        (ZERO_ADDRESS, vault_id, alpha_token.address, 10 * EIGHTEEN_DECIMALS),  # Zero user
        (alice, 0, alpha_token.address, 10 * EIGHTEEN_DECIMALS),  # Zero vault ID
        (alice, vault_id, ZERO_ADDRESS, 10 * EIGHTEEN_DECIMALS),  # Zero asset
        (alice, vault_id, alpha_token.address, 0),  # Zero amount
    ]

    green_amount = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)

    # Should revert since no valid redemptions
    with boa.reverts("no redemptions occurred"):
        teller.redeemCollateralFromMany(redemptions, green_amount, sender=alice)


def test_credit_redemption_refund_regular(
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
    green_token,
    whale,
    simple_erc20_vault,
    vault_book,
    createDebtTerms,
    _test,
):
    """Test redemption refund as regular GREEN tokens"""
    setGeneralConfig()
    
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=70_00,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Setup Bob with small redeemable position
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    # Make redeemable
    mock_price_source.setPrice(alpha_token, 70 * EIGHTEEN_DECIMALS // 100)

    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # Alice provides more green than needed
    green_amount = 200 * EIGHTEEN_DECIMALS  # Way more than needed
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)

    initial_green_balance = green_token.balanceOf(alice)

    # Redeem with shouldStakeRefund=False
    green_spent = teller.redeemCollateral(bob, vault_id, alpha_token, green_amount, False, sender=alice)

    # Alice should get refund as regular GREEN
    final_green_balance = green_token.balanceOf(alice)
    refund_amount = green_amount - green_spent
    _test(refund_amount, final_green_balance)


def test_credit_redemption_refund_savings(
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
    green_token,
    whale,
    simple_erc20_vault,
    vault_book,
    createDebtTerms,
    savings_green,
    _test,
):
    """Test redemption refund as savings GREEN tokens"""
    setGeneralConfig()
    
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=70_00,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Setup Bob with small redeemable position
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    # Make redeemable
    mock_price_source.setPrice(alpha_token, 70 * EIGHTEEN_DECIMALS // 100)

    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # Alice provides more green than needed
    green_amount = 200 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)

    initial_savings_balance = savings_green.balanceOf(alice)

    # Redeem with shouldStakeRefund=True (default)
    green_spent = teller.redeemCollateral(bob, vault_id, alpha_token, green_amount, sender=alice)

    # Alice should get refund as savings GREEN
    final_savings_balance = savings_green.balanceOf(alice)
    assert final_savings_balance > initial_savings_balance
    
    # Verify the savings green amount
    refund_amount = green_amount - green_spent
    savings_received = final_savings_balance - initial_savings_balance
    _test(refund_amount, savings_green.getLastUnderlying(savings_received))


def test_credit_redemption_price_oracle_issues(
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
    green_token,
    whale,
    simple_erc20_vault,
    vault_book,
    createDebtTerms,
):
    """Test redemption with price oracle issues"""
    setGeneralConfig()
    
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=70_00,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Setup Bob
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    # Make redeemable
    mock_price_source.setPrice(alpha_token, 70 * EIGHTEEN_DECIMALS // 100)

    vault_id = vault_book.getRegId(simple_erc20_vault)
    green_amount = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)

    # Set price to 0 (oracle failure)
    mock_price_source.setPrice(alpha_token, 0)

    # Should fail due to price calculation issues
    with boa.reverts("no redemptions occurred"):
        teller.redeemCollateral(bob, vault_id, alpha_token, green_amount, sender=alice)


def test_credit_redemption_user_no_balance(
    alpha_token,
    bravo_token,
    bravo_token_whale,
    bob,
    alice,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    green_token,
    whale,
    simple_erc20_vault,
    vault_book,
    createDebtTerms,
):
    """Test redemption when user has no balance of requested asset"""
    setGeneralConfig()
    
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=70_00,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setAssetConfig(bravo_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)

    # Bob deposits bravo but not alpha
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, bravo_token, bravo_token_whale)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    # Make redeemable
    mock_price_source.setPrice(bravo_token, 70 * EIGHTEEN_DECIMALS // 100)

    vault_id = vault_book.getRegId(simple_erc20_vault)
    green_amount = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)

    # Try to redeem alpha (which Bob doesn't have)
    with boa.reverts("no redemptions occurred"):
        teller.redeemCollateral(bob, vault_id, alpha_token, green_amount, sender=alice)


def test_credit_redemption_math_calculation(
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
    green_token,
    whale,
    credit_engine,
    simple_erc20_vault,
    vault_book,
    createDebtTerms,
    _test,
):
    """Test redemption math calculations are correct"""
    setGeneralConfig()
    
    debt_terms = createDebtTerms(
        _ltv=60_00,  # 60% LTV
        _redemptionThreshold=70_00,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig(_ltvPaybackBuffer=0)  # No buffer for easier math

    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Setup Bob
    collateral_amount = 1000 * EIGHTEEN_DECIMALS  # 1000 tokens
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale)
    debt_amount = 500 * EIGHTEEN_DECIMALS  # 500 debt (50% LTV)
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Drop price so collateral = 700, debt = 500
    # Ratio = 500 / 700 = 71.4% > 70% threshold
    new_price = 70 * EIGHTEEN_DECIMALS // 100
    mock_price_source.setPrice(alpha_token, new_price)

    # Calculate expected redemption to reach target LTV (60%)
    # Target: debt / collateral = 0.6
    # Let x = amount to pay
    # (500 - x) / (700 - x) = 0.6
    # 500 - x = 0.6 * (700 - x)
    # 500 - x = 420 - 0.6x
    # 500 - 420 = x - 0.6x
    # 80 = 0.4x
    # x = 200

    vault_id = vault_book.getRegId(simple_erc20_vault)
    green_amount = 300 * EIGHTEEN_DECIMALS  # More than needed
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)

    # Redeem
    green_spent = teller.redeemCollateral(bob, vault_id, alpha_token, green_amount, sender=alice)

    # Should spend approximately 200 GREEN
    assert abs(green_spent - 200 * EIGHTEEN_DECIMALS) < EIGHTEEN_DECIMALS  # Within 1 token

    # Verify final LTV is close to target (60%)
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    final_ltv = user_debt.amount * HUNDRED_PERCENT // bt.collateralVal
    assert abs(final_ltv - 60_00) < 100  # Within 1%


def test_can_redeem_user_collateral(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    createDebtTerms,
):
    """Test canRedeemUserCollateral function in various scenarios"""
    setGeneralConfig()
    
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=70_00,
        _liqThreshold=80_00,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Test 1: User with no debt - should not be redeemable
    assert not credit_engine.canRedeemUserCollateral(bob)

    # Test 2: User with good collateral ratio
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale)
    debt_amount = 80 * EIGHTEEN_DECIMALS  # 40% LTV
    teller.borrow(debt_amount, bob, False, sender=bob)
    
    # Ratio = 80/200 = 40% < 70% threshold
    assert not credit_engine.canRedeemUserCollateral(bob)

    # Test 3: Price drop to exactly redemption threshold
    # Need debt/collateral = 70%
    # 80 / (200 * price) = 0.70
    # price = 80 / (200 * 0.70) = 0.571
    mock_price_source.setPrice(alpha_token, 571 * EIGHTEEN_DECIMALS // 1000)
    assert credit_engine.canRedeemUserCollateral(bob)

    # Test 4: Price drop beyond redemption threshold
    mock_price_source.setPrice(alpha_token, 50 * EIGHTEEN_DECIMALS // 100)
    assert credit_engine.canRedeemUserCollateral(bob)

    # Test 5: Price recovery to safe level
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    assert not credit_engine.canRedeemUserCollateral(bob)


def test_get_max_redeem_value(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    createDebtTerms,
):
    """Test getMaxRedeemValue function"""
    setGeneralConfig()
    
    debt_terms = createDebtTerms(
        _ltv=60_00,  # 60% LTV
        _redemptionThreshold=70_00,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    
    # Test with 10% payback buffer
    setGeneralDebtConfig(_ltvPaybackBuffer=10_00)

    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Test 1: User with no debt
    assert credit_engine.getMaxRedeemValue(bob) == 0

    # Test 2: User with healthy position
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale)
    debt_amount = 100 * EIGHTEEN_DECIMALS  # 50% LTV
    teller.borrow(debt_amount, bob, False, sender=bob)
    
    # Not redeemable yet
    assert credit_engine.getMaxRedeemValue(bob) == 0

    # Test 3: User is redeemable
    # Drop price to make redeemable
    mock_price_source.setPrice(alpha_token, 70 * EIGHTEEN_DECIMALS // 100)
    
    # Now collateral = 200 * 0.70 = 140
    # Debt = 100
    # Ratio = 100/140 = 71.4% > 70% threshold
    
    max_redeem = credit_engine.getMaxRedeemValue(bob)
    assert max_redeem > 0
    
    # With 10% buffer, target LTV = 60% * 90% = 54%
    # To calculate expected max redeem:
    # (100 - x) / (140 - x) = 0.54
    # 100 - x = 0.54 * (140 - x)
    # 100 - x = 75.6 - 0.54x
    # 24.4 = 0.46x
    # x = 53.04
    
    expected_max = 53 * EIGHTEEN_DECIMALS  # Approximately
    assert abs(max_redeem - expected_max) < 2 * EIGHTEEN_DECIMALS  # Within 2 tokens


def test_get_redemption_threshold(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    createDebtTerms,
    _test,
):
    """Test getRedemptionThreshold function"""
    setGeneralConfig()
    
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=75_00,  # 75%
        _liqThreshold=85_00,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Test 1: User with no debt - should return 0
    threshold = credit_engine.getRedemptionThreshold(bob)
    assert threshold == 0

    # Test 2: User with debt
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale)
    debt_amount = 90 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)
    
    # Redemption threshold = debt * 100% / redemptionThreshold%
    # = 90 * 100% / 75% = 120
    threshold = credit_engine.getRedemptionThreshold(bob)
    expected_threshold = 120 * EIGHTEEN_DECIMALS
    _test(expected_threshold, threshold)
    
    # This represents the collateral value at which redemption is triggered
    # If collateral falls to 120 or below, redemption can occur


def test_get_redemption_threshold_multiple_assets(
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    createDebtTerms,
    _test,
):
    """Test getRedemptionThreshold with multiple collateral assets"""
    setGeneralConfig()
    
    # Different terms for each asset
    alpha_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=70_00,
    )
    bravo_terms = createDebtTerms(
        _ltv=60_00,
        _redemptionThreshold=80_00,
    )
    
    setAssetConfig(alpha_token, _debtTerms=alpha_terms)
    setAssetConfig(bravo_token, _debtTerms=bravo_terms)
    setGeneralDebtConfig()

    # Set prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)

    # Deposit both assets
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    performDeposit(bob, 50 * EIGHTEEN_DECIMALS, bravo_token, bravo_token_whale)
    
    # Total collateral value = 100 + 100 = 200
    # Max debt from alpha = 100 * 50% = 50
    # Max debt from bravo = 100 * 60% = 60
    # Total max debt = 110
    
    # Borrow 80
    debt_amount = 80 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)
    
    # The weighted average redemption threshold should be calculated
    threshold = credit_engine.getRedemptionThreshold(bob)
    
    # Weighted redemption threshold = (50 * 70% + 60 * 80%) / 110 = 75.45%
    # Threshold value = 80 * 100% / 75.45% = 106.05
    expected_threshold = 106 * EIGHTEEN_DECIMALS  # Approximately
    assert abs(threshold - expected_threshold) < 2 * EIGHTEEN_DECIMALS


def test_utility_functions_edge_cases(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    createDebtTerms,
    ledger,
):
    """Test utility functions with edge cases"""
    setGeneralConfig()
    
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=70_00,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Setup position
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    # Test with user in liquidation
    user_debt = ledger.userDebt(bob)
    user_debt = list(user_debt)
    user_debt[4] = True  # inLiquidation = True
    ledger.setUserDebt(bob, tuple(user_debt), 0, (0, 0), sender=credit_engine.address)
    
    # Should return 0 when in liquidation
    assert credit_engine.getMaxRedeemValue(bob) == 0
    
    # Reset liquidation status
    user_debt[4] = False
    ledger.setUserDebt(bob, tuple(user_debt), 0, (0, 0), sender=credit_engine.address)
    
    # Test with zero collateral value (price = 0)
    mock_price_source.setPrice(alpha_token, 0)

    user_debt = ledger.userDebt(bob)
    debt_amount = user_debt[0]  # Get the debt amount

    # When price is 0, collateral value becomes 0
    # With debt > 0 and collateral = 0, the user is technically underwater
    # canRedeemUserCollateral returns True because collateral (0) <= redemptionThreshold
    assert credit_engine.canRedeemUserCollateral(bob)
    
    # getMaxRedeemValue returns 0 because even though user is redeemable,
    # there's no collateral value to actually redeem
    assert credit_engine.getMaxRedeemValue(bob) == 0
    
    # getRedemptionThreshold calculation:
    # The function uses the redemption threshold from the user's debt terms
    # which was set when they borrowed (70% in this case)
    # Formula: debt * 100% / redemptionThreshold
    # = 100 * 10^18 * 100_00 / 70_00 = 142.857 * 10^18
    threshold = credit_engine.getRedemptionThreshold(bob)
    # The threshold represents the collateral value at which redemption would trigger
    # Even with price = 0, it still calculates based on the original debt terms
    expected_threshold = debt_amount * HUNDRED_PERCENT // 70_00  # 70% redemption threshold
    assert threshold == expected_threshold


def test_can_redeem_vs_can_liquidate(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    createDebtTerms,
):
    """Test relationship between redemption and liquidation thresholds"""
    setGeneralConfig()
    
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=70_00,
        _liqThreshold=80_00,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Setup position
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    # Test at different price levels
    # 1. Healthy position
    assert not credit_engine.canRedeemUserCollateral(bob)
    assert not credit_engine.canLiquidateUser(bob)
    
    # 2. Redeemable but not liquidatable
    # Need 70% < debt/collateral < 80%
    mock_price_source.setPrice(alpha_token, 65 * EIGHTEEN_DECIMALS // 100)
    # Collateral = 200 * 0.65 = 130
    # Ratio = 100/130 = 76.9%
    assert credit_engine.canRedeemUserCollateral(bob)
    assert not credit_engine.canLiquidateUser(bob)
    
    # 3. Both redeemable and liquidatable
    mock_price_source.setPrice(alpha_token, 50 * EIGHTEEN_DECIMALS // 100)
    # Collateral = 200 * 0.50 = 100
    # Ratio = 100/100 = 100%
    assert credit_engine.canRedeemUserCollateral(bob)
    assert credit_engine.canLiquidateUser(bob)
