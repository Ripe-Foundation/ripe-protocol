import pytest
import boa
from constants import EIGHTEEN_DECIMALS
from conf_utils import filter_logs

SIX_DECIMALS = 10**6  # For tokens like USDC/Charlie that have 6 decimals


@pytest.fixture(autouse=True)
def setup(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    alpha_token,
    bravo_token,
    charlie_token,
    delta_token,
    setup_priority_configs,
    mock_price_source,
):
    setGeneralConfig()
    setGeneralDebtConfig()

    # Standard debt terms for stablecoins
    debt_terms = createDebtTerms(
        _ltv=80_00,
        _redemptionThreshold=85_00,
        _liqThreshold=90_00,
        _liqFee=5_00,
        _borrowRate=0,
    )

    # Configure all tokens to use simple_erc20_vault (vault_id=3)
    # One vault can hold multiple asset types

    # Configure alpha_token (18 decimals)
    setAssetConfig(
        alpha_token,
        _vaultIds=[3],
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,  # Phase 2 transfer
    )

    # Configure bravo_token (18 decimals)
    setAssetConfig(
        bravo_token,
        _vaultIds=[3],
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,  # Phase 2 transfer
    )

    # Configure charlie_token (6 decimals)
    setAssetConfig(
        charlie_token,
        _vaultIds=[3],
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,  # Phase 2 transfer
    )

    # Configure delta_token (8 decimals)
    setAssetConfig(
        delta_token,
        _vaultIds=[3],
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,  # Phase 2 transfer
    )

    # Set prices for all tokens (assume all are $1 stablecoins)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(delta_token, 1 * EIGHTEEN_DECIMALS)

    # Configure EMPTY priority stab assets to isolate Phase 2
    setup_priority_configs(
        priority_stab_assets=[],  # Empty - skip Phase 1
        priority_liq_assets=[],  # Will be set per test
    )


def test_basic_endaoment_transfer(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    credit_engine,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    endaoment_funds,
    setupDeleverage,
    setup_priority_configs,
    _test,
    switchboard_alpha,
):
    """
    Test basic Phase 2 functionality: single asset transfer to Endaoment.

    SCENARIO: Single asset, single vault, full deleverage
    - User has 1000 alpha tokens as collateral
    - User has 500 GREEN debt
    - Phase 2 configured to transfer alpha to Endaoment

    EXPECTED:
    - 500 alpha tokens transferred to Endaoment
    - User's vault balance reduced by 500
    - Debt fully repaid
    - EndaomentTransferDuringDeleverage event emitted with correct values

    VALIDATES: Core Phase 2 transfer mechanism (Lines 437-460 in Deleverage.vy)
    """
    # Setup user with alpha_token collateral and debt
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Configure Phase 2 priority list
    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[
            (simple_erc20_vault, alpha_token),
        ]
    )

    # Pre-state
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    pre_user_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    pre_endaoment_balance = alpha_token.balanceOf(endaoment_funds)

    assert pre_debt > 0, "User should have debt"
    assert pre_user_balance >= pre_debt, "User should have sufficient collateral"

    # Deleverage
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Get events immediately
    transfer_log = filter_logs(teller, "EndaomentTransferDuringDeleverage")[0]
    deleverage_log = filter_logs(teller, "DeleverageUser")[0]

    # Verify collateral transferred
    post_user_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    post_endaoment_balance = alpha_token.balanceOf(endaoment_funds)

    transferred_amount = pre_user_balance - post_user_balance
    endaoment_received = post_endaoment_balance - pre_endaoment_balance

    _test(transferred_amount, endaoment_received)
    _test(transferred_amount, pre_debt)

    # Verify debt reduced
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    debt_reduction = pre_debt - post_debt
    _test(repaid_amount, debt_reduction)
    _test(debt_reduction, pre_debt)

    # Verify EndaomentTransferDuringDeleverage event
    assert transfer_log.user == bob
    assert transfer_log.vaultId == 3  # simple_erc20_vault
    assert transfer_log.asset == alpha_token.address
    _test(transfer_log.amountSent, transferred_amount)
    _test(transfer_log.usdValue, debt_reduction)
    assert transfer_log.isDepleted == False  # User has 500 collateral remaining

    # Verify DeleverageUser event
    assert deleverage_log.user == bob
    assert deleverage_log.caller == switchboard_alpha.address  # caller is now msg.sender
    assert deleverage_log.targetRepayAmount == pre_debt
    _test(deleverage_log.repaidAmount, repaid_amount)
    assert deleverage_log.hasGoodDebtHealth == True


def test_multiple_assets_priority_order(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    credit_engine,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    setupDeleverage,
    performDeposit,
    setup_priority_configs,
    _test,
    switchboard_alpha,
):
    """
    Test Phase 2 priority order: alpha_token should be processed before bravo_token.
    Both assets needed to fully repay debt.

    Setup: 200 alpha collateral, 400 total debt (requires both assets)
    """
    # Setup user with LIMITED alpha_token collateral
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=300 * EIGHTEEN_DECIMALS,  # Limited alpha
        borrow_amount=150 * EIGHTEEN_DECIMALS,   # Max alpha can support
        get_sgreen=False,
    )

    # Give user bravo_token collateral and borrow more
    # This creates additional debt that requires bravo to cover
    bravo_token.transfer(bob, 200 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, bravo_token, bob, simple_erc20_vault)

    # Borrow more using bravo as collateral
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    # Configure Phase 2 with priority order
    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[
            (simple_erc20_vault, bravo_token),   # First priority
            (simple_erc20_vault, alpha_token),  # Second priority
        ]
    )

    # Pre-state
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    pre_alpha_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    pre_bravo_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)

    # Deleverage
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Get events
    transfer_logs = filter_logs(teller, "EndaomentTransferDuringDeleverage")

    # Should have 2 transfer events
    assert len(transfer_logs) == 2, "Should have 2 transfer events"

    # Verify priority order: bravo_token first
    assert transfer_logs[0].asset == bravo_token.address
    assert transfer_logs[0].vaultId == 3
    assert transfer_logs[0].isDepleted == True

    # alpha_token second
    assert transfer_logs[1].asset == alpha_token.address
    assert transfer_logs[1].vaultId == 3
    assert transfer_logs[1].isDepleted == False

    # Verify both assets were transferred
    post_alpha_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    post_bravo_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)

    assert post_bravo_balance == 0
    assert post_alpha_balance < pre_alpha_balance

    # Verify debt fully repaid
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    _test(post_debt, 0)
    _test(repaid_amount, pre_debt)


def test_multiple_assets_first_sufficient(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    credit_engine,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    setupDeleverage,
    performDeposit,
    setup_priority_configs,
    bob,
    _test,
    switchboard_alpha,
):
    """
    Test Phase 2 when first priority asset is sufficient to cover debt.
    Second asset should not be touched.
    """
    # Setup user with sufficient alpha_token
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=400 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Give user bravo_token collateral (should not be touched)
    bravo_token.transfer(bob, 500 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    performDeposit(bob, 500 * EIGHTEEN_DECIMALS, bravo_token, bob, simple_erc20_vault)

    # Configure Phase 2 priority
    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[
            (simple_erc20_vault, alpha_token),
            (simple_erc20_vault, bravo_token),
        ]
    )

    # Pre-state
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    pre_alpha_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    pre_bravo_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)

    # Deleverage
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Get events
    transfer_logs = filter_logs(teller, "EndaomentTransferDuringDeleverage")

    # Should have only 1 transfer event (alpha_token only)
    assert len(transfer_logs) == 1, "Should have only 1 transfer event"
    assert transfer_logs[0].asset == alpha_token.address

    # Verify alpha_token used, bravo_token untouched
    post_alpha_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    post_bravo_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)

    assert post_alpha_balance < pre_alpha_balance, "Alpha should be used"
    assert post_bravo_balance == pre_bravo_balance, "Bravo should be untouched"

    # Verify debt fully repaid
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    _test(post_debt, 0)
    _test(repaid_amount, pre_debt)


def test_multiple_assets_both_needed(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    credit_engine,
    simple_erc20_vault,
    bob,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    setupDeleverage,
    performDeposit,
    setup_priority_configs,
    alpha_token,
    _test,
    switchboard_alpha,
):
    """
    Test Phase 2 when both assets are needed.

    Setup: 250 alpha + 250 bravo = 500 collateral, ~400 debt
    First asset (alpha) fully depleted, second asset (bravo) partially used.
    """
    # Setup user with limited alpha_token
    # 250 alpha allows ~200 borrow at 80% LTV
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=250 * EIGHTEEN_DECIMALS,
        borrow_amount=200 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Give user limited bravo_token and borrow more
    # 250 bravo allows ~200 more borrow
    bravo_token.transfer(bob, 250 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    performDeposit(bob, 250 * EIGHTEEN_DECIMALS, bravo_token, bob, simple_erc20_vault)
    teller.borrow(200 * EIGHTEEN_DECIMALS, bob, False, sender=bob)  # Additional debt

    # Configure Phase 2
    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[
            (simple_erc20_vault, alpha_token),
            (simple_erc20_vault, bravo_token),
        ]
    )

    # Pre-state
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    pre_alpha_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    pre_bravo_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)

    # Total collateral (500) should cover total debt (~400)
    total_collateral = pre_alpha_balance + pre_bravo_balance

    # Deleverage
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Get events
    transfer_logs = filter_logs(teller, "EndaomentTransferDuringDeleverage")

    # Should have 2 transfer events
    assert len(transfer_logs) == 2
    assert transfer_logs[0].asset == alpha_token.address
    assert transfer_logs[0].isDepleted == True  # Alpha fully used (250)
    assert transfer_logs[1].asset == bravo_token.address
    assert transfer_logs[1].isDepleted == False  # Bravo partially used (150/250)

    # Verify alpha depleted, bravo partially used
    post_alpha_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    post_bravo_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)

    assert post_alpha_balance == 0, "Alpha should be fully depleted"
    assert post_bravo_balance > 0, "Bravo should have remainder"
    assert post_bravo_balance < pre_bravo_balance, "Bravo should be partially used"

    # Debt fully repaid (400 debt covered by 250 alpha + 150 bravo)
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    assert post_debt == 0, "Debt should be fully repaid"
    _test(repaid_amount, pre_debt)


def test_no_balance_in_priority_asset(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    credit_engine,
    simple_erc20_vault,
    bob,
    alpha_token,
    bravo_token,
    bravo_token_whale,
    setupDeleverage,
    setup_priority_configs,
    _test,
    switchboard_alpha,
):
    """
    Test Phase 2 when user has no balance in first priority asset.
    Should skip to second priority asset.
    """
    # Setup user with bravo_token only (NO alpha_token)
    # Use bravo for collateral instead of alpha
    setupDeleverage(
        bob,
        bravo_token,  # Using bravo, not alpha
        bravo_token_whale,
        deposit_amount=500 * EIGHTEEN_DECIMALS,
        borrow_amount=400 * EIGHTEEN_DECIMALS,  # 80% LTV
        get_sgreen=False,
    )

    # Configure Phase 2: alpha first (will be skipped), then bravo
    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[
            (simple_erc20_vault, alpha_token),  # No balance - will skip
            (simple_erc20_vault, bravo_token),   # Will use this
        ]
    )

    # Verify no alpha balance
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0

    # Pre-state
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    pre_bravo_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)

    # Deleverage
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Get events
    transfer_logs = filter_logs(teller, "EndaomentTransferDuringDeleverage")

    # Should have only 1 event (bravo_token, alpha skipped)
    assert len(transfer_logs) == 1
    assert transfer_logs[0].asset == bravo_token.address, "Should only use bravo_token"

    # Verify bravo used
    post_bravo_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    assert post_bravo_balance < pre_bravo_balance

    # Verify debt reduced
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    _test(post_debt, 0)


def test_empty_priority_list(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    bob,
    alpha_token,
    alpha_token_whale,
    setupDeleverage,
    setup_priority_configs,
    switchboard_alpha,
):
    """
    Test Phase 2 is skipped when priority_liq_assets list is empty.
    Tests line 258: if len(_priorityLiqAssetVaults) != 0
    """
    # Setup user with debt and collateral
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Configure EMPTY priority list
    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[],  # EMPTY - Phase 2 should be skipped
    )

    # Deleverage (will fall through to Phase 3)
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Phase 2 skipped - but Phase 3 should still handle it
    assert repaid_amount > 0, "Should still deleverage via Phase 3"


def test_target_repay_amount(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    credit_engine,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    setupDeleverage,
    setup_priority_configs,
    _test,
    switchboard_alpha,
):
    """
    Test Phase 2 respects target repay amount parameter.
    """
    # Setup user with plenty of collateral
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Configure Phase 2
    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[
            (simple_erc20_vault, alpha_token),
        ]
    )

    # Pre-state
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    pre_user_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)

    # Set target to partial repay
    target_repay = 200 * EIGHTEEN_DECIMALS

    # Deleverage with target
    repaid_amount = teller.deleverageUser(bob, target_repay, sender=switchboard_alpha.address)

    # Get events
    transfer_log = filter_logs(teller, "EndaomentTransferDuringDeleverage")[0]
    deleverage_log = filter_logs(teller, "DeleverageUser")[0]

    # Verify only target amount repaid
    assert repaid_amount <= target_repay
    _test(repaid_amount, target_repay)

    # Verify partial transfer
    post_user_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    transferred = pre_user_balance - post_user_balance

    assert post_user_balance > 0, "Should have collateral remaining"
    _test(transferred, target_repay)

    # Verify debt partially reduced
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    assert post_debt > 0, "Debt should remain"
    assert post_debt == pre_debt - target_repay

    # Verify events
    assert transfer_log.isDepleted == False
    assert deleverage_log.targetRepayAmount == target_repay


def test_vault_balance_changes(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    endaoment_funds,
    setupDeleverage,
    setup_priority_configs,
    _test,
    switchboard_alpha,
):
    """
    Test that vault balances change correctly:
    - User balance decreases
    - Endaoment balance increases
    """
    # Setup
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=400 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[
            (simple_erc20_vault, alpha_token),
        ]
    )

    # Pre-state
    pre_user_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    pre_endaoment_token_balance = alpha_token.balanceOf(endaoment_funds)

    # Deleverage
    teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Post-state
    post_user_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    post_endaoment_token_balance = alpha_token.balanceOf(endaoment_funds)

    # Calculate changes
    user_decrease = pre_user_vault_balance - post_user_vault_balance
    endaoment_increase = post_endaoment_token_balance - pre_endaoment_token_balance

    # Verify balance changes match
    assert user_decrease > 0, "User balance should decrease"
    assert endaoment_increase > 0, "Endaoment balance should increase"
    _test(user_decrease, endaoment_increase)


def test_balance_changes_multiple_assets_all_depleted(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    endaoment_funds,
    setupDeleverage,
    performDeposit,
    setup_priority_configs,
    _test,
    switchboard_alpha,
):
    """
    Test balance changes when multiple assets are both used in deleverage.
    Verify exact balance accounting across vault and Endaoment for both assets.

    Setup: 200 alpha + 300 bravo = 500 total collateral, 400 debt at 80% LTV
    Alpha fully depleted (200), bravo partially used (200 of 300).
    """
    # Setup user with alpha_token (200 allows 160 borrow at 80% LTV)
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=200 * EIGHTEEN_DECIMALS,
        borrow_amount=160 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Add bravo_token and borrow more (300 allows another 240 borrow)
    bravo_token.transfer(bob, 300 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    performDeposit(bob, 300 * EIGHTEEN_DECIMALS, bravo_token, bob, simple_erc20_vault)
    teller.borrow(240 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    # Total: 500 collateral, 400 debt
    # Alpha will be fully depleted (200), bravo partially used (200 of 300)

    # Configure Phase 2
    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[
            (simple_erc20_vault, alpha_token),
            (simple_erc20_vault, bravo_token),
        ]
    )

    # Pre-state - track all balances
    pre_alpha_vault = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    pre_bravo_vault = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    pre_alpha_endaoment = alpha_token.balanceOf(endaoment_funds)
    pre_bravo_endaoment = bravo_token.balanceOf(endaoment_funds)

    # Deleverage
    teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Post-state
    post_alpha_vault = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    post_bravo_vault = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    post_alpha_endaoment = alpha_token.balanceOf(endaoment_funds)
    post_bravo_endaoment = bravo_token.balanceOf(endaoment_funds)

    # Calculate changes
    alpha_vault_decrease = pre_alpha_vault - post_alpha_vault
    bravo_vault_decrease = pre_bravo_vault - post_bravo_vault
    alpha_endaoment_increase = post_alpha_endaoment - pre_alpha_endaoment
    bravo_endaoment_increase = post_bravo_endaoment - pre_bravo_endaoment

    # Verify alpha fully depleted
    _test(alpha_vault_decrease, 200 * EIGHTEEN_DECIMALS)
    _test(alpha_endaoment_increase, 200 * EIGHTEEN_DECIMALS)
    _test(alpha_vault_decrease, alpha_endaoment_increase)
    assert post_alpha_vault == 0, "Alpha vault should be empty"

    # Verify bravo partially used (200 of 300)
    _test(bravo_vault_decrease, 200 * EIGHTEEN_DECIMALS)
    _test(bravo_endaoment_increase, 200 * EIGHTEEN_DECIMALS)
    _test(bravo_vault_decrease, bravo_endaoment_increase)
    _test(post_bravo_vault, 100 * EIGHTEEN_DECIMALS)

    # Verify total conservation: what left vault equals what entered Endaoment
    total_vault_decrease = alpha_vault_decrease + bravo_vault_decrease
    total_endaoment_increase = alpha_endaoment_increase + bravo_endaoment_increase
    _test(total_vault_decrease, total_endaoment_increase)
    _test(total_vault_decrease, 400 * EIGHTEEN_DECIMALS)


def test_balance_changes_multiple_assets_partial(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    charlie_token,
    charlie_token_whale,
    endaoment_funds,
    setupDeleverage,
    performDeposit,
    setup_priority_configs,
    _test,
    switchboard_alpha,
):
    """
    Test balance changes when assets are partially used.
    Verify exact accounting when first asset depleted, second partially used, third untouched.

    Setup: 200 alpha + 300 bravo + 400 charlie = 900 total, 320 debt
    Alpha fully depleted (200), bravo partially used (120), charlie untouched.
    """
    # Setup user with alpha_token (200 allows 160 borrow at 80% LTV)
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=200 * EIGHTEEN_DECIMALS,
        borrow_amount=160 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Add bravo_token and borrow more (300 allows 240 borrow at 80% LTV)
    bravo_token.transfer(bob, 300 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    performDeposit(bob, 300 * EIGHTEEN_DECIMALS, bravo_token, bob, simple_erc20_vault)
    teller.borrow(160 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    # Add charlie_token (6 decimals) - will not be touched
    charlie_token.transfer(bob, 400 * (10 ** 6), sender=charlie_token_whale)
    performDeposit(bob, 400 * (10 ** 6), charlie_token, bob, simple_erc20_vault)

    # Total debt now: 160 + 160 = 320
    # Will use all alpha (200) + some bravo (120), charlie untouched

    # Configure Phase 2
    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[
            (simple_erc20_vault, alpha_token),
            (simple_erc20_vault, bravo_token),
            (simple_erc20_vault, charlie_token),
        ]
    )

    # Pre-state
    pre_alpha_vault = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    pre_bravo_vault = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    pre_charlie_vault = simple_erc20_vault.getTotalAmountForUser(bob, charlie_token)
    pre_alpha_endaoment = alpha_token.balanceOf(endaoment_funds)
    pre_bravo_endaoment = bravo_token.balanceOf(endaoment_funds)
    pre_charlie_endaoment = charlie_token.balanceOf(endaoment_funds)

    # Deleverage
    teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Post-state
    post_alpha_vault = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    post_bravo_vault = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    post_charlie_vault = simple_erc20_vault.getTotalAmountForUser(bob, charlie_token)
    post_alpha_endaoment = alpha_token.balanceOf(endaoment_funds)
    post_bravo_endaoment = bravo_token.balanceOf(endaoment_funds)
    post_charlie_endaoment = charlie_token.balanceOf(endaoment_funds)

    # Calculate changes
    alpha_decrease = pre_alpha_vault - post_alpha_vault
    bravo_decrease = pre_bravo_vault - post_bravo_vault
    charlie_decrease = pre_charlie_vault - post_charlie_vault
    alpha_increase = post_alpha_endaoment - pre_alpha_endaoment
    bravo_increase = post_bravo_endaoment - pre_bravo_endaoment
    charlie_increase = post_charlie_endaoment - pre_charlie_endaoment

    # Verify alpha fully depleted (200)
    _test(alpha_decrease, 200 * EIGHTEEN_DECIMALS)
    _test(alpha_increase, 200 * EIGHTEEN_DECIMALS)
    _test(alpha_decrease, alpha_increase)
    assert post_alpha_vault == 0

    # Verify bravo partially used (120 of 300)
    _test(bravo_decrease, 120 * EIGHTEEN_DECIMALS)
    _test(bravo_increase, 120 * EIGHTEEN_DECIMALS)
    _test(bravo_decrease, bravo_increase)
    _test(post_bravo_vault, 180 * EIGHTEEN_DECIMALS)

    # Verify charlie untouched
    _test(charlie_decrease, 0)
    _test(charlie_increase, 0)
    _test(post_charlie_vault, 400 * (10 ** 6))

    # Verify total conservation
    total_decrease = alpha_decrease + bravo_decrease + charlie_decrease
    total_increase = alpha_increase + bravo_increase + charlie_increase
    _test(total_decrease, total_increase)
    _test(total_decrease, 320 * EIGHTEEN_DECIMALS)


def test_balance_changes_different_decimals(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    charlie_token,
    charlie_token_whale,
    delta_token,
    delta_token_whale,
    endaoment_funds,
    setupDeleverage,
    performDeposit,
    setup_priority_configs,
    _test,
    switchboard_alpha,
):
    """
    Test balance changes with tokens of different decimals to ensure proper accounting.

    Setup:
    - alpha (18 decimals): 100
    - charlie (6 decimals): 100
    - delta (8 decimals): 100
    Total: 300, Debt: 220

    All three assets should be used: alpha fully (100), charlie fully (100), delta partially (20).
    """
    # Setup user with alpha_token (18 decimals, 100 allows 80 borrow at 80% LTV)
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=100 * EIGHTEEN_DECIMALS,
        borrow_amount=80 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Add charlie_token (6 decimals, 100 allows 80 more borrow)
    charlie_token.transfer(bob, 100 * (10 ** 6), sender=charlie_token_whale)
    performDeposit(bob, 100 * (10 ** 6), charlie_token, bob, simple_erc20_vault)
    teller.borrow(80 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    # Add delta_token (8 decimals, 100 allows 80 more borrow)
    delta_token.transfer(bob, 100 * (10 ** 8), sender=delta_token_whale)
    performDeposit(bob, 100 * (10 ** 8), delta_token, bob, simple_erc20_vault)
    teller.borrow(60 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    # Total: 300 collateral, 220 debt
    # Will use alpha (100) + charlie (100) + delta (20)

    # Configure Phase 2
    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[
            (simple_erc20_vault, alpha_token),
            (simple_erc20_vault, charlie_token),
            (simple_erc20_vault, delta_token),
        ]
    )

    # Pre-state
    pre_alpha_vault = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    pre_charlie_vault = simple_erc20_vault.getTotalAmountForUser(bob, charlie_token)
    pre_delta_vault = simple_erc20_vault.getTotalAmountForUser(bob, delta_token)
    pre_alpha_endaoment = alpha_token.balanceOf(endaoment_funds)
    pre_charlie_endaoment = charlie_token.balanceOf(endaoment_funds)
    pre_delta_endaoment = delta_token.balanceOf(endaoment_funds)

    # Deleverage
    teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Post-state
    post_alpha_vault = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    post_charlie_vault = simple_erc20_vault.getTotalAmountForUser(bob, charlie_token)
    post_delta_vault = simple_erc20_vault.getTotalAmountForUser(bob, delta_token)
    post_alpha_endaoment = alpha_token.balanceOf(endaoment_funds)
    post_charlie_endaoment = charlie_token.balanceOf(endaoment_funds)
    post_delta_endaoment = delta_token.balanceOf(endaoment_funds)

    # Calculate changes
    alpha_decrease = pre_alpha_vault - post_alpha_vault
    charlie_decrease = pre_charlie_vault - post_charlie_vault
    delta_decrease = pre_delta_vault - post_delta_vault
    alpha_increase = post_alpha_endaoment - pre_alpha_endaoment
    charlie_increase = post_charlie_endaoment - pre_charlie_endaoment
    delta_increase = post_delta_endaoment - pre_delta_endaoment

    # Verify alpha (18 decimals) fully depleted
    _test(alpha_decrease, 100 * EIGHTEEN_DECIMALS)
    _test(alpha_increase, 100 * EIGHTEEN_DECIMALS)
    _test(alpha_decrease, alpha_increase)
    assert post_alpha_vault == 0

    # Verify charlie (6 decimals) fully depleted
    _test(charlie_decrease, 100 * (10 ** 6))
    _test(charlie_increase, 100 * (10 ** 6))
    _test(charlie_decrease, charlie_increase)
    assert post_charlie_vault == 0

    # Verify delta (8 decimals) partially used (20 of 100)
    _test(delta_decrease, 20 * (10 ** 8))
    _test(delta_increase, 20 * (10 ** 8))
    _test(delta_decrease, delta_increase)
    _test(post_delta_vault, 80 * (10 ** 8))

    # Verify each asset: vault decrease == endaoment increase (conservation per asset)
    _test(alpha_decrease, alpha_increase)
    _test(charlie_decrease, charlie_increase)
    _test(delta_decrease, delta_increase)


def test_balance_changes_with_target_amount(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    endaoment_funds,
    setupDeleverage,
    performDeposit,
    setup_priority_configs,
    _test,
    switchboard_alpha,
):
    """
    Test balance changes when using target repay amount (partial deleverage).
    Verify balances reflect partial transfer when target is less than full debt.

    Setup: 500 alpha + 500 bravo = 1000 total, 600 debt
    Target: 300 (only alpha should be touched, partially)
    """
    # Setup user with alpha_token
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=500 * EIGHTEEN_DECIMALS,
        borrow_amount=600 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Add bravo_token
    bravo_token.transfer(bob, 500 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    performDeposit(bob, 500 * EIGHTEEN_DECIMALS, bravo_token, bob, simple_erc20_vault)

    # Configure Phase 2
    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[
            (simple_erc20_vault, alpha_token),
            (simple_erc20_vault, bravo_token),
        ]
    )

    # Pre-state
    pre_alpha_vault = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    pre_bravo_vault = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    pre_alpha_endaoment = alpha_token.balanceOf(endaoment_funds)
    pre_bravo_endaoment = bravo_token.balanceOf(endaoment_funds)

    # Deleverage with target
    target_repay = 300 * EIGHTEEN_DECIMALS
    teller.deleverageUser(bob, target_repay, sender=switchboard_alpha.address)

    # Post-state
    post_alpha_vault = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    post_bravo_vault = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    post_alpha_endaoment = alpha_token.balanceOf(endaoment_funds)
    post_bravo_endaoment = bravo_token.balanceOf(endaoment_funds)

    # Calculate changes
    alpha_decrease = pre_alpha_vault - post_alpha_vault
    bravo_decrease = pre_bravo_vault - post_bravo_vault
    alpha_increase = post_alpha_endaoment - pre_alpha_endaoment
    bravo_increase = post_bravo_endaoment - pre_bravo_endaoment

    # Verify alpha partially used (300 of 500)
    _test(alpha_decrease, 300 * EIGHTEEN_DECIMALS)
    _test(alpha_increase, 300 * EIGHTEEN_DECIMALS)
    _test(alpha_decrease, alpha_increase)
    _test(post_alpha_vault, 200 * EIGHTEEN_DECIMALS)

    # Verify bravo untouched
    _test(bravo_decrease, 0)
    _test(bravo_increase, 0)
    _test(post_bravo_vault, 500 * EIGHTEEN_DECIMALS)

    # Verify total equals target
    total_decrease = alpha_decrease + bravo_decrease
    total_increase = alpha_increase + bravo_increase
    _test(total_decrease, total_increase)
    _test(total_decrease, target_repay)


def test_balance_changes_skip_empty_asset(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    simple_erc20_vault,
    bob,
    alpha_token,
    bravo_token,
    bravo_token_whale,
    charlie_token,
    charlie_token_whale,
    endaoment_funds,
    setupDeleverage,
    performDeposit,
    setup_priority_configs,
    _test,
    switchboard_alpha,
):
    """
    Test balance changes when priority asset has zero balance (should skip).
    Verify that skipped asset shows zero change while others change correctly.

    Setup: 0 alpha (priority 1, skipped) + 250 bravo + 250 charlie (6 decimals), 400 debt
    Alpha should show 0 change, bravo fully used (250), charlie fully used (150).
    """
    # Setup user with bravo_token only (NO alpha - will be priority 1 but skipped)
    setupDeleverage(
        bob,
        bravo_token,  # Using bravo, NOT alpha
        bravo_token_whale,
        deposit_amount=250 * EIGHTEEN_DECIMALS,
        borrow_amount=200 * EIGHTEEN_DECIMALS,  # 80% LTV
        get_sgreen=False,
    )

    # Add charlie_token (6 decimals) and borrow more
    charlie_token.transfer(bob, 250 * SIX_DECIMALS, sender=charlie_token_whale)
    performDeposit(bob, 250 * SIX_DECIMALS, charlie_token, bob, simple_erc20_vault)
    teller.borrow(200 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    # Total: 0 alpha + 250 bravo + 250 charlie = 500 collateral, 400 debt
    # Alpha is in priority list but has 0 balance - should skip
    # Bravo will be fully depleted (250), charlie fully depleted (150)

    # Configure Phase 2 (alpha first but will be skipped)
    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[
            (simple_erc20_vault, alpha_token),  # Priority 1 - empty, skipped
            (simple_erc20_vault, bravo_token),  # Priority 2 - will be used
            (simple_erc20_vault, charlie_token),  # Priority 3 - will be used
        ]
    )

    # Pre-state
    pre_alpha_vault = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    pre_bravo_vault = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    pre_charlie_vault = simple_erc20_vault.getTotalAmountForUser(bob, charlie_token)
    pre_alpha_endaoment = alpha_token.balanceOf(endaoment_funds)
    pre_bravo_endaoment = bravo_token.balanceOf(endaoment_funds)
    pre_charlie_endaoment = charlie_token.balanceOf(endaoment_funds)

    assert pre_alpha_vault == 0, "Alpha should be empty"

    # Deleverage
    teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Post-state
    post_alpha_vault = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    post_bravo_vault = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    post_charlie_vault = simple_erc20_vault.getTotalAmountForUser(bob, charlie_token)
    post_alpha_endaoment = alpha_token.balanceOf(endaoment_funds)
    post_bravo_endaoment = bravo_token.balanceOf(endaoment_funds)
    post_charlie_endaoment = charlie_token.balanceOf(endaoment_funds)

    # Calculate changes
    alpha_decrease = pre_alpha_vault - post_alpha_vault
    bravo_decrease = pre_bravo_vault - post_bravo_vault
    charlie_decrease = pre_charlie_vault - post_charlie_vault
    alpha_increase = post_alpha_endaoment - pre_alpha_endaoment
    bravo_increase = post_bravo_endaoment - pre_bravo_endaoment
    charlie_increase = post_charlie_endaoment - pre_charlie_endaoment

    # Verify alpha skipped (zero change)
    _test(alpha_decrease, 0)
    _test(alpha_increase, 0)
    assert post_alpha_vault == 0

    # Verify bravo fully depleted (250)
    _test(bravo_decrease, 250 * EIGHTEEN_DECIMALS)
    _test(bravo_increase, 250 * EIGHTEEN_DECIMALS)
    _test(bravo_decrease, bravo_increase)
    assert post_bravo_vault == 0

    # Verify charlie partially used (150 of 250)
    _test(charlie_decrease, 150 * SIX_DECIMALS)
    _test(charlie_increase, 150 * SIX_DECIMALS)
    _test(charlie_decrease, charlie_increase)
    _test(post_charlie_vault, 100 * SIX_DECIMALS)

    # Verify conservation per asset (can't sum different decimals directly)
    # Alpha: vault decrease == endaoment increase
    _test(alpha_decrease, alpha_increase)
    # Bravo: vault decrease == endaoment increase
    _test(bravo_decrease, bravo_increase)
    # Charlie: vault decrease == endaoment increase
    _test(charlie_decrease, charlie_increase)


def test_four_assets_priority(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    credit_engine,
    simple_erc20_vault,
    bob,
    alpha_token_whale,
    bravo_token_whale,
    bravo_token,
    alpha_token,
    charlie_token_whale,
    delta_token,
    delta_token_whale,
    charlie_token,
    setupDeleverage,
    performDeposit,
    setup_priority_configs,
    _test,
    switchboard_alpha,
):
    """
    Test Phase 2 with full priority list (4 assets: alpha, bravo, charlie, delta).
    Each asset should be processed in order until debt is satisfied.

    Setup: 200 each of alpha/bravo/charlie/delta = 800 collateral, ~640 debt
    First 3 depleted, 4th untouched.
    """
    # Setup user with alpha_token collateral (200 allows ~160 borrow)
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=200 * EIGHTEEN_DECIMALS,
        borrow_amount=160 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Give user charlie_token (6 decimals) and borrow more
    charlie_token.transfer(bob, 200 * (10 ** 6), sender=charlie_token_whale)
    performDeposit(bob, 200 * (10 ** 6), charlie_token, bob, simple_erc20_vault)
    teller.borrow(160 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    # Give user delta_token (8 decimals) and borrow more
    delta_token.transfer(bob, 200 * (10 ** 8), sender=delta_token_whale)
    performDeposit(bob, 200 * (10 ** 8), delta_token, bob, simple_erc20_vault)
    teller.borrow(160 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    # Give user bravo_token (18 decimals) and borrow more
    bravo_token.transfer(bob, 200 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, bravo_token, bob, simple_erc20_vault)
    teller.borrow(160 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    # Total debt: 160 * 4 = 640
    # Total collateral: 200 * 4 = 800

    # Configure Phase 2 with all 4 assets in priority order
    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[
            (simple_erc20_vault, alpha_token),      # 1st: 200 USD
            (simple_erc20_vault, bravo_token),       # 2nd: 200 USD
            (simple_erc20_vault, charlie_token),   # 3rd: 200 USD
            (simple_erc20_vault, delta_token),       # 4th: 200 USD (not needed)
        ]
    )

    # Pre-state
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount

    # Deleverage
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Get events
    transfer_logs = filter_logs(teller, "EndaomentTransferDuringDeleverage")

    # Should have 4 transfer events (all 4 assets used)
    assert len(transfer_logs) == 4, "Should have 4 transfer events"

    # Verify priority order
    assert transfer_logs[0].asset == alpha_token.address
    assert transfer_logs[0].vaultId == 3
    assert transfer_logs[0].isDepleted == True  # 200 fully used

    assert transfer_logs[1].asset == bravo_token.address
    assert transfer_logs[1].vaultId == 3
    assert transfer_logs[1].isDepleted == True  # 200 fully used

    assert transfer_logs[2].asset == charlie_token.address
    assert transfer_logs[2].vaultId == 3
    assert transfer_logs[2].isDepleted == True  # 200 fully used

    assert transfer_logs[3].asset == delta_token.address
    assert transfer_logs[3].vaultId == 3
    assert transfer_logs[3].isDepleted == False  # ~40 used, ~160 remaining

    # Verify balances
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == 0
    assert simple_erc20_vault.getTotalAmountForUser(bob, charlie_token) == 0

    # Delta partially used
    assert simple_erc20_vault.getTotalAmountForUser(bob, delta_token) > 0
    assert simple_erc20_vault.getTotalAmountForUser(bob, delta_token) < 200 * (10 ** 8)

    # Verify debt fully repaid (640 debt covered by 200+200+200+40 = 640)
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    _test(post_debt, 0)
    _test(repaid_amount, pre_debt)


def test_phase2_then_phase3_prevents_double_processing(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    simple_erc20_vault,
    rebase_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    endaoment_funds,
    performDeposit,
    setup_priority_configs,
    setAssetConfig,
    createDebtTerms,
    _test,
    switchboard_alpha,
):
    """
    CRITICAL TEST: Verify that same asset in Phase 2 priority list AND user's Phase 3 vault
    is only processed once via didHandleAsset cache mechanism.

    SCENARIO:
    - User has alpha in vault_3 (200 units) - will be in Phase 2 priority
    - User has alpha in vault_4 (300 units) - will be in Phase 3 iteration
    - User has bravo in vault_3 (100 units) - backup collateral
    - Total debt: 400 units

    PRIORITY: [(vault_3, alpha)] - only vault_3 alpha in priority

    EXPECTED:
    - Phase 2 processes vault_3 alpha (200 transferred)
    - Phase 3 SKIPS vault_4 alpha (didHandleAsset prevents double-processing)
    - Phase 3 processes vault_3 bravo (100 transferred)
    - Phase 3 processes vault_4 alpha (100 transferred) - different vault OK
    - Only 400 total transferred (not 500 if double-processed)

    VALIDATES: Lines 370-372 (didHandleAsset cache mechanism)
    """
    # Configure alpha_token to work with both vaults
    debt_terms = createDebtTerms(
        _ltv=80_00,
        _redemptionThreshold=85_00,
        _liqThreshold=90_00,
        _liqFee=5_00,
        _borrowRate=0,
    )

    # Configure alpha for both vault_3 and vault_4
    setAssetConfig(
        alpha_token,
        _vaultIds=[3, 4],  # Can be deposited in both vaults
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,
    )

    # Setup user with alpha in vault_3 (simple_erc20_vault)
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale, simple_erc20_vault)

    # Add alpha to vault_4 (rebase_erc20_vault) - same asset, different vault
    performDeposit(bob, 300 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale, rebase_erc20_vault)

    # Add bravo to vault_3 as backup collateral
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, bravo_token, bravo_token_whale, simple_erc20_vault)

    # Borrow 400 (80% of 500 alpha + 80% of 100 bravo = 480 max)
    teller.borrow(400 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    # Configure Phase 2 with ONLY vault_3 alpha in priority
    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[
            (simple_erc20_vault, alpha_token),  # Only vault_3 alpha
            # vault_4 alpha NOT in priority - will be Phase 3
        ]
    )

    # Track balances before
    pre_alpha_vault3 = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    pre_alpha_vault4 = rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    pre_bravo_vault3 = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    pre_endaoment_alpha = alpha_token.balanceOf(endaoment_funds)
    pre_endaoment_bravo = bravo_token.balanceOf(endaoment_funds)

    assert pre_alpha_vault3 == 200 * EIGHTEEN_DECIMALS
    assert pre_alpha_vault4 == 300 * EIGHTEEN_DECIMALS
    assert pre_bravo_vault3 == 100 * EIGHTEEN_DECIMALS

    # Deleverage
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Get transfer events
    transfer_logs = filter_logs(teller, "EndaomentTransferDuringDeleverage")

    # Track balances after
    post_alpha_vault3 = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    post_alpha_vault4 = rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    post_bravo_vault3 = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    post_endaoment_alpha = alpha_token.balanceOf(endaoment_funds)
    post_endaoment_bravo = bravo_token.balanceOf(endaoment_funds)

    # CRITICAL ASSERTIONS:

    # 1. Exactly 3 transfer events (not 4 if double-processed)
    assert len(transfer_logs) == 3, f"Expected 3 transfers, got {len(transfer_logs)}"

    # 2. First event: vault_3 alpha (Phase 2 priority)
    assert transfer_logs[0].vaultId == 3
    assert transfer_logs[0].asset == alpha_token.address
    assert transfer_logs[0].amountSent == 200 * EIGHTEEN_DECIMALS
    assert transfer_logs[0].isDepleted == True

    # 3. Second event: vault_3 bravo (Phase 3)
    assert transfer_logs[1].vaultId == 3
    assert transfer_logs[1].asset == bravo_token.address
    assert transfer_logs[1].amountSent == 100 * EIGHTEEN_DECIMALS
    assert transfer_logs[1].isDepleted == True

    # 4. Third event: vault_4 alpha (Phase 3 - different vault OK)
    assert transfer_logs[2].vaultId == 4
    assert transfer_logs[2].asset == alpha_token.address
    assert transfer_logs[2].amountSent == 100 * EIGHTEEN_DECIMALS
    assert transfer_logs[2].isDepleted == False  # 200 remains

    # 5. Verify NO double-processing of vault_3 alpha
    vault3_alpha_events = [e for e in transfer_logs if e.vaultId == 3 and e.asset == alpha_token.address]
    assert len(vault3_alpha_events) == 1, "vault_3 alpha should only be processed once"

    # 6. Verify correct final balances
    assert post_alpha_vault3 == 0  # Fully depleted
    assert post_alpha_vault4 == 200 * EIGHTEEN_DECIMALS  # 300 - 100 = 200
    assert post_bravo_vault3 == 0  # Fully depleted

    # 7. Verify Endaoment received correct totals
    alpha_increase = post_endaoment_alpha - pre_endaoment_alpha
    bravo_increase = post_endaoment_bravo - pre_endaoment_bravo

    _test(alpha_increase, 300 * EIGHTEEN_DECIMALS)  # 200 from vault_3 + 100 from vault_4
    _test(bravo_increase, 100 * EIGHTEEN_DECIMALS)  # 100 from vault_3

    # 8. Total transferred should be exactly 400 (not 500 if double-processed)
    total_transferred = sum(log.amountSent for log in transfer_logs)
    _test(total_transferred, 400 * EIGHTEEN_DECIMALS)


def test_phase2_with_non_dollar_asset_prices(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    charlie_token,
    charlie_token_whale,
    endaoment_funds,
    setupDeleverage,
    performDeposit,
    setup_priority_configs,
    mock_price_source,
    _test,
    switchboard_alpha,
):
    """
    CRITICAL TEST: Test Phase 2 with assets priced differently from $1.00.

    SCENARIO:
    - alpha @ $0.50 (500 tokens = $250 value)
    - bravo @ $2.00 (100 tokens = $200 value)
    - charlie @ $10.00 (20 tokens = $200 value) [6 decimals]
    - Total collateral value: $650
    - Debt: $300

    PRIORITY: [alpha, bravo, charlie]

    EXPECTED:
    - Alpha: 500 tokens transferred = $250 (fully depleted)
    - Bravo: 25 tokens transferred = $50 (partial)
    - Charlie: untouched (debt already satisfied)
    - Events show correct amountSent vs usdValue ratios
    - Debt reduced by exactly $300

    VALIDATES: Lines 498-512 (_getMaxAssetAmount price conversion logic)
    """
    # Setup user with alpha (will be 500 tokens @ $1 initially)
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=500 * EIGHTEEN_DECIMALS,
        borrow_amount=200 * EIGHTEEN_DECIMALS,  # $200 debt
        get_sgreen=False,
    )

    # Add bravo (100 tokens @ $1 initially)
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, bravo_token, bravo_token_whale, simple_erc20_vault)

    # Add charlie (20 tokens @ $1 initially) - 6 decimals
    performDeposit(bob, 20 * SIX_DECIMALS, charlie_token, charlie_token_whale, simple_erc20_vault)

    # Borrow additional $100 (total debt = $300)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    # NOW set non-dollar prices AFTER setup and borrowing
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS // 2)  # $0.50
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)   # $2.00
    mock_price_source.setPrice(charlie_token, 10 * EIGHTEEN_DECIMALS) # $10.00

    # Configure Phase 2 priority
    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[
            (simple_erc20_vault, alpha_token),   # Priority 1 @ $0.50
            (simple_erc20_vault, bravo_token),   # Priority 2 @ $2.00
            (simple_erc20_vault, charlie_token), # Priority 3 @ $10.00
        ]
    )

    # Track balances before
    pre_alpha_vault = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    pre_bravo_vault = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    pre_charlie_vault = simple_erc20_vault.getTotalAmountForUser(bob, charlie_token)
    pre_alpha_endaoment = alpha_token.balanceOf(endaoment_funds)
    pre_bravo_endaoment = bravo_token.balanceOf(endaoment_funds)
    pre_charlie_endaoment = charlie_token.balanceOf(endaoment_funds)

    # Verify starting amounts
    assert pre_alpha_vault == 500 * EIGHTEEN_DECIMALS
    assert pre_bravo_vault == 100 * EIGHTEEN_DECIMALS
    assert pre_charlie_vault == 20 * SIX_DECIMALS

    # Deleverage
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Get transfer events
    transfer_logs = filter_logs(teller, "EndaomentTransferDuringDeleverage")

    # Track balances after
    post_alpha_vault = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    post_bravo_vault = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    post_charlie_vault = simple_erc20_vault.getTotalAmountForUser(bob, charlie_token)
    post_alpha_endaoment = alpha_token.balanceOf(endaoment_funds)
    post_bravo_endaoment = bravo_token.balanceOf(endaoment_funds)
    post_charlie_endaoment = charlie_token.balanceOf(endaoment_funds)

    # CRITICAL PRICE-AWARE ASSERTIONS:

    # 1. Should have exactly 2 events (alpha fully, bravo partial, charlie untouched)
    assert len(transfer_logs) == 2, f"Expected 2 transfers, got {len(transfer_logs)}"

    # 2. First event: alpha fully depleted (500 tokens = $250)
    assert transfer_logs[0].asset == alpha_token.address
    assert transfer_logs[0].amountSent == 500 * EIGHTEEN_DECIMALS
    assert transfer_logs[0].usdValue == 250 * EIGHTEEN_DECIMALS  # $250 value
    assert transfer_logs[0].isDepleted == True

    # 3. Second event: bravo partially used (25 tokens @ $2 = $50)
    assert transfer_logs[1].asset == bravo_token.address
    assert transfer_logs[1].amountSent == 25 * EIGHTEEN_DECIMALS  # 25 tokens
    assert transfer_logs[1].usdValue == 50 * EIGHTEEN_DECIMALS    # $50 value
    assert transfer_logs[1].isDepleted == False

    # 4. Verify final balances
    assert post_alpha_vault == 0  # Fully depleted
    assert post_bravo_vault == 75 * EIGHTEEN_DECIMALS  # 100 - 25 = 75
    assert post_charlie_vault == 20 * SIX_DECIMALS  # Untouched

    # 5. Verify Endaoment received correct token amounts
    alpha_increase = post_alpha_endaoment - pre_alpha_endaoment
    bravo_increase = post_bravo_endaoment - pre_bravo_endaoment
    charlie_increase = post_charlie_endaoment - pre_charlie_endaoment

    _test(alpha_increase, 500 * EIGHTEEN_DECIMALS)  # 500 tokens
    _test(bravo_increase, 25 * EIGHTEEN_DECIMALS)   # 25 tokens
    _test(charlie_increase, 0)  # Untouched

    # 6. Total USD value repaid should be exactly $300
    total_usd_repaid = sum(log.usdValue for log in transfer_logs)
    _test(total_usd_repaid, 300 * EIGHTEEN_DECIMALS)
    _test(repaid_amount, 300 * EIGHTEEN_DECIMALS)

    # 7. Verify price ratios are correct (amountSent * price = usdValue)
    # Alpha: 500 tokens * $0.50 = $250
    _test(transfer_logs[0].amountSent // 2, transfer_logs[0].usdValue)
    # Bravo: 25 tokens * $2.00 = $50
    _test(transfer_logs[1].amountSent * 2, transfer_logs[1].usdValue)


def test_phase2_tiny_debt_amount(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    endaoment_funds,
    setupDeleverage,
    setup_priority_configs,
    credit_engine,
    _test,
    switchboard_alpha,
):
    """
    Test Phase 2 with extremely small debt amount (1 wei).

    SCENARIO:
    - User has 1000 alpha tokens
    - Debt: 1 wei (smallest possible)

    EXPECTED:
    - Transfers exactly 1 wei to Endaoment
    - No rounding errors
    - Correct event emission

    VALIDATES: Rounding behavior for tiny amounts
    """
    # Setup user with large collateral
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1000 * EIGHTEEN_DECIMALS,
        borrow_amount=1,  # 1 wei debt
        get_sgreen=False,
    )

    # Configure Phase 2
    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[(simple_erc20_vault, alpha_token)]
    )

    # Track balances
    pre_vault = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    pre_endaoment = alpha_token.balanceOf(endaoment_funds)
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount

    # Deleverage
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Get event
    transfer_logs = filter_logs(teller, "EndaomentTransferDuringDeleverage")

    # Post balances
    post_vault = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    post_endaoment = alpha_token.balanceOf(endaoment_funds)
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount

    # Assertions
    assert len(transfer_logs) == 1
    assert transfer_logs[0].amountSent == 1  # Exactly 1 wei
    assert transfer_logs[0].usdValue == 1    # $0.000...001
    assert transfer_logs[0].isDepleted == False

    # Balance changes
    _test(pre_vault - post_vault, 1)  # Vault decreased by 1 wei
    _test(post_endaoment - pre_endaoment, 1)  # Endaoment increased by 1 wei
    _test(pre_debt, 1)  # Debt was 1 wei
    _test(post_debt, 0)  # Debt now 0
    _test(repaid_amount, 1)  # Repaid 1 wei


def test_phase2_underscore_earn_vault_uses_underlying_share_conversion(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    alpha_token_vault,
    performDeposit,
    setupDeleverage,
    setup_priority_configs,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    price_desk,
    undy_vault_prices,
    governance,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
    _test,
):
    """
    Regression: underscore earn-vault deleverage should size shares from underlying
    and account usdValue from actual underlying transferred.
    """
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_undy_v2.setAllAddressesAreVaults(False)
    mock_undy_v2.setEarnVault(alpha_token_vault.address, True)
    mock_undy_v2.setBasicEarnVault(alpha_token_vault.address, True)

    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Register Undy feed for the vault token and snapshot at 1:1 pps.
    assert undy_vault_prices.isValidNewFeed(alpha_token_vault, 0, 5, 0, 3600)
    undy_vault_prices.addNewPriceFeed(alpha_token_vault, 0, 5, 0, 3600, sender=governance.address)
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    undy_vault_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)

    # Ensure this vault token is deleveragable in phase 2.
    debt_terms = createDebtTerms(
        _ltv=80_00,
        _redemptionThreshold=85_00,
        _liqThreshold=90_00,
        _liqFee=5_00,
        _borrowRate=0,
    )
    setAssetConfig(
        alpha_token_vault,
        _vaultIds=[3],
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,
    )

    # Create debt position.
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=20 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Give Bob vault shares and deposit those shares as collateral in simple_erc20_vault.
    alpha_token.transfer(bob, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    alpha_token.approve(alpha_token_vault, 100 * EIGHTEEN_DECIMALS, sender=bob)
    alpha_token_vault.deposit(100 * EIGHTEEN_DECIMALS, bob, sender=bob)
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token_vault, bob, simple_erc20_vault)

    # Simulate yield accrual so true pps is 2.0, but snapshot price remains 1.0.
    alpha_token.transfer(alpha_token_vault, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    assert alpha_token_vault.convertToAssets(EIGHTEEN_DECIMALS) == 2 * EIGHTEEN_DECIMALS
    assert price_desk.getPrice(alpha_token_vault) == 1 * EIGHTEEN_DECIMALS

    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[(simple_erc20_vault, alpha_token_vault)],
    )

    target_repay = 10 * EIGHTEEN_DECIMALS
    repaid_amount = teller.deleverageUser(bob, target_repay, sender=switchboard_alpha.address)

    transfer_logs = filter_logs(teller, "EndaomentTransferDuringDeleverage")
    vault_transfer_log = next(e for e in transfer_logs if e.asset == alpha_token_vault.address)

    expected_underlying = price_desk.getAssetAmount(alpha_token, target_repay, True)
    expected_shares = alpha_token_vault.convertToShares(expected_underlying)
    assert vault_transfer_log.amountSent == expected_shares

    underlying_sent = alpha_token_vault.convertToAssets(vault_transfer_log.amountSent)
    expected_usd_value = price_desk.getUsdValue(alpha_token, underlying_sent, True)
    assert vault_transfer_log.usdValue == expected_usd_value

    stale_token_usd_value = price_desk.getUsdValue(alpha_token_vault, vault_transfer_log.amountSent, True)
    assert stale_token_usd_value < vault_transfer_log.usdValue
    _test(repaid_amount, target_repay)

    # Restore default mock behavior for other tests.
    mock_undy_v2.setAllAddressesAreVaults(True)


def test_phase2_non_basic_underscore_vault_uses_standard_pricedesk_amount(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    alpha_token_vault,
    performDeposit,
    setupDeleverage,
    setup_priority_configs,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    price_desk,
    undy_vault_prices,
    governance,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """
    Regression: underscore fast-path should only apply to basic earn vaults.
    Non-basic underscore earn vaults use standard PriceDesk token pricing.
    """
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_undy_v2.setAllAddressesAreVaults(False)
    mock_undy_v2.setEarnVault(alpha_token_vault.address, True)
    mock_undy_v2.setBasicEarnVault(alpha_token_vault.address, False)

    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    assert undy_vault_prices.isValidNewFeed(alpha_token_vault, 0, 5, 0, 3600)
    undy_vault_prices.addNewPriceFeed(alpha_token_vault, 0, 5, 0, 3600, sender=governance.address)
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    undy_vault_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)

    debt_terms = createDebtTerms(
        _ltv=80_00,
        _redemptionThreshold=85_00,
        _liqThreshold=90_00,
        _liqFee=5_00,
        _borrowRate=0,
    )
    setAssetConfig(
        alpha_token_vault,
        _vaultIds=[3],
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,
    )

    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=20 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    alpha_token.transfer(bob, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    alpha_token.approve(alpha_token_vault, 100 * EIGHTEEN_DECIMALS, sender=bob)
    alpha_token_vault.deposit(100 * EIGHTEEN_DECIMALS, bob, sender=bob)
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token_vault, bob, simple_erc20_vault)

    # True PPS rises to 2.0 while token-level feed remains stale at 1.0.
    alpha_token.transfer(alpha_token_vault, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    assert alpha_token_vault.convertToAssets(EIGHTEEN_DECIMALS) == 2 * EIGHTEEN_DECIMALS
    assert price_desk.getPrice(alpha_token_vault) == 1 * EIGHTEEN_DECIMALS

    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[(simple_erc20_vault, alpha_token_vault)],
    )

    target_repay = 10 * EIGHTEEN_DECIMALS
    teller.deleverageUser(bob, target_repay, sender=switchboard_alpha.address)

    transfer_logs = filter_logs(teller, "EndaomentTransferDuringDeleverage")
    vault_transfer_log = next(e for e in transfer_logs if e.asset == alpha_token_vault.address)

    stale_token_shares = price_desk.getAssetAmount(alpha_token_vault, target_repay, True)
    underlying_amount = price_desk.getAssetAmount(alpha_token, target_repay, True)
    underlying_based_shares = alpha_token_vault.convertToShares(underlying_amount)

    assert vault_transfer_log.amountSent == stale_token_shares
    assert stale_token_shares > underlying_based_shares

    mock_undy_v2.setBasicEarnVault(alpha_token_vault.address, True)
    mock_undy_v2.setAllAddressesAreVaults(True)


def test_phase2_underscore_earn_vault_credit_uses_convertToAssets_when_spread_is_within_bound(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    alpha_token_vault_with_safe_gap,
    performDeposit,
    setupDeleverage,
    setup_priority_configs,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    price_desk,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """
    Regression: underscore earn-vault debt credit intentionally uses convertToAssets
    (max) rather than convertToAssetsSafe when safe/max spread is within guard bound.
    """
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_undy_v2.setAllAddressesAreVaults(False)
    mock_undy_v2.setEarnVault(alpha_token_vault_with_safe_gap.address, True)
    mock_undy_v2.setBasicEarnVault(alpha_token_vault_with_safe_gap.address, True)

    # Keep safe/max spread below Deleverage MAX_UNDERSCORE_SAFE_SPREAD_BPS (100 bps).
    alpha_token_vault_with_safe_gap.setSafeDiscountBps(25)

    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    debt_terms = createDebtTerms(
        _ltv=80_00,
        _redemptionThreshold=85_00,
        _liqThreshold=90_00,
        _liqFee=5_00,
        _borrowRate=0,
    )
    setAssetConfig(
        alpha_token_vault_with_safe_gap,
        _vaultIds=[3],
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,
    )

    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=20 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    alpha_token.transfer(bob, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    alpha_token.approve(alpha_token_vault_with_safe_gap, 100 * EIGHTEEN_DECIMALS, sender=bob)
    alpha_token_vault_with_safe_gap.deposit(100 * EIGHTEEN_DECIMALS, bob, sender=bob)
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token_vault_with_safe_gap, bob, simple_erc20_vault)

    # Increase PPS so the safe discount creates a measurable gap.
    alpha_token.transfer(alpha_token_vault_with_safe_gap, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)

    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[(simple_erc20_vault, alpha_token_vault_with_safe_gap)],
    )

    target_repay = 10 * EIGHTEEN_DECIMALS
    teller.deleverageUser(bob, target_repay, sender=switchboard_alpha.address)

    transfer_logs = filter_logs(teller, "EndaomentTransferDuringDeleverage")
    vault_transfer_log = next(e for e in transfer_logs if e.asset == alpha_token_vault_with_safe_gap.address)

    underlying_amount_max = alpha_token_vault_with_safe_gap.convertToAssets(vault_transfer_log.amountSent)
    underlying_amount_safe = alpha_token_vault_with_safe_gap.convertToAssetsSafe(vault_transfer_log.amountSent)

    expected_usd_max = price_desk.getUsdValue(alpha_token, underlying_amount_max, True)
    expected_usd_safe = price_desk.getUsdValue(alpha_token, underlying_amount_safe, True)

    assert vault_transfer_log.usdValue == expected_usd_max
    assert vault_transfer_log.usdValue > expected_usd_safe

    alpha_token_vault_with_safe_gap.setSafeDiscountBps(500)
    # Restore default mock behavior for other tests.
    mock_undy_v2.setAllAddressesAreVaults(True)


def test_phase2_underscore_earn_vault_clamps_credit_and_sizing_when_safe_spread_too_wide(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    alpha_token_vault_with_safe_gap,
    performDeposit,
    setupDeleverage,
    setup_priority_configs,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    price_desk,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """
    Regression: when safe/max spread exceeds threshold, underscore path should clamp
    max conversion to (safe + allowed spread) for both sizing and crediting.
    """
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_undy_v2.setAllAddressesAreVaults(False)
    mock_undy_v2.setEarnVault(alpha_token_vault_with_safe_gap.address, True)
    mock_undy_v2.setBasicEarnVault(alpha_token_vault_with_safe_gap.address, True)

    # Exceeds Deleverage MAX_UNDERSCORE_SAFE_SPREAD_BPS (100 bps).
    alpha_token_vault_with_safe_gap.setSafeDiscountBps(500)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    debt_terms = createDebtTerms(
        _ltv=80_00,
        _redemptionThreshold=85_00,
        _liqThreshold=90_00,
        _liqFee=5_00,
        _borrowRate=0,
    )
    setAssetConfig(
        alpha_token_vault_with_safe_gap,
        _vaultIds=[3],
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,
    )

    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=20 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    alpha_token.transfer(bob, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    alpha_token.approve(alpha_token_vault_with_safe_gap, 100 * EIGHTEEN_DECIMALS, sender=bob)
    alpha_token_vault_with_safe_gap.deposit(100 * EIGHTEEN_DECIMALS, bob, sender=bob)
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token_vault_with_safe_gap, bob, simple_erc20_vault)

    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[(simple_erc20_vault, alpha_token_vault_with_safe_gap)],
    )

    target_repay = 10 * EIGHTEEN_DECIMALS
    repaid_amount = teller.deleverageUser(bob, target_repay, sender=switchboard_alpha.address)

    transfer_logs = filter_logs(teller, "EndaomentTransferDuringDeleverage")
    vault_transfer_log = next(e for e in transfer_logs if e.asset == alpha_token_vault_with_safe_gap.address)

    target_underlying = price_desk.getAssetAmount(alpha_token, target_repay, True)

    sample_shares = 10 ** alpha_token_vault_with_safe_gap.decimals()
    sample_max_underlying = alpha_token_vault_with_safe_gap.convertToAssets(sample_shares)
    sample_safe_underlying = alpha_token_vault_with_safe_gap.convertToAssetsSafe(sample_shares)
    sample_capped_underlying = sample_safe_underlying * 10100 // 10000
    adjusted_underlying = (target_underlying * sample_max_underlying + sample_capped_underlying - 1) // sample_capped_underlying

    expected_shares = alpha_token_vault_with_safe_gap.convertToShares(adjusted_underlying)
    assert vault_transfer_log.amountSent == expected_shares

    max_underlying_sent = alpha_token_vault_with_safe_gap.convertToAssets(vault_transfer_log.amountSent)
    safe_underlying_sent = alpha_token_vault_with_safe_gap.convertToAssetsSafe(vault_transfer_log.amountSent)
    capped_underlying_sent = safe_underlying_sent * 10100 // 10000
    expected_credited_underlying = min(max_underlying_sent, capped_underlying_sent)
    expected_usd = price_desk.getUsdValue(alpha_token, expected_credited_underlying, True)

    assert vault_transfer_log.usdValue == expected_usd
    assert vault_transfer_log.usdValue <= price_desk.getUsdValue(alpha_token, max_underlying_sent, True)
    assert repaid_amount == target_repay

    # Restore defaults for other tests.
    alpha_token_vault_with_safe_gap.setSafeDiscountBps(500)
    mock_undy_v2.setAllAddressesAreVaults(True)


def test_phase2_underscore_earn_vault_no_sizing_adjustment_at_99bps_gap(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    alpha_token_vault_with_safe_gap,
    performDeposit,
    setupDeleverage,
    setup_priority_configs,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    price_desk,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """
    Boundary test: with 99 bps safe discount, safe+100bps cap should not require
    extra share sizing.
    """
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_undy_v2.setAllAddressesAreVaults(False)
    mock_undy_v2.setEarnVault(alpha_token_vault_with_safe_gap.address, True)
    mock_undy_v2.setBasicEarnVault(alpha_token_vault_with_safe_gap.address, True)
    alpha_token_vault_with_safe_gap.setSafeDiscountBps(99)

    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    debt_terms = createDebtTerms(
        _ltv=80_00,
        _redemptionThreshold=85_00,
        _liqThreshold=90_00,
        _liqFee=5_00,
        _borrowRate=0,
    )
    setAssetConfig(
        alpha_token_vault_with_safe_gap,
        _vaultIds=[3],
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,
    )

    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=20 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    alpha_token.transfer(bob, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    alpha_token.approve(alpha_token_vault_with_safe_gap, 100 * EIGHTEEN_DECIMALS, sender=bob)
    alpha_token_vault_with_safe_gap.deposit(100 * EIGHTEEN_DECIMALS, bob, sender=bob)
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token_vault_with_safe_gap, bob, simple_erc20_vault)
    alpha_token.transfer(alpha_token_vault_with_safe_gap, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)

    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[(simple_erc20_vault, alpha_token_vault_with_safe_gap)],
    )

    target_repay = 10 * EIGHTEEN_DECIMALS
    teller.deleverageUser(bob, target_repay, sender=switchboard_alpha.address)

    transfer_logs = filter_logs(teller, "EndaomentTransferDuringDeleverage")
    vault_transfer_log = next(e for e in transfer_logs if e.asset == alpha_token_vault_with_safe_gap.address)

    target_underlying = price_desk.getAssetAmount(alpha_token, target_repay, True)
    expected_shares_no_adjust = alpha_token_vault_with_safe_gap.convertToShares(target_underlying)
    assert vault_transfer_log.amountSent == expected_shares_no_adjust

    alpha_token_vault_with_safe_gap.setSafeDiscountBps(500)
    mock_undy_v2.setAllAddressesAreVaults(True)


def test_phase2_underscore_earn_vault_applies_sizing_adjustment_at_100bps_gap(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    alpha_token_vault_with_safe_gap,
    performDeposit,
    setupDeleverage,
    setup_priority_configs,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    price_desk,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """
    Boundary test: at 100 bps safe discount, tiny scaling should kick in because
    safe*(1+100bps) is slightly below max.
    """
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_undy_v2.setAllAddressesAreVaults(False)
    mock_undy_v2.setEarnVault(alpha_token_vault_with_safe_gap.address, True)
    mock_undy_v2.setBasicEarnVault(alpha_token_vault_with_safe_gap.address, True)
    alpha_token_vault_with_safe_gap.setSafeDiscountBps(100)

    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    debt_terms = createDebtTerms(
        _ltv=80_00,
        _redemptionThreshold=85_00,
        _liqThreshold=90_00,
        _liqFee=5_00,
        _borrowRate=0,
    )
    setAssetConfig(
        alpha_token_vault_with_safe_gap,
        _vaultIds=[3],
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,
    )

    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=20 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    alpha_token.transfer(bob, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    alpha_token.approve(alpha_token_vault_with_safe_gap, 100 * EIGHTEEN_DECIMALS, sender=bob)
    alpha_token_vault_with_safe_gap.deposit(100 * EIGHTEEN_DECIMALS, bob, sender=bob)
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token_vault_with_safe_gap, bob, simple_erc20_vault)
    alpha_token.transfer(alpha_token_vault_with_safe_gap, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)

    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[(simple_erc20_vault, alpha_token_vault_with_safe_gap)],
    )

    target_repay = 10 * EIGHTEEN_DECIMALS
    teller.deleverageUser(bob, target_repay, sender=switchboard_alpha.address)

    transfer_logs = filter_logs(teller, "EndaomentTransferDuringDeleverage")
    vault_transfer_log = next(e for e in transfer_logs if e.asset == alpha_token_vault_with_safe_gap.address)

    target_underlying = price_desk.getAssetAmount(alpha_token, target_repay, True)
    unadjusted_shares = alpha_token_vault_with_safe_gap.convertToShares(target_underlying)

    sample_shares = 10 ** alpha_token_vault_with_safe_gap.decimals()
    sample_max_underlying = alpha_token_vault_with_safe_gap.convertToAssets(sample_shares)
    sample_safe_underlying = alpha_token_vault_with_safe_gap.convertToAssetsSafe(sample_shares)
    sample_capped_underlying = sample_safe_underlying * 10100 // 10000
    adjusted_underlying = (target_underlying * sample_max_underlying + sample_capped_underlying - 1) // sample_capped_underlying
    expected_adjusted_shares = alpha_token_vault_with_safe_gap.convertToShares(adjusted_underlying)

    assert sample_max_underlying > sample_capped_underlying
    assert expected_adjusted_shares > unadjusted_shares
    assert vault_transfer_log.amountSent == expected_adjusted_shares

    alpha_token_vault_with_safe_gap.setSafeDiscountBps(500)
    mock_undy_v2.setAllAddressesAreVaults(True)


def test_phase2_underscore_earn_vault_safe_zero_does_not_overcredit(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    alpha_token_vault_with_safe_gap,
    performDeposit,
    setupDeleverage,
    setup_priority_configs,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """
    Safety test: if convertToAssetsSafe returns 0 for nonzero shares, deleverage
    flow must not over-credit relative to requested repay.
    """
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_undy_v2.setAllAddressesAreVaults(False)
    mock_undy_v2.setEarnVault(alpha_token_vault_with_safe_gap.address, True)
    mock_undy_v2.setBasicEarnVault(alpha_token_vault_with_safe_gap.address, True)
    alpha_token_vault_with_safe_gap.setSafeDiscountBps(10000)

    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    debt_terms = createDebtTerms(
        _ltv=80_00,
        _redemptionThreshold=85_00,
        _liqThreshold=90_00,
        _liqFee=5_00,
        _borrowRate=0,
    )
    setAssetConfig(
        alpha_token_vault_with_safe_gap,
        _vaultIds=[3],
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,
    )
    # Disable fallback deleverage on raw alpha collateral so this test must route
    # through the underscore vault path.
    setAssetConfig(
        alpha_token,
        _vaultIds=[3],
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
    )

    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=20 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    alpha_token.transfer(bob, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    alpha_token.approve(alpha_token_vault_with_safe_gap, 100 * EIGHTEEN_DECIMALS, sender=bob)
    alpha_token_vault_with_safe_gap.deposit(100 * EIGHTEEN_DECIMALS, bob, sender=bob)
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token_vault_with_safe_gap, bob, simple_erc20_vault)
    alpha_token.transfer(alpha_token_vault_with_safe_gap, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    assert alpha_token_vault_with_safe_gap.convertToAssetsSafe(EIGHTEEN_DECIMALS) == 0

    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[(simple_erc20_vault, alpha_token_vault_with_safe_gap)],
    )

    target_repay = 10 * EIGHTEEN_DECIMALS
    repaid_amount = teller.deleverageUser(bob, target_repay, sender=switchboard_alpha.address)
    transfer_logs = filter_logs(teller, "EndaomentTransferDuringDeleverage")
    vault_transfer_log = next(e for e in transfer_logs if e.asset == alpha_token_vault_with_safe_gap.address)
    assert vault_transfer_log.usdValue <= target_repay
    assert repaid_amount <= target_repay

    alpha_token_vault_with_safe_gap.setSafeDiscountBps(500)
    # restore alpha token deleverage behavior for following tests
    setAssetConfig(
        alpha_token,
        _vaultIds=[3],
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,
    )
    mock_undy_v2.setAllAddressesAreVaults(True)


def test_phase2_underscore_earn_vault_depleted_position_credits_from_amount_sent(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    alpha_token_vault_with_safe_gap,
    performDeposit,
    setupDeleverage,
    setup_priority_configs,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    price_desk,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """
    If requested shares exceed user balance, transfer depletes position.
    Credit must use capped conversion of actual amountSent, not requested amount.
    """
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_undy_v2.setAllAddressesAreVaults(False)
    mock_undy_v2.setEarnVault(alpha_token_vault_with_safe_gap.address, True)
    mock_undy_v2.setBasicEarnVault(alpha_token_vault_with_safe_gap.address, True)
    alpha_token_vault_with_safe_gap.setSafeDiscountBps(500)

    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    debt_terms = createDebtTerms(
        _ltv=80_00,
        _redemptionThreshold=85_00,
        _liqThreshold=90_00,
        _liqFee=5_00,
        _borrowRate=0,
    )
    setAssetConfig(
        alpha_token_vault_with_safe_gap,
        _vaultIds=[3],
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,
    )

    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=20 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Intentionally tiny share position so deleverage request depletes this asset.
    alpha_token.transfer(bob, 2 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    alpha_token.approve(alpha_token_vault_with_safe_gap, 2 * EIGHTEEN_DECIMALS, sender=bob)
    alpha_token_vault_with_safe_gap.deposit(2 * EIGHTEEN_DECIMALS, bob, sender=bob)
    performDeposit(bob, 2 * EIGHTEEN_DECIMALS, alpha_token_vault_with_safe_gap, bob, simple_erc20_vault)
    alpha_token.transfer(alpha_token_vault_with_safe_gap, 2 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)

    pre_shares = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token_vault_with_safe_gap)
    assert pre_shares != 0

    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[(simple_erc20_vault, alpha_token_vault_with_safe_gap)],
    )

    teller.deleverageUser(bob, 10 * EIGHTEEN_DECIMALS, sender=switchboard_alpha.address)

    transfer_logs = filter_logs(teller, "EndaomentTransferDuringDeleverage")
    vault_transfer_log = next(e for e in transfer_logs if e.asset == alpha_token_vault_with_safe_gap.address)

    post_shares = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token_vault_with_safe_gap)
    assert post_shares == 0
    assert vault_transfer_log.isDepleted == True

    max_underlying_sent = alpha_token_vault_with_safe_gap.convertToAssets(vault_transfer_log.amountSent)
    safe_underlying_sent = alpha_token_vault_with_safe_gap.convertToAssetsSafe(vault_transfer_log.amountSent)
    capped_underlying_sent = safe_underlying_sent * 10100 // 10000
    expected_credited_underlying = min(max_underlying_sent, capped_underlying_sent)
    expected_usd = price_desk.getUsdValue(alpha_token, expected_credited_underlying, True)
    assert vault_transfer_log.usdValue == expected_usd

    alpha_token_vault_with_safe_gap.setSafeDiscountBps(500)
    mock_undy_v2.setAllAddressesAreVaults(True)
