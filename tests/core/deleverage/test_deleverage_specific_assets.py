import pytest
import boa
from constants import EIGHTEEN_DECIMALS
from conf_utils import filter_logs

SIX_DECIMALS = 10**6  # For tokens like USDC/Charlie that have 6 decimals


def _set_full_payoff_params(
    deleverage,
    switchboard_alpha,
    buffer_amount=0,
    overage_bps=0,
    dust_threshold=0,
    dust_bps=0,
):
    deleverage.setDeleverageFullPayoffParam(1, buffer_amount, sender=switchboard_alpha.address)
    deleverage.setDeleverageFullPayoffParam(2, overage_bps, sender=switchboard_alpha.address)
    deleverage.setDeleverageFullPayoffParam(3, dust_threshold, sender=switchboard_alpha.address)
    deleverage.setDeleverageFullPayoffParam(4, dust_bps, sender=switchboard_alpha.address)


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
    mock_undy_v2,
    deleverage,
    switchboard_alpha,
    alice,
):
    # Specific-asset tests use the intended production defaults so full-payoff
    # behavior is exercised by default; tests opt out by setting params to zero.
    _set_full_payoff_params(
        deleverage,
        switchboard_alpha,
        buffer_amount=10**15,
        overage_bps=100,
        dust_threshold=10**15,
        dust_bps=100,
    )
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

    yield
    mock_undy_v2.setEarnVault(alice, False)
    mock_undy_v2.setBasicEarnVault(alice, False)
    mock_undy_v2.setAllAddressesAreVaults(True)


######################
# Basic Functionality
######################


def test_single_asset_sgreen_burn(
    switchboard_alpha,
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

    repaid_amount = teller.deleverageWithSpecificAssets(
        assets, bob, sender=switchboard_alpha.address
    )

    # Get events immediately
    burn_log = filter_logs(teller, "StabAssetBurntDuringDeleverage")[0]
    main_log = filter_logs(teller, "DeleverageUser")[0]

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
    assert main_log.caller == switchboard_alpha.address
    _test(main_log.targetRepayAmount, target_amount)
    _test(main_log.targetRepayAmountWithBuffer, target_amount)
    _test(main_log.collateralValueRepaid, target_amount)
    _test(main_log.debtToClear, repaid_amount)
    assert main_log.hasGoodDebtHealth == True


def test_single_asset_endaoment_transfer(
    switchboard_alpha,
    deleverage,
    teller,
    credit_engine,
    simple_erc20_vault,
    bob,
    bravo_token,
    bravo_token_whale,
    endaoment_funds,
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
    pre_endaoment_bravo = bravo_token.balanceOf(endaoment_funds)

    # Call deleverageWithSpecificAssets
    target_amount = 200 * EIGHTEEN_DECIMALS
    assets = [(3, bravo_token.address, target_amount)]

    repaid_amount = teller.deleverageWithSpecificAssets(
        assets, bob, sender=switchboard_alpha.address
    )

    # Get events immediately
    transfer_log = filter_logs(teller, "EndaomentTransferDuringDeleverage")[0]
    main_log = filter_logs(teller, "DeleverageUser")[0]

    # Post-state
    post_bravo_vault = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    post_endaoment_bravo = bravo_token.balanceOf(endaoment_funds)

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
    assert main_log.caller == switchboard_alpha.address
    _test(main_log.targetRepayAmount, target_amount)
    _test(main_log.debtToClear, repaid_amount)


def test_partial_target_specific_assets_do_not_use_full_payoff_extras(
    switchboard_alpha,
    teller,
    credit_engine,
    simple_erc20_vault,
    bob,
    bravo_token,
    bravo_token_whale,
    setupDeleverage,
):
    """
    Enabled full-payoff params must not add buffer or forgive dust for partial targets.
    """
    setupDeleverage(
        bob,
        bravo_token,
        bravo_token_whale,
        deposit_amount=500 * EIGHTEEN_DECIMALS,
        borrow_amount=300 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    target_amount = pre_debt // 2
    assets = [(3, bravo_token.address, target_amount)]

    repaid_amount = teller.deleverageWithSpecificAssets(
        assets, bob, sender=switchboard_alpha.address
    )

    transfer_log = filter_logs(teller, "EndaomentTransferDuringDeleverage")[0]
    main_log = filter_logs(teller, "DeleverageUser")[0]

    assert repaid_amount == target_amount
    assert transfer_log.usdValue == target_amount
    assert main_log.targetRepayAmount == target_amount
    assert main_log.targetRepayAmountWithBuffer == target_amount
    assert main_log.collateralValueRepaid == target_amount
    assert main_log.debtToClear == target_amount


def test_full_payoff_single_specific_asset_uses_buffer(
    switchboard_alpha,
    teller,
    credit_engine,
    simple_erc20_vault,
    bob,
    bravo_token,
    bravo_token_whale,
    endaoment_funds,
    setupDeleverage,
):
    """
    Full-payoff specific-asset calls lift the collateral target by the configured buffer,
    while debt clearing stays capped at the real debt amount.
    """
    setupDeleverage(
        bob,
        bravo_token,
        bravo_token_whale,
        deposit_amount=500 * EIGHTEEN_DECIMALS,
        borrow_amount=300 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    expected_buffer = min(10**15, pre_debt * 100 // 100_00)
    pre_bravo_vault = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    pre_endaoment_bravo = bravo_token.balanceOf(endaoment_funds)

    assets = [(3, bravo_token.address, pre_debt)]
    repaid_amount = teller.deleverageWithSpecificAssets(
        assets, bob, sender=switchboard_alpha.address
    )

    transfer_log = filter_logs(teller, "EndaomentTransferDuringDeleverage")[0]
    main_log = filter_logs(teller, "DeleverageUser")[0]

    post_bravo_vault = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    post_endaoment_bravo = bravo_token.balanceOf(endaoment_funds)
    bravo_transferred = pre_bravo_vault - post_bravo_vault

    assert repaid_amount == pre_debt
    assert credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount == 0
    assert bravo_transferred == pre_debt + expected_buffer
    assert post_endaoment_bravo - pre_endaoment_bravo == bravo_transferred
    assert transfer_log.usdValue == pre_debt + expected_buffer
    assert main_log.targetRepayAmount == pre_debt
    assert main_log.targetRepayAmountWithBuffer == pre_debt + expected_buffer
    assert main_log.collateralValueRepaid == pre_debt + expected_buffer
    assert main_log.debtToClear == pre_debt


def test_full_payoff_specific_assets_forgives_dust_after_real_collateral(
    switchboard_alpha,
    deleverage,
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
):
    """
    Dust forgiveness applies to specific-assets full payoff only after nonzero
    collateral was consumed and both dust caps allow the remainder.
    """
    _set_full_payoff_params(
        deleverage,
        switchboard_alpha,
        dust_threshold=1,
        dust_bps=100,
    )

    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    performDeposit(bob, pre_debt - 1, bravo_token, bravo_token_whale, simple_erc20_vault)

    assets = [(3, bravo_token.address, pre_debt)]
    repaid_amount = teller.deleverageWithSpecificAssets(
        assets, bob, sender=switchboard_alpha.address
    )

    transfer_log = filter_logs(teller, "EndaomentTransferDuringDeleverage")[0]
    main_log = filter_logs(teller, "DeleverageUser")[0]

    assert repaid_amount == pre_debt
    assert credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount == 0
    assert transfer_log.usdValue == pre_debt - 1
    assert main_log.targetRepayAmount == pre_debt
    assert main_log.targetRepayAmountWithBuffer == pre_debt
    assert main_log.collateralValueRepaid == pre_debt - 1
    assert main_log.debtToClear == pre_debt


def test_full_payoff_specific_assets_excludes_underscore_earn_vault_caller(
    switchboard_alpha,
    deleverage,
    teller,
    credit_engine,
    simple_erc20_vault,
    bob,
    alice,
    bravo_token,
    bravo_token_whale,
    setupDeleverage,
    mission_control,
    mock_undy_v2,
):
    """
    Underscore earn-vault callers remain trusted, but they do not get the new
    full-payoff buffer or dust behavior.
    """
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_undy_v2.setAllAddressesAreVaults(False)
    mock_undy_v2.setEarnVault(alice, True)
    mock_undy_v2.setBasicEarnVault(alice, False)

    _set_full_payoff_params(
        deleverage,
        switchboard_alpha,
        buffer_amount=10**15,
        overage_bps=100,
        dust_threshold=10**15,
        dust_bps=100,
    )

    setupDeleverage(
        bob,
        bravo_token,
        bravo_token_whale,
        deposit_amount=500 * EIGHTEEN_DECIMALS,
        borrow_amount=300 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    pre_bravo_vault = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)

    assets = [(3, bravo_token.address, pre_debt)]
    repaid_amount = teller.deleverageWithSpecificAssets(
        assets, bob, sender=alice
    )

    transfer_log = filter_logs(teller, "EndaomentTransferDuringDeleverage")[0]
    main_log = filter_logs(teller, "DeleverageUser")[0]
    post_bravo_vault = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)

    assert repaid_amount == pre_debt
    assert credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount == 0
    assert pre_bravo_vault - post_bravo_vault == pre_debt
    assert transfer_log.usdValue == pre_debt
    assert main_log.targetRepayAmount == pre_debt
    assert main_log.targetRepayAmountWithBuffer == pre_debt
    assert main_log.collateralValueRepaid == pre_debt
    assert main_log.debtToClear == pre_debt


def test_full_payoff_specific_assets_carries_buffer_after_depleted_trigger_asset(
    switchboard_alpha,
    teller,
    credit_engine,
    stability_pool,
    simple_erc20_vault,
    bob,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    charlie_token,
    charlie_token_whale,
    savings_green,
    setAssetConfig,
    createDebtTerms,
    setupDeleverage,
    performDeposit,
):
    """
    If the asset that completes full-payoff intent cannot fill the buffer, the
    remaining buffer stays in the collateral budget for later specified assets.
    """
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=60_00,
        _liqThreshold=70_00,
        _liqFee=10_00,
        _borrowRate=0,
    )
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
    )

    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=100 * EIGHTEEN_DECIMALS,
        get_sgreen=True,
    )

    sgreen_balance = savings_green.balanceOf(bob)
    performDeposit(bob, sgreen_balance, savings_green, bob, stability_pool)
    performDeposit(bob, 50 * EIGHTEEN_DECIMALS, bravo_token, bravo_token_whale, simple_erc20_vault)
    performDeposit(bob, 30 * SIX_DECIMALS, charlie_token, charlie_token_whale, simple_erc20_vault)

    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    expected_buffer = min(10**15, pre_debt * 100 // 100_00)

    bravo_target = 50 * EIGHTEEN_DECIMALS
    charlie_available = 30 * EIGHTEEN_DECIMALS
    charlie_target = pre_debt - bravo_target
    charlie_consumed = min(charlie_available, charlie_target)
    sgreen_consumed = pre_debt + expected_buffer - bravo_target - charlie_consumed

    assets = [
        (3, bravo_token.address, bravo_target),
        (3, charlie_token.address, charlie_target),
        (1, savings_green.address, 2**256 - 1),
    ]
    repaid_amount = teller.deleverageWithSpecificAssets(
        assets, bob, sender=switchboard_alpha.address
    )

    transfer_logs = filter_logs(teller, "EndaomentTransferDuringDeleverage")
    burn_log = filter_logs(teller, "StabAssetBurntDuringDeleverage")[0]
    main_log = filter_logs(teller, "DeleverageUser")[0]

    assert repaid_amount == pre_debt
    assert credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount == 0
    assert transfer_logs[0].asset == bravo_token.address
    assert transfer_logs[0].usdValue == bravo_target
    assert transfer_logs[1].asset == charlie_token.address
    assert transfer_logs[1].usdValue == charlie_consumed
    assert burn_log.usdValue == sgreen_consumed
    assert main_log.targetRepayAmount == pre_debt
    assert main_log.targetRepayAmountWithBuffer == pre_debt + expected_buffer
    assert main_log.collateralValueRepaid == pre_debt + expected_buffer
    assert main_log.debtToClear == pre_debt


def test_multiple_assets_custom_order(
    switchboard_alpha,
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

    repaid_amount = teller.deleverageWithSpecificAssets(
        assets, bob, sender=switchboard_alpha.address
    )

    # Get events immediately
    transfer_logs = filter_logs(teller, "EndaomentTransferDuringDeleverage")
    burn_logs = filter_logs(teller, "StabAssetBurntDuringDeleverage")

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
    switchboard_alpha,
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

    teller.deleverageWithSpecificAssets(assets, bob, sender=switchboard_alpha.address)

    # Get events immediately
    transfer_logs = filter_logs(teller, "EndaomentTransferDuringDeleverage")
    burn_logs = filter_logs(teller, "StabAssetBurntDuringDeleverage")

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
    switchboard_alpha,
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

    repaid_amount = teller.deleverageWithSpecificAssets(
        assets, bob, sender=switchboard_alpha.address
    )

    # Get events immediately
    burn_logs = filter_logs(teller, "StabAssetBurntDuringDeleverage")

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
    switchboard_alpha,
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

    repaid_amount = teller.deleverageWithSpecificAssets(
        assets, bob, sender=switchboard_alpha.address
    )

    # Get main event
    main_log = filter_logs(teller, "DeleverageUser")[0]

    # Post-state
    post_sgreen = stability_pool.getTotalAmountForUser(bob, savings_green)
    sgreen_used = pre_sgreen - post_sgreen

    # Should use ALL available, not fail on overflow
    _test(sgreen_used, pre_sgreen)
    _test(post_sgreen, 0)
    assert repaid_amount > 0

    # trueTargetRepayAmount should be capped amount, not max_uint
    _test(main_log.targetRepayAmount, repaid_amount)
    _test(main_log.debtToClear, repaid_amount)


def test_caps_per_asset_when_debt_runs_out(
    switchboard_alpha,
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

    repaid_amount = teller.deleverageWithSpecificAssets(
        assets, bob, sender=switchboard_alpha.address
    )

    # Get events
    transfer_logs = filter_logs(teller, "EndaomentTransferDuringDeleverage")
    main_log = filter_logs(teller, "DeleverageUser")[0]
    expected_buffer = min(10**15, main_log.targetRepayAmount * 100 // 100_00)

    # Should have 2 events: bravo (150) and charlie (50)
    assert len(transfer_logs) == 2
    assert transfer_logs[0].asset == bravo_token.address
    _test(transfer_logs[0].usdValue, 150 * EIGHTEEN_DECIMALS)

    assert transfer_logs[1].asset == charlie_token.address
    _test(transfer_logs[1].usdValue, 50 * EIGHTEEN_DECIMALS + expected_buffer)

    # Verify balances
    post_bravo = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    post_charlie = simple_erc20_vault.getTotalAmountForUser(bob, charlie_token)

    bravo_used = pre_bravo - post_bravo
    charlie_used = pre_charlie - post_charlie

    _test(bravo_used, 150 * EIGHTEEN_DECIMALS)
    _test(charlie_used, 50 * SIX_DECIMALS + expected_buffer // 10**12)

    # Total repaid should be 200 (debt fully cleared)
    _test(repaid_amount, 200 * EIGHTEEN_DECIMALS)

    # trueTargetRepayAmount should be 200 (capped total)
    _test(main_log.targetRepayAmount, 200 * EIGHTEEN_DECIMALS)
    _test(main_log.targetRepayAmountWithBuffer, 200 * EIGHTEEN_DECIMALS + expected_buffer)
    _test(main_log.collateralValueRepaid, 200 * EIGHTEEN_DECIMALS + expected_buffer)
    _test(main_log.debtToClear, 200 * EIGHTEEN_DECIMALS)


def test_partial_asset_depletion_midway(
    switchboard_alpha,
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

    repaid_amount = teller.deleverageWithSpecificAssets(
        assets, bob, sender=switchboard_alpha.address
    )

    # Get events
    transfer_logs = filter_logs(teller, "EndaomentTransferDuringDeleverage")

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
    expected_buffer = min(10**15, pre_debt * 100 // 100_00)
    _test(total_from_events, repaid_amount + expected_buffer)

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
    teller,
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

    repaid_amount = teller.deleverageWithSpecificAssets(
        assets, bob, sender=bob  # User calling for themselves
    )

    assert repaid_amount > 0

    # Verify debt reduced
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    assert post_debt < pre_debt


def test_untrusted_caller_blocked(
    teller,
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
        teller.deleverageWithSpecificAssets(assets, bob, sender=alice)


###########################
# Edge Cases & Errors
###########################


def test_empty_array_fails(
    switchboard_alpha,
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
        teller.deleverageWithSpecificAssets(assets, bob, sender=switchboard_alpha.address)


def test_full_payoff_specific_assets_all_skipped_still_reverts(
    switchboard_alpha,
    teller,
    bob,
    alpha_token,
    alpha_token_whale,
    setupDeleverage,
):
    """
    Full-payoff buffer cannot turn skipped/non-deleveragable assets into a debt clear.
    """
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=500 * EIGHTEEN_DECIMALS,
        borrow_amount=300 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    assets = [(3, alpha_token.address, 2**256 - 1)]

    with boa.reverts("no assets processed"):
        teller.deleverageWithSpecificAssets(assets, bob, sender=switchboard_alpha.address)


def test_all_invalid_vaults_fails(
    switchboard_alpha,
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
        teller.deleverageWithSpecificAssets(assets, bob, sender=switchboard_alpha.address)
