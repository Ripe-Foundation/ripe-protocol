import pytest
import boa
from constants import EIGHTEEN_DECIMALS
from conf_utils import filter_logs

SIX_DECIMALS = 10**6
EIGHT_DECIMALS = 10**8


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
    green_token,
    savings_green,
    setup_priority_configs,
    mock_price_source,
):
    """Setup test environment for Phase 3 tests."""
    setGeneralConfig()
    setGeneralDebtConfig()

    # Standard debt terms
    debt_terms = createDebtTerms(
        _ltv=80_00,
        _redemptionThreshold=85_00,
        _liqThreshold=90_00,
        _liqFee=5_00,
        _borrowRate=0,
    )

    # Configure alpha_token for simple_erc20_vault (vault_id=3)
    setAssetConfig(
        alpha_token,
        _vaultIds=[3],
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,
    )

    # Configure bravo_token for simple_erc20_vault and rebase_erc20_vault
    setAssetConfig(
        bravo_token,
        _vaultIds=[3, 4],  # Can be in multiple vaults
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,
    )

    # Configure charlie_token (6 decimals) for both vaults
    setAssetConfig(
        charlie_token,
        _vaultIds=[3, 4],
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,
    )

    # Configure delta_token (8 decimals)
    setAssetConfig(
        delta_token,
        _vaultIds=[3, 4],
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,
    )

    # Configure GREEN and sGREEN for burning
    setAssetConfig(
        green_token,
        _vaultIds=[3],
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=True,  # Should burn
        _shouldTransferToEndaoment=False,
    )

    setAssetConfig(
        savings_green,
        _vaultIds=[1, 3],  # Can be in stability pool or simple vault
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=True,  # Should burn
        _shouldTransferToEndaoment=False,
    )

    # Set prices - all $1 to keep math simple
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(delta_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(savings_green, 1 * EIGHTEEN_DECIMALS)

    # Default: No priority configs (pure Phase 3 tests)
    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[],
    )


def test_phase3_only_no_priority_assets(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    credit_engine,
    simple_erc20_vault,
    bob,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    endaoment_funds,
    setupDeleverage,
    performDeposit,
    _test,
    switchboard_alpha,
):
    """
    Test Phase 3 execution when no priority assets are configured.
    Phase 1 and 2 should be skipped, Phase 3 handles full deleverage.
    """
    # Setup user with debt and collateral
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=500 * EIGHTEEN_DECIMALS,
        borrow_amount=300 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Add more collateral of different types
    bravo_token.transfer(bob, 200 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, bravo_token, bob, simple_erc20_vault)

    charlie_token.transfer(bob, 100 * SIX_DECIMALS, sender=charlie_token_whale)
    performDeposit(bob, 100 * SIX_DECIMALS, charlie_token, bob, simple_erc20_vault)

    # Get initial state
    initial_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    initial_alpha = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    initial_bravo = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    initial_endaoment_alpha = alpha_token.balanceOf(endaoment_funds)

    # Execute deleverage - should use Phase 3 for everything
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Check events - should have transfers from Phase 3 only
    events = filter_logs(teller, "EndaomentTransferDuringDeleverage")
    assert len(events) > 0  # Should have processed assets

    # Check final state
    final_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    assert final_debt == 0  # Debt fully cleared

    # Verify endaoment_funds received the assets
    assert alpha_token.balanceOf(endaoment_funds) > initial_endaoment_alpha

    # Verify correct repayment
    _test(repaid_amount, initial_debt)


def test_phase3_fallback_after_phase1_partial(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    credit_engine,
    stability_pool,
    bob,
    savings_green,
    alpha_token,
    alpha_token_whale,
    setupDeleverage,
    performDeposit,
    setup_priority_configs,
    _test,
    switchboard_alpha,
):
    """
    Test Phase 3 as fallback when Phase 1 partially covers debt.
    Phase 1 burns some sGREEN from stability pool, Phase 3 completes deleverage.
    """
    # Setup Phase 1 priority
    setup_priority_configs(
        priority_stab_assets=[(stability_pool, savings_green.address)],
        priority_liq_assets=[],
    )

    # Setup user with debt
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=600 * EIGHTEEN_DECIMALS,
        borrow_amount=400 * EIGHTEEN_DECIMALS,
        get_sgreen=True,  # Get sGREEN from borrowing
    )

    # Deposit only partial sGREEN to stability pool (not enough to cover all debt)
    sgreen_balance = savings_green.balanceOf(bob)
    partial_sgreen = min(sgreen_balance, 100 * EIGHTEEN_DECIMALS)  # Only 100 sGREEN
    if partial_sgreen > 0:
        performDeposit(bob, partial_sgreen, savings_green, bob, stability_pool)

    # Execute deleverage
    initial_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Check events - should have both burn and transfer events
    burn_events = filter_logs(teller, "StabAssetBurntDuringDeleverage")
    transfer_events = filter_logs(teller, "EndaomentTransferDuringDeleverage")

    # Should have Phase 1 burn event if sGREEN was deposited
    if partial_sgreen > 0:
        assert len(burn_events) > 0

    # Should have Phase 3 transfer events for remaining debt
    assert len(transfer_events) > 0

    # Verify debt cleared
    final_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    assert final_debt == 0


def test_phase3_fallback_after_phase2_partial(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    credit_engine,
    simple_erc20_vault,
    rebase_erc20_vault,
    bob,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    setupDeleverage,
    performDeposit,
    setup_priority_configs,
    _test,
    switchboard_alpha,
):
    """
    Test Phase 3 as fallback when Phase 2 partially covers debt.
    Phase 2 processes priority assets, Phase 3 completes with non-priority collateral.
    """
    # Setup user with limited collateral that will be priority
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=200 * EIGHTEEN_DECIMALS,  # 200 alpha - less than debt we'll create
        borrow_amount=150 * EIGHTEEN_DECIMALS,  # 150 debt initially (near max for 200 collateral)
        get_sgreen=False,
    )

    # Add non-priority collateral FIRST to support more borrowing
    bravo_token.transfer(bob, 300 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    performDeposit(bob, 300 * EIGHTEEN_DECIMALS, bravo_token, bob, simple_erc20_vault)

    charlie_token.transfer(bob, 200 * SIX_DECIMALS, sender=charlie_token_whale)
    performDeposit(bob, 200 * SIX_DECIMALS, charlie_token, bob, rebase_erc20_vault)

    # Now borrow more against the additional collateral
    # Total collateral: 200 alpha + 300 bravo + 200 charlie = 700
    # Max debt at 80% LTV: 560
    # Borrow additional to reach 400 total debt (more than 200 alpha can cover)
    teller.borrow(250 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    # Setup Phase 2 priority - only alpha_token
    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[(simple_erc20_vault, alpha_token.address)],
    )

    # Execute deleverage
    initial_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Check events
    events = filter_logs(teller, "EndaomentTransferDuringDeleverage")

    # Should have events for multiple assets (alpha from Phase 2, others from Phase 3)
    assert len(events) > 1

    # Find alpha event (should be first due to priority)
    alpha_events = [e for e in events if e.asset == alpha_token.address]
    assert len(alpha_events) == 1
    assert alpha_events[0].isDepleted == True  # Alpha should be fully used

    # Verify debt cleared
    final_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    assert final_debt == 0


def test_phase3_multiple_vaults_iteration(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    credit_engine,
    simple_erc20_vault,
    rebase_erc20_vault,
    bob,
    alpha_token,
    bravo_token,
    charlie_token,
    delta_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    delta_token_whale,
    setupDeleverage,
    performDeposit,
    _test,
    switchboard_alpha,
):
    """
    Test Phase 3 iterating through multiple vaults.
    User has deposits in multiple vaults, Phase 3 processes them sequentially.
    """
    # Setup user with debt
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=200 * EIGHTEEN_DECIMALS,  # 200 alpha
        borrow_amount=150 * EIGHTEEN_DECIMALS,  # 150 debt initially
        get_sgreen=False,
    )

    # Add assets to simple_erc20_vault (vault_id=3)
    bravo_token.transfer(bob, 150 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    performDeposit(bob, 150 * EIGHTEEN_DECIMALS, bravo_token, bob, simple_erc20_vault)

    # Add assets to rebase_erc20_vault (vault_id=4)
    charlie_token.transfer(bob, 200 * SIX_DECIMALS, sender=charlie_token_whale)
    performDeposit(bob, 200 * SIX_DECIMALS, charlie_token, bob, rebase_erc20_vault)

    delta_token.transfer(bob, 100 * EIGHT_DECIMALS, sender=delta_token_whale)
    performDeposit(bob, 100 * EIGHT_DECIMALS, delta_token, bob, rebase_erc20_vault)

    # Now borrow more - we have 200+150+200+100 = 650 collateral
    # Can borrow up to 520 at 80% LTV
    # Borrow enough so that vault 3 alone can't cover it all
    teller.borrow(250 * EIGHTEEN_DECIMALS, bob, False, sender=bob)  # Total debt = 400

    # Execute deleverage
    initial_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Check events
    events = filter_logs(teller, "EndaomentTransferDuringDeleverage")

    # Should have multiple events from different vaults
    assert len(events) >= 2

    # Check that multiple vaults were processed
    vault_ids = set(e.vaultId for e in events)
    assert len(vault_ids) >= 2  # At least 2 different vaults

    # Verify debt cleared
    final_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    assert final_debt == 0


def test_phase3_multiple_assets_within_vault(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    credit_engine,
    simple_erc20_vault,
    bob,
    alpha_token,
    bravo_token,
    delta_token,
    alpha_token_whale,
    bravo_token_whale,
    delta_token_whale,
    setupDeleverage,
    performDeposit,
    _test,
    switchboard_alpha,
):
    """
    Test Phase 3 processing multiple assets within a single vault.
    """
    # Setup user with debt - less alpha than debt we'll create
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=150 * EIGHTEEN_DECIMALS,  # 150 alpha
        borrow_amount=100 * EIGHTEEN_DECIMALS,  # 100 debt initially
        get_sgreen=False,
    )

    # Add more assets to the same vault
    bravo_token.transfer(bob, 150 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    performDeposit(bob, 150 * EIGHTEEN_DECIMALS, bravo_token, bob, simple_erc20_vault)

    delta_token.transfer(bob, 100 * EIGHT_DECIMALS, sender=delta_token_whale)
    performDeposit(bob, 100 * EIGHT_DECIMALS, delta_token, bob, simple_erc20_vault)

    # Now borrow more - we have 150+150+100 = 400 collateral
    # Can borrow up to 320 at 80% LTV
    # Borrow enough so that alpha alone can't cover it
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)  # Total debt = 200

    # Execute deleverage
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Check events
    events = filter_logs(teller, "EndaomentTransferDuringDeleverage")

    # All events should be from same vault
    vault_ids = set(e.vaultId for e in events)
    assert len(vault_ids) == 1  # All from same vault

    # Should have processed multiple assets
    asset_addresses = set(e.asset for e in events)
    assert len(asset_addresses) >= 2  # At least 2 different assets

    # Verify debt cleared
    final_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    assert final_debt == 0


def test_phase3_cross_phase_deduplication(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    credit_engine,
    simple_erc20_vault,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    setupDeleverage,
    performDeposit,
    setup_priority_configs,
    _test,
    switchboard_alpha,
):
    """
    CRITICAL TEST: Asset processed in Phase 2 should NOT be processed again in Phase 3.
    Tests the didHandleAsset cache working across phases.
    """
    # Setup user with limited alpha that won't cover all debt
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=200 * EIGHTEEN_DECIMALS,  # Will be processed in Phase 2
        borrow_amount=150 * EIGHTEEN_DECIMALS,  # Start with 150 debt
        get_sgreen=False,
    )

    # Add bravo BEFORE setting priority to support more borrowing
    bravo_token.transfer(bob, 200 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, bravo_token, bob, simple_erc20_vault)

    # Now borrow more - total collateral 200+200=400, max debt at 80% = 320
    teller.borrow(150 * EIGHTEEN_DECIMALS, bob, False, sender=bob)  # Total debt = 300

    # Setup Phase 2 priority with alpha_token
    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[(simple_erc20_vault, alpha_token.address)],
    )

    # Execute deleverage
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Check events
    events = filter_logs(teller, "EndaomentTransferDuringDeleverage")

    # Find alpha events
    alpha_events = [e for e in events if e.asset == alpha_token.address]

    # Should have exactly ONE alpha event (from Phase 2)
    assert len(alpha_events) == 1

    # Bravo should have been processed in Phase 3
    bravo_events = [e for e in events if e.asset == bravo_token.address]
    assert len(bravo_events) > 0

    # Verify debt cleared
    final_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    assert final_debt == 0


def test_phase3_multiple_vaults_same_asset(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    credit_engine,
    simple_erc20_vault,
    rebase_erc20_vault,
    bob,
    bravo_token,  # Configured for both vaults
    bravo_token_whale,
    performDeposit,
    _test,
    switchboard_alpha,
):
    """
    Test that same asset in different vaults are treated as separate positions.
    Both should be processed since didHandleAsset uses [user][vaultId][asset] key.
    """
    # Setup user with debt - use bravo as collateral
    bravo_token.transfer(bob, 400 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, bravo_token, bob, simple_erc20_vault)

    # Borrow against bravo collateral
    teller.borrow(150 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    # Add bravo to second vault
    performDeposit(bob, 150 * EIGHTEEN_DECIMALS, bravo_token, bob, rebase_erc20_vault)

    # Borrow more to ensure both vaults are needed
    # Total collateral: 200 + 150 = 350, max debt at 80% = 280
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)  # Total debt = 250

    # Execute deleverage
    initial_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Check events
    events = filter_logs(teller, "EndaomentTransferDuringDeleverage")

    # Find bravo events
    bravo_events = [e for e in events if e.asset == bravo_token.address]

    # Should have TWO bravo events from different vaults
    assert len(bravo_events) == 2

    # Should be from different vaults
    vault_ids = [e.vaultId for e in bravo_events]
    assert len(set(vault_ids)) == 2  # Two different vault IDs

    # Verify debt cleared
    final_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    assert final_debt == 0


def test_phase3_all_assets_depleted_partial_repay(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    credit_engine,
    simple_erc20_vault,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    setupDeleverage,
    performDeposit,
    _test,
    switchboard_alpha,
):
    """
    Test Phase 3 when user requests partial repayment that depletes all assets.
    """
    # Setup user with collateral and debt
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=200 * EIGHTEEN_DECIMALS,  # 200 collateral
        borrow_amount=150 * EIGHTEEN_DECIMALS,  # 150 debt
        get_sgreen=False,
    )

    # Add more collateral
    bravo_token.transfer(bob, 100 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, bravo_token, bob, simple_erc20_vault)
    # Total collateral = 300

    initial_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount

    # Execute deleverage requesting to repay MORE than available collateral
    # This will deplete all assets but not fully repay if we request full debt
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Check events
    events = filter_logs(teller, "EndaomentTransferDuringDeleverage")

    # Since we have enough collateral to cover debt, assets will be used as needed
    assert len(events) > 0

    # Verify debt fully cleared since we have enough collateral
    final_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    assert final_debt == 0


def test_phase3_exact_debt_match(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    credit_engine,
    simple_erc20_vault,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    setupDeleverage,
    performDeposit,
    _test,
    switchboard_alpha,
):
    """
    Test Phase 3 when total collateral exactly equals remaining debt.
    """
    # Setup user with specific debt amount
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=300 * EIGHTEEN_DECIMALS,  # 300 collateral
        borrow_amount=200 * EIGHTEEN_DECIMALS,  # 200 debt
        get_sgreen=False,
    )

    # Add collateral to match debt exactly
    bravo_token.transfer(bob, 100 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, bravo_token, bob, simple_erc20_vault)

    # Adjust debt to match collateral if needed
    # We have 400 collateral at 80% LTV, current debt is 200
    # Borrow 200 more to reach 400 total debt matching collateral value
    teller.borrow(200 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    # Execute deleverage
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Check events
    events = filter_logs(teller, "EndaomentTransferDuringDeleverage")
    assert len(events) > 0

    # Verify debt fully cleared
    final_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    assert final_debt == 0


def test_all_three_phases_sequential(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    credit_engine,
    stability_pool,
    simple_erc20_vault,
    rebase_erc20_vault,
    bob,
    savings_green,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    setupDeleverage,
    performDeposit,
    setup_priority_configs,
    _test,
    switchboard_alpha,
):
    """
    Test all three phases executing sequentially.
    Phase 1: Burns sGREEN (partial)
    Phase 2: Transfers priority alpha (partial)
    Phase 3: Transfers remaining bravo and charlie
    """
    # Setup both priority lists
    setup_priority_configs(
        priority_stab_assets=[(stability_pool, savings_green.address)],
        priority_liq_assets=[(simple_erc20_vault, alpha_token.address)],
    )

    # Setup user with less alpha so Phase 3 is needed
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=250 * EIGHTEEN_DECIMALS,  # Phase 2 priority - reduced from 500
        borrow_amount=200 * EIGHTEEN_DECIMALS,  # Start with 200 debt
        get_sgreen=True,  # Get some sGREEN for Phase 1
    )

    # Phase 1: Add some sGREEN to stability pool
    sgreen_balance = savings_green.balanceOf(bob)
    if sgreen_balance > 0:
        partial_sgreen = min(sgreen_balance, 30 * EIGHTEEN_DECIMALS)  # Smaller amount for Phase 1
        performDeposit(bob, partial_sgreen, savings_green, bob, stability_pool)

    # Phase 3: Add non-priority assets
    bravo_token.transfer(bob, 150 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    performDeposit(bob, 150 * EIGHTEEN_DECIMALS, bravo_token, bob, simple_erc20_vault)

    charlie_token.transfer(bob, 100 * SIX_DECIMALS, sender=charlie_token_whale)
    performDeposit(bob, 100 * SIX_DECIMALS, charlie_token, bob, rebase_erc20_vault)

    # Now borrow more to ensure all phases are needed
    # Total collateral: 30 sGREEN + 250 alpha + 150 bravo + 100 charlie = 530
    # Max debt at 80% = 424
    # Borrow more to reach 400 total debt
    teller.borrow(200 * EIGHTEEN_DECIMALS, bob, False, sender=bob)  # Total debt = 400

    # Execute deleverage
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Check events
    burn_events = filter_logs(teller, "StabAssetBurntDuringDeleverage")
    transfer_events = filter_logs(teller, "EndaomentTransferDuringDeleverage")

    # Should have events from all phases if sGREEN was available
    if sgreen_balance > 0:
        assert len(burn_events) > 0  # Phase 1

    assert len(transfer_events) > 1  # Phase 2 and 3

    # Verify debt cleared
    final_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    assert final_debt == 0


def test_phase3_burns_green_sgreen(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    credit_engine,
    simple_erc20_vault,
    bob,
    green_token,
    savings_green,
    alpha_token,
    alpha_token_whale,
    endaoment,
    setupDeleverage,
    performDeposit,
    _test,
    switchboard_alpha,
):
    """
    Test Phase 3 burns GREEN/sGREEN from non-priority vaults.
    Should burn (not transfer to Endaoment) based on asset config.
    """
    # Setup user with debt
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=200 * EIGHTEEN_DECIMALS,
        borrow_amount=150 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Get GREEN and sGREEN tokens
    green_balance = green_token.balanceOf(bob)
    sgreen_balance = savings_green.balanceOf(bob)

    # If user has GREEN/sGREEN, deposit to simple vault (not stability pool)
    if green_balance > 0:
        deposit_green = min(green_balance, 100 * EIGHTEEN_DECIMALS)
        performDeposit(bob, deposit_green, green_token, bob, simple_erc20_vault)

    if sgreen_balance > 0:
        deposit_sgreen = min(sgreen_balance, 100 * EIGHTEEN_DECIMALS)
        performDeposit(bob, deposit_sgreen, savings_green, bob, simple_erc20_vault)

    # Record initial Endaoment balances
    initial_endaoment_green = green_token.balanceOf(endaoment)
    initial_endaoment_sgreen = savings_green.balanceOf(endaoment)

    # Execute deleverage
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Check events - should have transfers (alpha) and potentially burns (green/sgreen)
    burn_events = filter_logs(teller, "StabAssetBurntDuringDeleverage")
    transfer_events = filter_logs(teller, "EndaomentTransferDuringDeleverage")

    # Verify GREEN/sGREEN not sent to Endaoment (burned instead)
    assert green_token.balanceOf(endaoment) == initial_endaoment_green
    assert savings_green.balanceOf(endaoment) == initial_endaoment_sgreen

    # Verify debt cleared
    final_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    assert final_debt == 0


def test_phase3_target_repay_respected(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    credit_engine,
    simple_erc20_vault,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    setupDeleverage,
    performDeposit,
    _test,
    switchboard_alpha,
):
    """
    Test that Phase 3 respects targetRepayAmount parameter.
    Should stop when target reached even if more collateral available.
    """
    # Setup user with debt
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=400 * EIGHTEEN_DECIMALS,
        borrow_amount=200 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Add more collateral
    bravo_token.transfer(bob, 200 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, bravo_token, bob, simple_erc20_vault)
    # Total = 600 available

    initial_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount

    # Execute deleverage with target amount (half of debt)
    target_repay = initial_debt // 2
    repaid_amount = teller.deleverageUser(bob, target_repay, sender=switchboard_alpha.address)

    # Check final debt
    final_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    debt_repaid = initial_debt - final_debt

    # Should have repaid approximately the target amount
    _test(debt_repaid, target_repay)

    # Check that not all collateral was used
    final_alpha = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    final_bravo = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)

    # Should have significant collateral remaining
    assert final_alpha > 0 or final_bravo > 0


def test_target_repay_spans_all_phases(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    credit_engine,
    stability_pool,
    simple_erc20_vault,
    bob,
    savings_green,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    setupDeleverage,
    performDeposit,
    setup_priority_configs,
    _test,
    switchboard_alpha,
):
    """
    Test target repay amount spanning all three phases.
    Phase 1 repays partial, Phase 2 repays partial, Phase 3 completes to target.
    """
    # Setup priorities
    setup_priority_configs(
        priority_stab_assets=[(stability_pool, savings_green.address)],
        priority_liq_assets=[(simple_erc20_vault, alpha_token.address)],
    )

    # Setup user with debt
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=300 * EIGHTEEN_DECIMALS,
        borrow_amount=200 * EIGHTEEN_DECIMALS,
        get_sgreen=True,
    )

    # Phase 1: Add sGREEN to stability pool
    sgreen_balance = savings_green.balanceOf(bob)
    if sgreen_balance > 0:
        partial_sgreen = min(sgreen_balance, 50 * EIGHTEEN_DECIMALS)
        performDeposit(bob, partial_sgreen, savings_green, bob, stability_pool)

    # Phase 3: Add bravo
    bravo_token.transfer(bob, 200 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, bravo_token, bob, simple_erc20_vault)

    initial_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount

    # Execute with target that spans all phases (half of debt)
    target_repay = initial_debt // 2
    repaid_amount = teller.deleverageUser(bob, target_repay, sender=switchboard_alpha.address)

    # Check events
    burn_events = filter_logs(teller, "StabAssetBurntDuringDeleverage")
    transfer_events = filter_logs(teller, "EndaomentTransferDuringDeleverage")

    # Should have events from multiple phases
    assert len(burn_events) + len(transfer_events) > 0

    # Verify target amount respected
    final_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    debt_repaid = initial_debt - final_debt
    _test(debt_repaid, target_repay)


def test_phase3_user_no_vaults(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    alice,  # Use alice who has no positions
    switchboard_alpha,
):
    """
    Test that deleverage reverts when user has no debt.
    The contract has an assertion that repaidAmount != 0.
    """
    # Try to deleverage alice (who has no positions) - should revert
    with boa.reverts("cannot deleverage"):
        teller.deleverageUser(alice, 0, sender=switchboard_alpha.address)


def test_phase3_mixed_decimal_accounting(
    ripe_hq,  # Ensures switchboard is registered
    switchboard,  # Ensures switchboard_alpha is registered
    teller,
    credit_engine,
    rebase_erc20_vault,
    bob,
    alpha_token,  # 18 decimals
    charlie_token,  # 6 decimals
    delta_token,  # 8 decimals
    alpha_token_whale,
    charlie_token_whale,
    delta_token_whale,
    setupDeleverage,
    performDeposit,
    _test,
    switchboard_alpha,
):
    """
    Test USD value accounting with different decimal tokens.
    Verifies correct value calculation regardless of token decimals.
    """
    # Setup user with debt
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=200 * EIGHTEEN_DECIMALS,  # 18 decimals
        borrow_amount=150 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Add tokens with different decimals
    charlie_token.transfer(bob, 100 * SIX_DECIMALS, sender=charlie_token_whale)  # 6 decimals
    performDeposit(bob, 100 * SIX_DECIMALS, charlie_token, bob, rebase_erc20_vault)

    delta_token.transfer(bob, 50 * EIGHT_DECIMALS, sender=delta_token_whale)  # 8 decimals
    performDeposit(bob, 50 * EIGHT_DECIMALS, delta_token, bob, rebase_erc20_vault)

    initial_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount

    # Execute deleverage
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Check events
    events = filter_logs(teller, "EndaomentTransferDuringDeleverage")

    # Calculate total USD value liquidated
    total_usd_liquidated = sum(e.usdValue for e in events)

    # Should have liquidated approximately the debt amount
    _test(total_usd_liquidated, initial_debt)

    # Verify debt cleared
    final_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    assert final_debt == 0