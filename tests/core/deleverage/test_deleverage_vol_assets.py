"""
Comprehensive tests for deleverageWithVolAssets() function.

This function allows governance to deleverage users using volatile collateral assets
(assets where shouldBurnAsPayment=False AND shouldTransferToEndaoment=False).
These volatile assets (like WETH, cbBTC) are transferred to Endaoment.
"""
import pytest
import boa
from constants import EIGHTEEN_DECIMALS
from conf_utils import filter_logs

SIX_DECIMALS = 10**6
EIGHT_DECIMALS = 10**8
MAX_UINT256 = 2**256 - 1


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
    savings_green,
    green_token,
    stability_pool,
    setup_priority_configs,
    mock_price_source,
):
    """
    Configure assets for testing:
    - alpha_token: Volatile asset (WETH-like, 18 decimals)
    - bravo_token: Volatile asset (cbBTC-like, 18 decimals)
    - charlie_token: Volatile asset (6 decimals)
    - delta_token: Endaoment transfer asset (shouldTransferToEndaoment=True)
    - savings_green/green_token: Stability pool assets (shouldBurnAsPayment=True)
    """
    setGeneralConfig()
    setGeneralDebtConfig()

    # Configure alpha_token as VOLATILE collateral (WETH-like)
    # NOT deleveragable in normal flow, but IS used in deleverageWithVolAssets
    alpha_debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=60_00,
        _liqThreshold=70_00,
        _liqFee=10_00,
        _borrowRate=5_00,
    )
    setAssetConfig(
        alpha_token,
        _vaultIds=[3],  # simple_erc20_vault
        _debtTerms=alpha_debt_terms,
        _shouldBurnAsPayment=False,      # NOT burnable
        _shouldTransferToEndaoment=False, # NOT marked for endaoment in normal flow
    )

    # Configure bravo_token as VOLATILE collateral (cbBTC-like)
    bravo_debt_terms = createDebtTerms(
        _ltv=60_00,
        _redemptionThreshold=70_00,
        _liqThreshold=80_00,
        _liqFee=10_00,
        _borrowRate=3_00,
    )
    setAssetConfig(
        bravo_token,
        _vaultIds=[3],  # simple_erc20_vault
        _debtTerms=bravo_debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
    )

    # Configure charlie_token as VOLATILE (6 decimals)
    charlie_debt_terms = createDebtTerms(
        _ltv=55_00,
        _redemptionThreshold=65_00,
        _liqThreshold=75_00,
        _liqFee=8_00,
        _borrowRate=4_00,
    )
    setAssetConfig(
        charlie_token,
        _vaultIds=[3],
        _debtTerms=charlie_debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
    )

    # Configure delta_token as ENDAOMENT TRANSFER asset (stablecoin-like)
    # This should be SKIPPED by deleverageWithVolAssets
    delta_debt_terms = createDebtTerms(
        _ltv=90_00,
        _redemptionThreshold=95_00,
        _liqThreshold=98_00,
        _liqFee=3_00,
        _borrowRate=0,
    )
    setAssetConfig(
        delta_token,
        _vaultIds=[3],
        _debtTerms=delta_debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,  # Should be SKIPPED
    )

    # Configure sGREEN and GREEN for burning (stability pool)
    # These should also be SKIPPED by deleverageWithVolAssets
    stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(
        savings_green,
        _vaultIds=[1],  # Stability Pool
        _debtTerms=stab_debt_terms,
        _shouldBurnAsPayment=True,  # Should be SKIPPED
    )
    setAssetConfig(
        green_token,
        _vaultIds=[1],
        _debtTerms=stab_debt_terms,
        _shouldBurnAsPayment=True,  # Should be SKIPPED
    )

    # Set prices
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(delta_token, 1 * EIGHTEEN_DECIMALS)

    # Set empty priority configs to isolate specific asset testing
    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[],
    )


######################
# Basic Functionality
######################


def test_single_volatile_asset_deleverage(
    deleverage,
    switchboard_alpha,
    ripe_hq,
    credit_engine,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    endaoment,
    setupDeleverage,
    _test,
):
    """
    Test deleveraging with single volatile asset (alpha_token as WETH).
    Verify exact transfer to Endaoment and debt reduction.

    SCENARIO:
    - Bob deposits 1000 alpha_token (WETH), borrows 500 GREEN
    - Governance calls deleverageWithVolAssets to use 250 alpha_token worth

    EXPECTED:
    - 250 USD worth of alpha_token transferred to Endaoment
    - Debt reduced by 250 USD
    - EndaomentTransferDuringDeleverage event emitted
    - DeleverageUserWithVolatileAssets event emitted
    """
    # Setup: User deposits alpha_token and borrows
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Pre-state
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    pre_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    pre_endaoment_balance = alpha_token.balanceOf(endaoment)


    # Call deleverageWithVolAssets
    target_amount = 250 * EIGHTEEN_DECIMALS
    vault_id = 3  # simple_erc20_vault
    assets = [(vault_id, alpha_token.address, target_amount)]

    repaid_amount = deleverage.deleverageWithVolAssets(
        bob, assets, sender=switchboard_alpha.address
    )

    # Get events immediately
    transfer_log = filter_logs(deleverage, "EndaomentTransferDuringDeleverage")[0]
    vol_log = filter_logs(deleverage, "DeleverageUserWithVolatileAssets")[0]

    # Ensure NO burn events
    burn_logs = filter_logs(deleverage, "StabAssetBurntDuringDeleverage")
    assert len(burn_logs) == 0

    # Post-state
    post_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    post_endaoment_balance = alpha_token.balanceOf(endaoment)
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount

    # Calculate changes
    vault_decrease = pre_vault_balance - post_vault_balance
    endaoment_increase = post_endaoment_balance - pre_endaoment_balance
    debt_reduction = pre_debt - post_debt

    # Verify balance conservation
    _test(vault_decrease, endaoment_increase)
    _test(vault_decrease, target_amount)
    _test(repaid_amount, target_amount)
    _test(debt_reduction, repaid_amount)

    # Verify EndaomentTransferDuringDeleverage event
    assert transfer_log.user == bob
    assert transfer_log.vaultId == vault_id
    assert transfer_log.asset == alpha_token.address
    _test(transfer_log.amountSent, vault_decrease)
    _test(transfer_log.usdValue, target_amount)
    assert transfer_log.isDepleted == False

    # Verify DeleverageUserWithVolatileAssets event
    assert vol_log.user == bob
    _test(vol_log.repaidAmount, repaid_amount)
    assert vol_log.hasGoodDebtHealth == True


def test_multiple_volatile_assets_ordered(
    deleverage,
    switchboard_alpha,
    ripe_hq,
    credit_engine,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    endaoment,
    setupDeleverage,
    performDeposit,
    _test,
):
    """
    Test deleveraging with multiple volatile assets processed in specified order.
    Verify assets processed in exact order provided.

    SCENARIO:
    - Bob has alpha_token (WETH) and bravo_token (cbBTC) as collateral
    - Specify order: bravo FIRST, then alpha

    EXPECTED:
    - Assets processed in exact order specified
    - Two EndaomentTransferDuringDeleverage events in correct order
    - Total debt reduction equals sum of both assets
    """
    # Setup: User deposits alpha_token and borrows
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Add bravo_token collateral
    bravo_token.transfer(bob, 500 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    performDeposit(bob, 500 * EIGHTEEN_DECIMALS, bravo_token, bob, simple_erc20_vault)

    # Pre-state
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    pre_alpha = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    pre_bravo = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)


    # Call with SPECIFIC ORDER: bravo FIRST, then alpha
    vault_id = 3
    assets = [
        (vault_id, bravo_token.address, 150 * EIGHTEEN_DECIMALS),
        (vault_id, alpha_token.address, 200 * EIGHTEEN_DECIMALS),
    ]

    repaid_amount = deleverage.deleverageWithVolAssets(
        bob, assets, sender=switchboard_alpha.address
    )

    # Get events immediately
    transfer_logs = filter_logs(deleverage, "EndaomentTransferDuringDeleverage")

    # Should have exactly 2 transfer events
    assert len(transfer_logs) == 2

    # Verify ORDER: bravo processed FIRST
    assert transfer_logs[0].asset == bravo_token.address
    assert transfer_logs[1].asset == alpha_token.address

    # Post-state
    post_alpha = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    post_bravo = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount

    # Calculate changes
    alpha_used = pre_alpha - post_alpha
    bravo_used = pre_bravo - post_bravo
    debt_reduction = pre_debt - post_debt

    # Verify amounts
    _test(bravo_used, 150 * EIGHTEEN_DECIMALS)
    _test(alpha_used, 200 * EIGHTEEN_DECIMALS)
    _test(repaid_amount, 350 * EIGHTEEN_DECIMALS)
    _test(debt_reduction, repaid_amount)


def test_max_uint_amount(
    deleverage,
    switchboard_alpha,
    ripe_hq,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    setupDeleverage,
    _test,
):
    """
    Test using max_value(uint256) to deleverage all available volatile asset.

    SCENARIO:
    - Bob has 1000 alpha_token, 500 debt
    - Use MAX_UINT256 as target amount

    EXPECTED:
    - All debt repaid (500)
    - Only 500 worth of alpha_token used (not all 1000)
    """
    # Setup
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Pre-state
    pre_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    assert pre_vault_balance == 1_000 * EIGHTEEN_DECIMALS


    # Use MAX_UINT256
    vault_id = 3
    assets = [(vault_id, alpha_token.address, MAX_UINT256)]

    repaid_amount = deleverage.deleverageWithVolAssets(
        bob, assets, sender=switchboard_alpha.address
    )

    # Post-state
    post_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    vault_decrease = pre_vault_balance - post_vault_balance

    # Should have repaid exactly 500 (total debt), not more
    _test(repaid_amount, 500 * EIGHTEEN_DECIMALS)
    _test(vault_decrease, 500 * EIGHTEEN_DECIMALS)

    # Should still have 500 alpha_token left
    _test(post_vault_balance, 500 * EIGHTEEN_DECIMALS)


def test_partial_amount_deleverage(
    deleverage,
    switchboard_alpha,
    ripe_hq,
    credit_engine,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    setupDeleverage,
    _test,
):
    """
    Test deleveraging with target less than available balance.

    SCENARIO:
    - Bob has 1000 alpha_token, 500 debt
    - Target only 100 USD worth

    EXPECTED:
    - Exactly 100 USD worth processed
    - Debt reduced by 100
    - Most collateral remains
    """
    # Setup
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Pre-state
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    pre_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)


    # Target only 100 USD
    target_amount = 100 * EIGHTEEN_DECIMALS
    vault_id = 3
    assets = [(vault_id, alpha_token.address, target_amount)]

    repaid_amount = deleverage.deleverageWithVolAssets(
        bob, assets, sender=switchboard_alpha.address
    )

    # Post-state
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    post_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)

    # Verify exact amounts
    _test(repaid_amount, target_amount)
    _test(pre_debt - post_debt, target_amount)
    _test(pre_vault_balance - post_vault_balance, target_amount)

    # Verify most collateral remains
    _test(post_vault_balance, 900 * EIGHTEEN_DECIMALS)


def test_different_decimals(
    deleverage,
    switchboard_alpha,
    ripe_hq,
    credit_engine,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    charlie_token,
    charlie_token_whale,
    endaoment,
    setupDeleverage,
    performDeposit,
    _test,
):
    """
    Test deleveraging volatile assets with different decimals (6 vs 18).

    SCENARIO:
    - alpha_token: 18 decimals (WETH-like)
    - charlie_token: 6 decimals (WBTC-like)

    EXPECTED:
    - Both processed correctly despite different decimals
    - USD values correct for both
    """
    # Setup with alpha (18 decimals)
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Add charlie (6 decimals)
    charlie_token.transfer(bob, 300 * SIX_DECIMALS, sender=charlie_token_whale)
    performDeposit(bob, 300 * SIX_DECIMALS, charlie_token, bob, simple_erc20_vault)

    # Pre-state
    pre_endaoment_alpha = alpha_token.balanceOf(endaoment)
    pre_endaoment_charlie = charlie_token.balanceOf(endaoment)


    # Deleverage both
    vault_id = 3
    assets = [
        (vault_id, alpha_token.address, 100 * EIGHTEEN_DECIMALS),  # 100 USD worth
        (vault_id, charlie_token.address, 50 * EIGHTEEN_DECIMALS),  # 50 USD worth
    ]

    repaid_amount = deleverage.deleverageWithVolAssets(
        bob, assets, sender=switchboard_alpha.address
    )

    # Post-state
    post_endaoment_alpha = alpha_token.balanceOf(endaoment)
    post_endaoment_charlie = charlie_token.balanceOf(endaoment)

    # Verify both received correct amounts
    alpha_received = post_endaoment_alpha - pre_endaoment_alpha
    charlie_received = post_endaoment_charlie - pre_endaoment_charlie

    _test(alpha_received, 100 * EIGHTEEN_DECIMALS)  # 100 tokens (18 decimals)
    _test(charlie_received, 50 * SIX_DECIMALS)  # 50 tokens (6 decimals)
    _test(repaid_amount, 150 * EIGHTEEN_DECIMALS)  # Total 150 USD


##################
# Asset Filtering
##################


def test_skips_stability_pool_assets(
    deleverage,
    switchboard_alpha,
    ripe_hq,
    credit_engine,
    stability_pool,
    bob,
    alpha_token,
    alpha_token_whale,
    savings_green,
    setupDeleverage,
    performDeposit,
    _test,
):
    """
    Test that stability pool assets (shouldBurnAsPayment=True) are SKIPPED.

    SCENARIO:
    - Bob has both sGREEN (stability pool) and alpha_token (volatile)
    - Try to deleverage sGREEN

    EXPECTED:
    - sGREEN skipped (no burn event)
    - Function reverts with "no volatile assets processed"
    """
    # Setup: User borrows and receives sGREEN
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=True,
    )

    # Deposit all sGREEN into stability pool
    sgreen_balance = savings_green.balanceOf(bob)
    performDeposit(bob, sgreen_balance, savings_green, bob, stability_pool)


    # Try to deleverage sGREEN - should FAIL
    assets = [(1, savings_green.address, 250 * EIGHTEEN_DECIMALS)]

    with boa.reverts("no volatile assets processed"):
        deleverage.deleverageWithVolAssets(bob, assets, sender=switchboard_alpha.address)


def test_skips_endaoment_transfer_assets(
    deleverage,
    switchboard_alpha,
    ripe_hq,
    simple_erc20_vault,
    bob,
    delta_token,
    delta_token_whale,
    setupDeleverage,
    _test,
):
    """
    Test that shouldTransferToEndaoment=True assets are SKIPPED.

    SCENARIO:
    - delta_token has shouldTransferToEndaoment=True (stablecoin-like)
    - Try to deleverage it

    EXPECTED:
    - delta_token skipped
    - Function reverts with "no volatile assets processed"
    """
    # Setup with delta_token (shouldTransferToEndaoment=True)
    # Note: delta_token has 8 decimals
    setupDeleverage(
        bob,
        delta_token,
        delta_token_whale,
        deposit_amount=1_000 * EIGHT_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )


    # Try to deleverage delta_token - should FAIL
    vault_id = 3
    assets = [(vault_id, delta_token.address, 250 * EIGHTEEN_DECIMALS)]

    with boa.reverts("no volatile assets processed"):
        deleverage.deleverageWithVolAssets(bob, assets, sender=switchboard_alpha.address)


def test_mixed_assets_only_processes_volatiles(
    deleverage,
    switchboard_alpha,
    ripe_hq,
    credit_engine,
    stability_pool,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    delta_token,
    delta_token_whale,
    savings_green,
    setupDeleverage,
    performDeposit,
    _test,
):
    """
    Test that when given mix of volatile, stability pool, and endaoment assets,
    ONLY volatile assets are processed.

    SCENARIO:
    - sGREEN (shouldBurnAsPayment=True) - SKIP
    - delta_token (shouldTransferToEndaoment=True) - SKIP
    - alpha_token (both False) - PROCESS

    EXPECTED:
    - Only alpha_token processed
    - Only ONE EndaomentTransferDuringDeleverage event
    - NO StabAssetBurntDuringDeleverage events
    """
    # Setup with alpha_token
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=True,
    )

    # Add sGREEN to stability pool
    sgreen_balance = savings_green.balanceOf(bob)
    performDeposit(bob, sgreen_balance, savings_green, bob, stability_pool)

    # Add delta_token (8 decimals)
    delta_token.transfer(bob, 300 * EIGHT_DECIMALS, sender=delta_token_whale)
    performDeposit(bob, 300 * EIGHT_DECIMALS, delta_token, bob, simple_erc20_vault)

    # Pre-state
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    pre_alpha = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    pre_delta = simple_erc20_vault.getTotalAmountForUser(bob, delta_token)
    pre_sgreen = stability_pool.getTotalAmountForUser(bob, savings_green)


    # Try to deleverage all three - only alpha should work
    assets = [
        (1, savings_green.address, 100 * EIGHTEEN_DECIMALS),  # SKIP
        (3, delta_token.address, 100 * EIGHTEEN_DECIMALS),  # SKIP
        (3, alpha_token.address, 200 * EIGHTEEN_DECIMALS),  # PROCESS
    ]

    repaid_amount = deleverage.deleverageWithVolAssets(
        bob, assets, sender=switchboard_alpha.address
    )

    # Get events
    transfer_logs = filter_logs(deleverage, "EndaomentTransferDuringDeleverage")
    burn_logs = filter_logs(deleverage, "StabAssetBurntDuringDeleverage")

    # Only ONE transfer event (alpha_token)
    assert len(transfer_logs) == 1
    assert transfer_logs[0].asset == alpha_token.address

    # NO burn events
    assert len(burn_logs) == 0

    # Post-state
    post_alpha = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    post_delta = simple_erc20_vault.getTotalAmountForUser(bob, delta_token)
    post_sgreen = stability_pool.getTotalAmountForUser(bob, savings_green)
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount

    # Verify only alpha processed
    alpha_used = pre_alpha - post_alpha
    _test(alpha_used, 200 * EIGHTEEN_DECIMALS)
    _test(repaid_amount, 200 * EIGHTEEN_DECIMALS)
    _test(pre_debt - post_debt, 200 * EIGHTEEN_DECIMALS)

    # Verify delta and sgreen UNTOUCHED
    assert post_delta == pre_delta
    assert post_sgreen == pre_sgreen


def test_only_non_volatiles_fails(
    deleverage,
    switchboard_alpha,
    ripe_hq,
    stability_pool,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    delta_token,
    delta_token_whale,
    savings_green,
    setupDeleverage,
    performDeposit,
    _test,
):
    """
    Test that providing ONLY non-volatile assets fails with proper error.

    SCENARIO:
    - Only sGREEN and delta_token (both non-volatile)
    - No volatile assets

    EXPECTED:
    - Reverts with "no volatile assets processed"
    """
    # Setup with alpha_token
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=True,
    )

    # Add sGREEN and delta
    sgreen_balance = savings_green.balanceOf(bob)
    performDeposit(bob, sgreen_balance, savings_green, bob, stability_pool)

    # delta_token has 8 decimals
    delta_token.transfer(bob, 300 * EIGHT_DECIMALS, sender=delta_token_whale)
    performDeposit(bob, 300 * EIGHT_DECIMALS, delta_token, bob, simple_erc20_vault)


    # Only non-volatile assets - should FAIL
    assets = [
        (1, savings_green.address, 100 * EIGHTEEN_DECIMALS),
        (3, delta_token.address, 100 * EIGHTEEN_DECIMALS),
    ]

    with boa.reverts("no volatile assets processed"):
        deleverage.deleverageWithVolAssets(bob, assets, sender=switchboard_alpha.address)


#####################
# Event Verification
#####################


def test_emits_endaoment_transfer_event(
    deleverage,
    switchboard_alpha,
    ripe_hq,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    setupDeleverage,
    _test,
):
    """
    Test that EndaomentTransferDuringDeleverage event is emitted with correct details.

    EXPECTED:
    - Event has correct user, vaultId, asset
    - amountSent and usdValue correct
    - isDepleted flag correct
    """
    # Setup
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Pre-state
    pre_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)


    # Deleverage
    target_amount = 300 * EIGHTEEN_DECIMALS
    vault_id = 3
    assets = [(vault_id, alpha_token.address, target_amount)]

    deleverage.deleverageWithVolAssets(bob, assets, sender=switchboard_alpha.address)

    # Get event immediately
    transfer_log = filter_logs(deleverage, "EndaomentTransferDuringDeleverage")[0]

    # Post-state
    post_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    vault_decrease = pre_vault_balance - post_vault_balance

    # Verify event details
    assert transfer_log.user == bob
    assert transfer_log.vaultId == vault_id
    assert transfer_log.asset == alpha_token.address
    _test(transfer_log.amountSent, vault_decrease)
    _test(transfer_log.usdValue, target_amount)
    assert transfer_log.isDepleted == False  # Not fully depleted


def test_emits_deleverage_vol_assets_event(
    deleverage,
    switchboard_alpha,
    ripe_hq,
    bob,
    alpha_token,
    alpha_token_whale,
    setupDeleverage,
    _test,
):
    """
    Test that DeleverageUserWithVolatileAssets event is emitted with correct details.

    EXPECTED:
    - Event has correct user
    - repaidAmount correct
    - hasGoodDebtHealth flag correct
    """
    # Setup
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )


    # Deleverage
    target_amount = 250 * EIGHTEEN_DECIMALS
    vault_id = 3
    assets = [(vault_id, alpha_token.address, target_amount)]

    repaid_amount = deleverage.deleverageWithVolAssets(bob, assets, sender=switchboard_alpha.address)

    # Get event immediately
    vol_log = filter_logs(deleverage, "DeleverageUserWithVolatileAssets")[0]

    # Verify event details
    assert vol_log.user == bob
    _test(vol_log.repaidAmount, repaid_amount)
    _test(vol_log.repaidAmount, target_amount)
    assert vol_log.hasGoodDebtHealth == True


def test_no_burn_events_emitted(
    deleverage,
    switchboard_alpha,
    ripe_hq,
    bob,
    alpha_token,
    alpha_token_whale,
    setupDeleverage,
    _test,
):
    """
    Test that NO StabAssetBurntDuringDeleverage events are emitted.

    EXPECTED:
    - Zero burn events (since we're not processing stability pool assets)
    - Only EndaomentTransferDuringDeleverage events
    """
    # Setup
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )


    # Deleverage volatile
    vault_id = 3
    assets = [(vault_id, alpha_token.address, 250 * EIGHTEEN_DECIMALS)]

    deleverage.deleverageWithVolAssets(bob, assets, sender=switchboard_alpha.address)

    # Get events
    burn_logs = filter_logs(deleverage, "StabAssetBurntDuringDeleverage")
    transfer_logs = filter_logs(deleverage, "EndaomentTransferDuringDeleverage")

    # Verify NO burn events
    assert len(burn_logs) == 0

    # Verify transfer event exists
    assert len(transfer_logs) == 1


##############################
# Balance & Debt Verification
##############################


def test_vault_balance_decreases_correctly(
    deleverage,
    switchboard_alpha,
    ripe_hq,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    setupDeleverage,
    _test,
):
    """
    Test that vault balance decreases by exact amount.

    EXPECTED:
    - Vault balance reduction matches target amount
    """
    # Setup
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Pre-state
    pre_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)


    # Deleverage
    target_amount = 175 * EIGHTEEN_DECIMALS
    vault_id = 3
    assets = [(vault_id, alpha_token.address, target_amount)]

    deleverage.deleverageWithVolAssets(bob, assets, sender=switchboard_alpha.address)

    # Post-state
    post_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)

    # Verify exact decrease
    vault_decrease = pre_vault_balance - post_vault_balance
    _test(vault_decrease, target_amount)
    _test(post_vault_balance, 825 * EIGHTEEN_DECIMALS)


def test_endaoment_receives_exact_amount(
    deleverage,
    switchboard_alpha,
    ripe_hq,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    endaoment,
    setupDeleverage,
    _test,
):
    """
    Test that Endaoment receives exact amount transferred from vault.

    EXPECTED:
    - Endaoment balance increase = vault balance decrease
    """
    # Setup
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Pre-state
    pre_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    pre_endaoment_balance = alpha_token.balanceOf(endaoment)


    # Deleverage
    target_amount = 225 * EIGHTEEN_DECIMALS
    vault_id = 3
    assets = [(vault_id, alpha_token.address, target_amount)]

    deleverage.deleverageWithVolAssets(bob, assets, sender=switchboard_alpha.address)

    # Post-state
    post_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    post_endaoment_balance = alpha_token.balanceOf(endaoment)

    # Verify balance conservation
    vault_decrease = pre_vault_balance - post_vault_balance
    endaoment_increase = post_endaoment_balance - pre_endaoment_balance

    _test(vault_decrease, endaoment_increase)
    _test(endaoment_increase, target_amount)


def test_debt_reduced_by_usd_value(
    deleverage,
    switchboard_alpha,
    ripe_hq,
    credit_engine,
    bob,
    alpha_token,
    alpha_token_whale,
    setupDeleverage,
    _test,
):
    """
    Test that debt reduction matches USD value of assets transferred.

    EXPECTED:
    - Debt reduction = USD value of assets used
    """
    # Setup
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Pre-state
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount


    # Deleverage
    target_amount = 275 * EIGHTEEN_DECIMALS
    vault_id = 3
    assets = [(vault_id, alpha_token.address, target_amount)]

    repaid_amount = deleverage.deleverageWithVolAssets(bob, assets, sender=switchboard_alpha.address)

    # Post-state
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount

    # Verify debt reduction
    debt_reduction = pre_debt - post_debt
    _test(debt_reduction, repaid_amount)
    _test(debt_reduction, target_amount)


def test_multiple_assets_cumulative_debt_reduction(
    deleverage,
    switchboard_alpha,
    ripe_hq,
    credit_engine,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    setupDeleverage,
    performDeposit,
    _test,
):
    """
    Test that using multiple volatile assets results in cumulative debt reduction.

    SCENARIO:
    - Use 100 alpha + 150 bravo = 250 total

    EXPECTED:
    - Total debt reduction = 250
    """
    # Setup
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Add bravo
    bravo_token.transfer(bob, 500 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    performDeposit(bob, 500 * EIGHTEEN_DECIMALS, bravo_token, bob, simple_erc20_vault)

    # Pre-state
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount


    # Deleverage both
    vault_id = 3
    assets = [
        (vault_id, alpha_token.address, 100 * EIGHTEEN_DECIMALS),
        (vault_id, bravo_token.address, 150 * EIGHTEEN_DECIMALS),
    ]

    repaid_amount = deleverage.deleverageWithVolAssets(bob, assets, sender=switchboard_alpha.address)

    # Post-state
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount

    # Verify cumulative debt reduction
    debt_reduction = pre_debt - post_debt
    _test(repaid_amount, 250 * EIGHTEEN_DECIMALS)
    _test(debt_reduction, 250 * EIGHTEEN_DECIMALS)


############
# Edge Cases
############


def test_empty_assets_array_fails(
    deleverage,
    switchboard_alpha,
    ripe_hq,
    bob,
    alpha_token,
    alpha_token_whale,
    setupDeleverage,
):
    """
    Test that empty assets array fails with proper error.

    EXPECTED:
    - Reverts with "no volatile assets processed"
    """
    # Setup
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )


    # Empty array should fail
    assets = []

    with boa.reverts("no volatile assets processed"):
        deleverage.deleverageWithVolAssets(bob, assets, sender=switchboard_alpha.address)


def test_zero_target_amounts_skipped(
    deleverage,
    switchboard_alpha,
    ripe_hq,
    bob,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    setupDeleverage,
    performDeposit,
    simple_erc20_vault,
    _test,
):
    """
    Test that assets with zero targetRepayAmount are skipped gracefully.

    SCENARIO:
    - alpha with 0 target (skipped)
    - bravo with non-zero target (processed)

    EXPECTED:
    - Only bravo processed
    - alpha untouched
    """
    # Setup
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Add bravo
    bravo_token.transfer(bob, 500 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    performDeposit(bob, 500 * EIGHTEEN_DECIMALS, bravo_token, bob, simple_erc20_vault)

    # Pre-state
    pre_alpha = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    pre_bravo = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)


    # alpha with 0, bravo with 200
    vault_id = 3
    assets = [
        (vault_id, alpha_token.address, 0),  # Zero - skipped
        (vault_id, bravo_token.address, 200 * EIGHTEEN_DECIMALS),  # Processed
    ]

    repaid_amount = deleverage.deleverageWithVolAssets(bob, assets, sender=switchboard_alpha.address)

    # Post-state
    post_alpha = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    post_bravo = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)

    # Verify only bravo used
    assert post_alpha == pre_alpha  # Alpha unchanged
    _test(pre_bravo - post_bravo, 200 * EIGHTEEN_DECIMALS)
    _test(repaid_amount, 200 * EIGHTEEN_DECIMALS)


def test_invalid_vault_id_skipped(
    deleverage,
    switchboard_alpha,
    ripe_hq,
    bob,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    setupDeleverage,
    performDeposit,
    simple_erc20_vault,
    _test,
):
    """
    Test that invalid vault IDs are skipped, processing continues.

    SCENARIO:
    - Invalid vault 999 (skipped)
    - Valid vault 3 with bravo (processed)

    EXPECTED:
    - Invalid vault skipped
    - Valid vault processed
    """
    # Setup
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Add bravo
    bravo_token.transfer(bob, 500 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    performDeposit(bob, 500 * EIGHTEEN_DECIMALS, bravo_token, bob, simple_erc20_vault)


    # Invalid vault 999, then valid vault 3
    assets = [
        (999, alpha_token.address, 100 * EIGHTEEN_DECIMALS),  # Invalid - skipped
        (3, bravo_token.address, 150 * EIGHTEEN_DECIMALS),  # Valid - processed
    ]

    repaid_amount = deleverage.deleverageWithVolAssets(bob, assets, sender=switchboard_alpha.address)

    # Should have processed bravo despite invalid first entry
    _test(repaid_amount, 150 * EIGHTEEN_DECIMALS)


def test_asset_depletion_flag_set(
    deleverage,
    switchboard_alpha,
    ripe_hq,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    setupDeleverage,
    _test,
):
    """
    Test deleverage behavior when debt repayment requires all available collateral.

    SCENARIO:
    - Bob has 500 alpha collateral (50% LTV = 250 max debt)
    - Bob borrows 250 (at limit)
    - Deleverage repays all 250 debt

    EXPECTED:
    - 250 alpha used (all debt repaid)
    - 250 alpha remains as collateral (deleverage only takes what's needed for debt)
    - Debt reduced to 0
    """
    # Setup - alpha_token has 50% LTV, so 500 collateral = 250 max debt
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=500 * EIGHTEEN_DECIMALS,
        borrow_amount=250 * EIGHTEEN_DECIMALS,  # At 50% LTV limit
        get_sgreen=False,
    )

    # Pre-state
    pre_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    _test(pre_balance, 500 * EIGHTEEN_DECIMALS)


    # Use MAX_UINT to repay all debt
    vault_id = 3
    assets = [(vault_id, alpha_token.address, MAX_UINT256)]

    repaid_amount = deleverage.deleverageWithVolAssets(bob, assets, sender=switchboard_alpha.address)

    # Get event
    transfer_log = filter_logs(deleverage, "EndaomentTransferDuringDeleverage")[0]

    # Post-state
    post_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)

    # Verify only debt amount was used (250), not all collateral (500)
    _test(repaid_amount, 250 * EIGHTEEN_DECIMALS)
    _test(transfer_log.amountSent, 250 * EIGHTEEN_DECIMALS)
    _test(transfer_log.usdValue, 250 * EIGHTEEN_DECIMALS)

    # 250 alpha remains as collateral
    _test(post_balance, 250 * EIGHTEEN_DECIMALS)


def test_duplicate_assets_only_processed_once(
    deleverage,
    switchboard_alpha,
    ripe_hq,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    setupDeleverage,
    _test,
):
    """
    Test that duplicate assets in array are only processed once due to didHandleAsset cache.

    SCENARIO:
    - Same asset specified twice with different targets

    EXPECTED:
    - Only first entry processed
    - Second entry skipped (deduplication)
    """
    # Setup
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Pre-state
    pre_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)


    # Duplicate alpha entries
    vault_id = 3
    assets = [
        (vault_id, alpha_token.address, 100 * EIGHTEEN_DECIMALS),  # First
        (vault_id, alpha_token.address, 200 * EIGHTEEN_DECIMALS),  # Duplicate - skipped
    ]

    repaid_amount = deleverage.deleverageWithVolAssets(bob, assets, sender=switchboard_alpha.address)

    # Get events
    transfer_logs = filter_logs(deleverage, "EndaomentTransferDuringDeleverage")

    # Should have only ONE event (deduplication works)
    assert len(transfer_logs) == 1

    # Post-state
    post_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    vault_decrease = pre_vault_balance - post_vault_balance

    # Should only use 100 (first entry), not 300
    _test(vault_decrease, 100 * EIGHTEEN_DECIMALS)
    _test(repaid_amount, 100 * EIGHTEEN_DECIMALS)


#########################
# Governance Permissions
#########################


def test_governance_can_call(
    deleverage,
    switchboard_alpha,
    ripe_hq,
    bob,
    alpha_token,
    alpha_token_whale,
    setupDeleverage,
    _test,
):
    """
    Test that switchboard address can successfully call the function.

    EXPECTED:
    - Switchboard call succeeds
    - Function executes normally
    """
    # Setup
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )


    # Switchboard should be able to call
    vault_id = 3
    assets = [(vault_id, alpha_token.address, 100 * EIGHTEEN_DECIMALS)]

    repaid_amount = deleverage.deleverageWithVolAssets(
        bob, assets, sender=switchboard_alpha.address
    )

    # Should succeed
    _test(repaid_amount, 100 * EIGHTEEN_DECIMALS)


def test_non_governance_reverts(
    deleverage,
    switchboard_alpha,
    bob,
    alice,
    alpha_token,
    alpha_token_whale,
    setupDeleverage,
):
    """
    Test that non-trusted caller reverts with "no perms" error.

    EXPECTED:
    - Non-trusted (alice) cannot call
    - Reverts with "no perms"
    """
    # Setup
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Alice (not trusted) tries to call
    vault_id = 3
    assets = [(vault_id, alpha_token.address, 100 * EIGHTEEN_DECIMALS)]

    with boa.reverts("no perms"):
        deleverage.deleverageWithVolAssets(bob, assets, sender=alice)


def test_user_cannot_call_own_position(
    deleverage,
    switchboard_alpha,
    bob,
    alpha_token,
    alpha_token_whale,
    setupDeleverage,
):
    """
    Test that even the user themselves cannot call this function.
    Only trusted addresses (Ripe addresses or switchboard) can call.

    EXPECTED:
    - Bob cannot deleverage own position
    - Reverts with "no perms"
    """
    # Setup
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Bob tries to call on own position - should FAIL
    vault_id = 3
    assets = [(vault_id, alpha_token.address, 100 * EIGHTEEN_DECIMALS)]

    with boa.reverts("no perms"):
        deleverage.deleverageWithVolAssets(bob, assets, sender=bob)


################
# Debt Scenarios
################


def test_insufficient_collateral_to_cover_target(
    deleverage,
    switchboard_alpha,
    ripe_hq,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    setupDeleverage,
    _test,
):
    """
    Test that when target exceeds available collateral, all available collateral is used.

    SCENARIO:
    - Bob has 400 alpha collateral (50% LTV = 200 borrowing capacity)
    - Bob borrows 200 (at limit)
    - Target 500 (more than debt and more than collateral)

    EXPECTED:
    - Uses all debt amount (200)
    - Cannot use more than total debt
    """
    # Setup with limited collateral
    # alpha_token has 50% LTV, so 400 collateral = 200 max debt
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=400 * EIGHTEEN_DECIMALS,
        borrow_amount=200 * EIGHTEEN_DECIMALS,  # At LTV limit
        get_sgreen=False,
    )

    # Pre-state
    pre_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    _test(pre_vault_balance, 400 * EIGHTEEN_DECIMALS)


    # Target more than debt (500 > 200 debt)
    vault_id = 3
    assets = [(vault_id, alpha_token.address, 500 * EIGHTEEN_DECIMALS)]

    repaid_amount = deleverage.deleverageWithVolAssets(bob, assets, sender=switchboard_alpha.address)

    # Post-state
    post_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)

    # Should use all debt (200), not all collateral
    _test(repaid_amount, 200 * EIGHTEEN_DECIMALS)
    _test(post_vault_balance, 200 * EIGHTEEN_DECIMALS)  # 200 collateral remains


def test_target_exceeds_total_debt(
    deleverage,
    switchboard_alpha,
    ripe_hq,
    credit_engine,
    bob,
    alpha_token,
    alpha_token_whale,
    setupDeleverage,
    _test,
):
    """
    Test that when target exceeds total debt, only debt amount is repaid.

    SCENARIO:
    - Bob has 500 debt, 1000 collateral
    - Target 800 (more than debt)

    EXPECTED:
    - Only repays 500 (total debt)
    - Doesn't use more collateral than needed
    """
    # Setup
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Pre-state
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    _test(pre_debt, 500 * EIGHTEEN_DECIMALS)


    # Target more than debt
    vault_id = 3
    assets = [(vault_id, alpha_token.address, 800 * EIGHTEEN_DECIMALS)]

    repaid_amount = deleverage.deleverageWithVolAssets(bob, assets, sender=switchboard_alpha.address)

    # Post-state
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount

    # Should only repay total debt (500), not target (800)
    _test(repaid_amount, 500 * EIGHTEEN_DECIMALS)
    _test(post_debt, 0)


def test_zero_debt_returns_zero(
    deleverage,
    switchboard_alpha,
    ripe_hq,
    bob,
    alpha_token,
    alpha_token_whale,
    teller,
    performDeposit,
):
    """
    Test that user with no debt returns 0 immediately.

    SCENARIO:
    - Bob has collateral but no debt

    EXPECTED:
    - Returns 0 immediately
    - No events emitted
    - No state changes
    """
    # Deposit collateral but don't borrow
    alpha_token.transfer(bob, 1_000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    performDeposit(bob, 1_000 * EIGHTEEN_DECIMALS, alpha_token, bob)


    # Try to deleverage user with no debt
    vault_id = 3
    assets = [(vault_id, alpha_token.address, 100 * EIGHTEEN_DECIMALS)]

    repaid_amount = deleverage.deleverageWithVolAssets(bob, assets, sender=switchboard_alpha.address)

    # Should return 0
    assert repaid_amount == 0

    # No events should be emitted
    transfer_logs = filter_logs(deleverage, "EndaomentTransferDuringDeleverage")
    vol_logs = filter_logs(deleverage, "DeleverageUserWithVolatileAssets")

    assert len(transfer_logs) == 0
    assert len(vol_logs) == 0


##############################
# Asset Depletion & Health
##############################


def test_partial_depletion_isDepleted_false(
    deleverage,
    switchboard_alpha,
    ripe_hq,
    bob,
    alpha_token,
    alpha_token_whale,
    setupDeleverage,
    _test,
):
    """
    Test that when only partial balance is used, isDepleted=False.

    SCENARIO:
    - Use 300 out of 1000 alpha

    EXPECTED:
    - isDepleted = False
    """
    # Setup
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )


    # Use partial amount
    vault_id = 3
    assets = [(vault_id, alpha_token.address, 300 * EIGHTEEN_DECIMALS)]

    deleverage.deleverageWithVolAssets(bob, assets, sender=switchboard_alpha.address)

    # Get event
    transfer_log = filter_logs(deleverage, "EndaomentTransferDuringDeleverage")[0]

    # Should NOT be depleted
    assert transfer_log.isDepleted == False


def test_full_depletion_isDepleted_true(
    deleverage,
    switchboard_alpha,
    ripe_hq,
    credit_engine,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    setupDeleverage,
    _test,
):
    """
    Test deleverage when using MAX_UINT to repay all debt.

    SCENARIO:
    - Bob has 600 alpha collateral (50% LTV = 300 max debt)
    - Bob borrows 300 (at limit)
    - Deleverage with MAX_UINT target

    EXPECTED:
    - All debt (300) repaid
    - 300 alpha collateral remains (deleverage doesn't take more than needed)
    - Debt reduced to 0
    """
    # Setup - alpha_token has 50% LTV, so 600 collateral = 300 max debt
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=600 * EIGHTEEN_DECIMALS,
        borrow_amount=300 * EIGHTEEN_DECIMALS,  # At 50% LTV limit
        get_sgreen=False,
    )

    # Pre-state
    pre_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount


    # Use MAX_UINT to repay all debt
    vault_id = 3
    assets = [(vault_id, alpha_token.address, MAX_UINT256)]

    repaid_amount = deleverage.deleverageWithVolAssets(bob, assets, sender=switchboard_alpha.address)

    # Get event
    transfer_log = filter_logs(deleverage, "EndaomentTransferDuringDeleverage")[0]

    # Post-state
    post_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount

    # Verify only debt amount was used (300), not all collateral (600)
    _test(repaid_amount, 300 * EIGHTEEN_DECIMALS)
    _test(transfer_log.amountSent, 300 * EIGHTEEN_DECIMALS)
    _test(transfer_log.usdValue, 300 * EIGHTEEN_DECIMALS)

    # Verify debt fully repaid
    _test(pre_debt - post_debt, 300 * EIGHTEEN_DECIMALS)
    assert post_debt == 0

    # 300 alpha remains as collateral (half of original 600)
    _test(post_balance, 300 * EIGHTEEN_DECIMALS)


def test_hasGoodDebtHealth_flag_correct(
    deleverage,
    switchboard_alpha,
    ripe_hq,
    credit_engine,
    bob,
    alpha_token,
    alpha_token_whale,
    setupDeleverage,
    _test,
):
    """
    Test that hasGoodDebtHealth flag is correctly set based on final debt health.

    SCENARIO:
    - Partial repayment should result in hasGoodDebtHealth=True

    EXPECTED:
    - Event has hasGoodDebtHealth=True
    """
    # Setup
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )


    # Partial repayment
    vault_id = 3
    assets = [(vault_id, alpha_token.address, 200 * EIGHTEEN_DECIMALS)]

    deleverage.deleverageWithVolAssets(bob, assets, sender=switchboard_alpha.address)

    # Get event
    vol_log = filter_logs(deleverage, "DeleverageUserWithVolatileAssets")[0]

    # Should have good debt health after partial repayment
    assert vol_log.hasGoodDebtHealth == True

    # Verify debt is reduced but not zero
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    _test(post_debt, 300 * EIGHTEEN_DECIMALS)
    assert post_debt > 0
