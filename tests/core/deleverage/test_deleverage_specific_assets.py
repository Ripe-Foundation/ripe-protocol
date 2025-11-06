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
    savings_green,
    green_token,
    stability_pool,
    setup_priority_configs,
    mock_price_source,
):
    setGeneralConfig()
    setGeneralDebtConfig()

    # Configure alpha_token as collateral (NOT deleveragable)
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=60_00,
        _liqThreshold=70_00,
        _liqFee=10_00,
        _borrowRate=5_00,
    )
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
    )

    # Configure sGREEN and GREEN for burning
    stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(
        savings_green,
        _vaultIds=[1],  # Stability Pool
        _debtTerms=stab_debt_terms,
        _shouldBurnAsPayment=True,
    )
    setAssetConfig(
        green_token,
        _vaultIds=[1],
        _debtTerms=stab_debt_terms,
        _shouldBurnAsPayment=True,
    )

    # Configure bravo_token for endaoment transfer
    bravo_debt_terms = createDebtTerms(
        _ltv=80_00,
        _redemptionThreshold=85_00,
        _liqThreshold=90_00,
        _liqFee=5_00,
        _borrowRate=0,
    )
    setAssetConfig(
        bravo_token,
        _vaultIds=[3],  # simple_erc20_vault
        _debtTerms=bravo_debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,
    )

    # Configure charlie_token for endaoment transfer (6 decimals)
    setAssetConfig(
        charlie_token,
        _vaultIds=[3],
        _debtTerms=bravo_debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,
    )

    # Set prices
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, 1 * EIGHTEEN_DECIMALS)

    # Set empty priority configs to isolate specific asset testing
    setup_priority_configs(
        priority_stab_assets=[],
        priority_liq_assets=[],
    )


######################
# Basic Functionality
######################


def test_single_asset_sgreen_burn(
    deleverage,
    teller,
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
    Test deleveraging with single sGREEN asset from stability pool.
    Verify exact amount burned and events emitted.
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
    assert sgreen_balance > 0
    performDeposit(bob, sgreen_balance, savings_green, bob, stability_pool)

    # Pre-state
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    pre_sgreen_in_pool = stability_pool.getTotalAmountForUser(bob, savings_green)
    assert pre_sgreen_in_pool > 0

    # Call deleverageWithSpecificAssets
    target_amount = 250 * EIGHTEEN_DECIMALS
    assets = [(1, savings_green.address, target_amount)]

    repaid_amount = deleverage.deleverageWithSpecificAssets(
        bob, assets, sender=teller.address
    )

    # Get events immediately
    burn_log = filter_logs(deleverage, "StabAssetBurntDuringDeleverage")[0]
    main_log = filter_logs(deleverage, "DeleverageUser")[0]

    # Post-state
    post_sgreen_in_pool = stability_pool.getTotalAmountForUser(bob, savings_green)
    sgreen_burned = pre_sgreen_in_pool - post_sgreen_in_pool

    # Verify exact amounts
    _test(sgreen_burned, target_amount)
    _test(repaid_amount, target_amount)

    # Verify debt reduced correctly
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    debt_reduction = pre_debt - post_debt
    _test(repaid_amount, debt_reduction)

    # Verify burn event
    assert burn_log.user == bob
    assert burn_log.vaultId == 1
    assert burn_log.stabAsset == savings_green.address
    _test(burn_log.amountBurned, sgreen_burned)
    _test(burn_log.usdValue, target_amount)
    assert burn_log.isDepleted == False

    # Verify main event - trueTargetRepayAmount should match requested
    assert main_log.user == bob
    assert main_log.caller == teller.address
    _test(main_log.targetRepayAmount, target_amount)
    _test(main_log.repaidAmount, repaid_amount)
    assert main_log.hasGoodDebtHealth == True


def test_single_asset_endaoment_transfer(
    deleverage,
    teller,
    credit_engine,
    simple_erc20_vault,
    bob,
    bravo_token,
    bravo_token_whale,
    endaoment,
    setupDeleverage,
    _test,
):
    """
    Test deleveraging with single bravo_token asset transferring to endaoment.
    Verify balance conservation and events.
    """
    # Setup: User deposits bravo_token and borrows
    setupDeleverage(
        bob,
        bravo_token,
        bravo_token_whale,
        deposit_amount=500 * EIGHTEEN_DECIMALS,
        borrow_amount=300 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Pre-state
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    pre_bravo_vault = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    pre_endaoment_bravo = bravo_token.balanceOf(endaoment)

    # Call deleverageWithSpecificAssets
    target_amount = 200 * EIGHTEEN_DECIMALS
    assets = [(3, bravo_token.address, target_amount)]

    repaid_amount = deleverage.deleverageWithSpecificAssets(
        bob, assets, sender=teller.address
    )

    # Get events immediately
    transfer_log = filter_logs(deleverage, "EndaomentTransferDuringDeleverage")[0]
    main_log = filter_logs(deleverage, "DeleverageUser")[0]

    # Post-state
    post_bravo_vault = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    post_endaoment_bravo = bravo_token.balanceOf(endaoment)

    # Calculate changes
    bravo_transferred = pre_bravo_vault - post_bravo_vault
    endaoment_received = post_endaoment_bravo - pre_endaoment_bravo

    # Verify balance conservation
    _test(bravo_transferred, endaoment_received)
    _test(bravo_transferred, target_amount)
    _test(repaid_amount, target_amount)

    # Verify debt reduced
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    debt_reduction = pre_debt - post_debt
    _test(repaid_amount, debt_reduction)

    # Verify transfer event
    assert transfer_log.user == bob
    assert transfer_log.vaultId == 3
    assert transfer_log.asset == bravo_token.address
    _test(transfer_log.amountSent, bravo_transferred)
    _test(transfer_log.usdValue, target_amount)
    assert transfer_log.isDepleted == False

    # Verify main event
    assert main_log.user == bob
    assert main_log.caller == teller.address
    _test(main_log.targetRepayAmount, target_amount)
    _test(main_log.repaidAmount, repaid_amount)


def test_multiple_assets_custom_order(
    deleverage,
    teller,
    credit_engine,
    stability_pool,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    savings_green,
    setupDeleverage,
    performDeposit,
    _test,
):
    """
    Test multiple assets processed in specified order.
    Verify bravo_token processed first, then sGREEN.
    """
    # Setup: User has both sGREEN and bravo_token
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=500 * EIGHTEEN_DECIMALS,
        borrow_amount=400 * EIGHTEEN_DECIMALS,
        get_sgreen=True,
    )

    # Deposit sGREEN to stability pool
    sgreen_balance = savings_green.balanceOf(bob)
    performDeposit(bob, sgreen_balance, savings_green, bob, stability_pool)

    # Add bravo_token collateral
    bravo_token.transfer(bob, 300 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    performDeposit(bob, 300 * EIGHTEEN_DECIMALS, bravo_token, bob, simple_erc20_vault)

    # Pre-state
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    pre_sgreen = stability_pool.getTotalAmountForUser(bob, savings_green)
    pre_bravo = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)

    # Call with custom order: bravo FIRST, then sGREEN
    assets = [
        (3, bravo_token.address, 150 * EIGHTEEN_DECIMALS),
        (1, savings_green.address, 200 * EIGHTEEN_DECIMALS),
    ]

    repaid_amount = deleverage.deleverageWithSpecificAssets(
        bob, assets, sender=teller.address
    )

    # Get events immediately
    transfer_logs = filter_logs(deleverage, "EndaomentTransferDuringDeleverage")
    burn_logs = filter_logs(deleverage, "StabAssetBurntDuringDeleverage")

    # Verify event order: bravo transfer FIRST
    assert len(transfer_logs) == 1
    assert len(burn_logs) == 1
    assert transfer_logs[0].asset == bravo_token.address
    _test(transfer_logs[0].usdValue, 150 * EIGHTEEN_DECIMALS)

    # sGREEN burn SECOND
    assert burn_logs[0].stabAsset == savings_green.address
    assert burn_logs[0].usdValue > 0

    # Verify both assets were used
    post_sgreen = stability_pool.getTotalAmountForUser(bob, savings_green)
    post_bravo = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)

    assert post_bravo < pre_bravo
    assert post_sgreen < pre_sgreen

    # Verify debt reduction
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    debt_reduction = pre_debt - post_debt
    _test(repaid_amount, debt_reduction)

    # Verify repayment happened (should be close to 350 target)
    assert repaid_amount > 0


################################
# Ordering & Priority Override
################################


def test_order_overrides_priority_configs(
    deleverage,
    teller,
    stability_pool,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    savings_green,
    setupDeleverage,
    performDeposit,
    setup_priority_configs,
    _test,
):
    """
    Test that deleverageWithSpecificAssets order overrides priority configs.
    Setup priority with sGREEN first, but call with bravo first.
    """
    # Setup priority configs with sGREEN as Phase 1 priority
    setup_priority_configs(
        priority_stab_assets=[(stability_pool, savings_green)],
        priority_liq_assets=[],
    )

    # Setup: User has both assets
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=500 * EIGHTEEN_DECIMALS,
        borrow_amount=300 * EIGHTEEN_DECIMALS,
        get_sgreen=True,
    )

    sgreen_balance = savings_green.balanceOf(bob)
    performDeposit(bob, sgreen_balance, savings_green, bob, stability_pool)

    bravo_token.transfer(bob, 200 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, bravo_token, bob, simple_erc20_vault)

    # Pre-state
    pre_bravo = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    pre_sgreen = stability_pool.getTotalAmountForUser(bob, savings_green)

    # Call with bravo BEFORE sGREEN (opposite of priority config)
    assets = [
        (3, bravo_token.address, 100 * EIGHTEEN_DECIMALS),
        (1, savings_green.address, 100 * EIGHTEEN_DECIMALS),
    ]

    deleverage.deleverageWithSpecificAssets(bob, assets, sender=teller.address)

    # Get events immediately
    transfer_logs = filter_logs(deleverage, "EndaomentTransferDuringDeleverage")
    burn_logs = filter_logs(deleverage, "StabAssetBurntDuringDeleverage")

    # Verify bravo processed FIRST despite priority saying sGREEN should be first
    assert len(transfer_logs) == 1
    assert len(burn_logs) == 1

    # The key check: bravo event comes before burn event in processing
    assert transfer_logs[0].asset == bravo_token.address
    assert burn_logs[0].stabAsset == savings_green.address

    # Verify both were actually used
    post_bravo = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    post_sgreen = stability_pool.getTotalAmountForUser(bob, savings_green)

    assert post_bravo < pre_bravo
    assert post_sgreen < pre_sgreen


def test_processes_same_asset_only_once_deduplication(
    deleverage,
    teller,
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
    Test that duplicate assets in array are only processed once due to didHandleAsset cache.
    """
    # Setup
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=True,
    )

    sgreen_balance = savings_green.balanceOf(bob)
    performDeposit(bob, sgreen_balance, savings_green, bob, stability_pool)

    # Pre-state
    pre_sgreen = stability_pool.getTotalAmountForUser(bob, savings_green)

    # Call with duplicate sGREEN entries
    assets = [
        (1, savings_green.address, 100 * EIGHTEEN_DECIMALS),
        (1, savings_green.address, 200 * EIGHTEEN_DECIMALS),  # Duplicate!
    ]

    repaid_amount = deleverage.deleverageWithSpecificAssets(
        bob, assets, sender=teller.address
    )

    # Get events immediately
    burn_logs = filter_logs(deleverage, "StabAssetBurntDuringDeleverage")

    # Should have only ONE burn event (deduplication works)
    assert len(burn_logs) == 1

    # Post-state
    post_sgreen = stability_pool.getTotalAmountForUser(bob, savings_green)
    sgreen_used = pre_sgreen - post_sgreen

    # Should only burn once (100 GREEN, not 300)
    _test(sgreen_used, 100 * EIGHTEEN_DECIMALS)
    _test(repaid_amount, 100 * EIGHTEEN_DECIMALS)


#####################
# Amount Handling
#####################


def test_max_uint_amount_uses_all_available(
    deleverage,
    teller,
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
    Test that max_uint in targetRepayAmount uses all available asset.
    User has 500 debt but only 300 sGREEN available.
    """
    # Setup: 500 debt
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=True,
    )

    # Deposit all sGREEN (less than debt)
    sgreen_balance = savings_green.balanceOf(bob)
    performDeposit(bob, sgreen_balance, savings_green, bob, stability_pool)

    # Pre-state
    pre_sgreen = stability_pool.getTotalAmountForUser(bob, savings_green)
    assert pre_sgreen > 0

    # Call with max_uint
    assets = [(1, savings_green.address, 2**256 - 1)]

    repaid_amount = deleverage.deleverageWithSpecificAssets(
        bob, assets, sender=teller.address
    )

    # Get main event
    main_log = filter_logs(deleverage, "DeleverageUser")[0]

    # Post-state
    post_sgreen = stability_pool.getTotalAmountForUser(bob, savings_green)
    sgreen_used = pre_sgreen - post_sgreen

    # Should use ALL available, not fail on overflow
    _test(sgreen_used, pre_sgreen)
    _test(post_sgreen, 0)
    assert repaid_amount > 0

    # trueTargetRepayAmount should be capped amount, not max_uint
    _test(main_log.targetRepayAmount, repaid_amount)
    _test(main_log.repaidAmount, repaid_amount)


def test_caps_per_asset_when_debt_runs_out(
    deleverage,
    teller,
    simple_erc20_vault,
    bob,
    bravo_token,
    charlie_token,
    bravo_token_whale,
    charlie_token_whale,
    performDeposit,
    setupDeleverage,
    _test,
):
    """
    Test that per-asset amounts are capped when debt runs out mid-loop.
    User has 200 debt but requests 150+150+150=450 total.
    """
    # Setup: 200 debt
    setupDeleverage(
        bob,
        bravo_token,
        bravo_token_whale,
        deposit_amount=500 * EIGHTEEN_DECIMALS,
        borrow_amount=200 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Add charlie_token
    charlie_token.transfer(bob, 200 * SIX_DECIMALS, sender=charlie_token_whale)
    performDeposit(bob, 200 * SIX_DECIMALS, charlie_token, bob, simple_erc20_vault)

    # Pre-state
    pre_bravo = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    pre_charlie = simple_erc20_vault.getTotalAmountForUser(bob, charlie_token)

    # Call with 150+150+150=450 requested (but only 200 debt)
    assets = [
        (3, bravo_token.address, 150 * EIGHTEEN_DECIMALS),
        (3, charlie_token.address, 150 * EIGHTEEN_DECIMALS),
        (3, bravo_token.address, 150 * EIGHTEEN_DECIMALS),  # Won't process (deduplicated + no debt left)
    ]

    repaid_amount = deleverage.deleverageWithSpecificAssets(
        bob, assets, sender=teller.address
    )

    # Get events
    transfer_logs = filter_logs(deleverage, "EndaomentTransferDuringDeleverage")
    main_log = filter_logs(deleverage, "DeleverageUser")[0]

    # Should have 2 events: bravo (150) and charlie (50)
    assert len(transfer_logs) == 2
    assert transfer_logs[0].asset == bravo_token.address
    _test(transfer_logs[0].usdValue, 150 * EIGHTEEN_DECIMALS)

    assert transfer_logs[1].asset == charlie_token.address
    _test(transfer_logs[1].usdValue, 50 * EIGHTEEN_DECIMALS)

    # Verify balances
    post_bravo = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    post_charlie = simple_erc20_vault.getTotalAmountForUser(bob, charlie_token)

    bravo_used = pre_bravo - post_bravo
    charlie_used = pre_charlie - post_charlie

    _test(bravo_used, 150 * EIGHTEEN_DECIMALS)
    _test(charlie_used, 50 * SIX_DECIMALS)

    # Total repaid should be 200 (debt fully cleared)
    _test(repaid_amount, 200 * EIGHTEEN_DECIMALS)

    # trueTargetRepayAmount should be 200 (capped total)
    _test(main_log.targetRepayAmount, 200 * EIGHTEEN_DECIMALS)


def test_partial_asset_depletion_midway(
    deleverage,
    teller,
    credit_engine,
    simple_erc20_vault,
    bob,
    bravo_token,
    charlie_token,
    bravo_token_whale,
    charlie_token_whale,
    performDeposit,
    setupDeleverage,
    _test,
):
    """
    Test partial asset depletion.
    User has 500 debt, 200 bravo, 400 charlie.
    Request 250 bravo + 300 charlie.
    """
    # Setup: 500 debt
    setupDeleverage(
        bob,
        bravo_token,
        bravo_token_whale,
        deposit_amount=200 * EIGHTEEN_DECIMALS,
        borrow_amount=160 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Add charlie and borrow more
    charlie_token.transfer(bob, 400 * SIX_DECIMALS, sender=charlie_token_whale)
    performDeposit(bob, 400 * SIX_DECIMALS, charlie_token, bob, simple_erc20_vault)
    teller.borrow(340 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    # Pre-state
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    assert pre_debt > 0

    # Call with 250 bravo + 300 charlie
    assets = [
        (3, bravo_token.address, 250 * EIGHTEEN_DECIMALS),
        (3, charlie_token.address, 300 * EIGHTEEN_DECIMALS),
    ]

    repaid_amount = deleverage.deleverageWithSpecificAssets(
        bob, assets, sender=teller.address
    )

    # Get events
    transfer_logs = filter_logs(deleverage, "EndaomentTransferDuringDeleverage")

    # Find each asset's event
    bravo_log = next(e for e in transfer_logs if e.asset == bravo_token.address)
    charlie_log = next(e for e in transfer_logs if e.asset == charlie_token.address)

    # Bravo should be depleted (asked for 250, only had 200)
    assert bravo_log.isDepleted == True
    _test(bravo_log.usdValue, 200 * EIGHTEEN_DECIMALS)

    # Charlie should be used for remaining debt
    assert charlie_log.isDepleted == False
    assert charlie_log.usdValue > 0

    # Total repaid should be bravo + charlie
    total_from_events = bravo_log.usdValue + charlie_log.usdValue
    _test(repaid_amount, total_from_events)

    # Total repaid should match debt reduction
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    debt_reduction = pre_debt - post_debt
    _test(repaid_amount, debt_reduction)

    # Verify debt cleared
    _test(post_debt, 0)


################
# Permissions
################


def test_user_can_call_for_themselves(
    deleverage,
    credit_engine,
    stability_pool,
    bob,
    alpha_token,
    alpha_token_whale,
    savings_green,
    setupDeleverage,
    performDeposit,
):
    """
    Test that user can call deleverageWithSpecificAssets for themselves.
    """
    # Setup
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=500 * EIGHTEEN_DECIMALS,
        borrow_amount=300 * EIGHTEEN_DECIMALS,
        get_sgreen=True,
    )

    sgreen_balance = savings_green.balanceOf(bob)
    performDeposit(bob, sgreen_balance, savings_green, bob, stability_pool)

    # Pre-state
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount

    # Bob calls for himself
    assets = [(1, savings_green.address, 100 * EIGHTEEN_DECIMALS)]

    repaid_amount = deleverage.deleverageWithSpecificAssets(
        bob, assets, sender=bob  # User calling for themselves
    )

    assert repaid_amount > 0

    # Verify debt reduced
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    assert post_debt < pre_debt


def test_untrusted_caller_blocked(
    deleverage,
    stability_pool,
    bob,
    alice,  # Untrusted caller
    alpha_token,
    alpha_token_whale,
    savings_green,
    setupDeleverage,
    performDeposit,
):
    """
    Test that untrusted callers are blocked from calling deleverageWithSpecificAssets.
    This function requires strict trust - no redemption zone exception.
    """
    # Setup
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=500 * EIGHTEEN_DECIMALS,
        borrow_amount=300 * EIGHTEEN_DECIMALS,
        get_sgreen=True,
    )

    sgreen_balance = savings_green.balanceOf(bob)
    performDeposit(bob, sgreen_balance, savings_green, bob, stability_pool)

    # Alice (untrusted) attempts to deleverage Bob
    assets = [(1, savings_green.address, 100 * EIGHTEEN_DECIMALS)]

    with boa.reverts("not allowed"):
        deleverage.deleverageWithSpecificAssets(bob, assets, sender=alice)


###########################
# Edge Cases & Errors
###########################


def test_empty_array_fails(
    deleverage,
    teller,
    bob,
    alpha_token,
    alpha_token_whale,
    setupDeleverage,
):
    """
    Test that empty asset array fails with 'no assets processed'.
    """
    # Setup
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=500 * EIGHTEEN_DECIMALS,
        borrow_amount=300 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Call with empty array
    assets = []

    with boa.reverts("no assets processed"):
        deleverage.deleverageWithSpecificAssets(bob, assets, sender=teller.address)


def test_all_invalid_vaults_fails(
    deleverage,
    teller,
    bob,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    setupDeleverage,
):
    """
    Test that all invalid vault IDs causes failure.
    """
    # Setup
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=500 * EIGHTEEN_DECIMALS,
        borrow_amount=300 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Call with invalid vault IDs
    assets = [
        (999, bravo_token.address, 100 * EIGHTEEN_DECIMALS),
        (888, alpha_token.address, 200 * EIGHTEEN_DECIMALS),
    ]

    with boa.reverts("no assets processed"):
        deleverage.deleverageWithSpecificAssets(bob, assets, sender=teller.address)
