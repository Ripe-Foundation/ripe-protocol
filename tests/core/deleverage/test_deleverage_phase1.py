import pytest
from constants import EIGHTEEN_DECIMALS
from conf_utils import filter_logs


@pytest.fixture(autouse=True)
def setup(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    alpha_token,
    savings_green,
    green_token,
    stability_pool,
    setup_priority_configs,
):
    setGeneralConfig()
    setGeneralDebtConfig()

    # Configure alpha_token as collateral
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

    # Configure sGREEN and GREEN for burning (stability pool assets)
    stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(
        savings_green,
        _vaultIds=[1], # Stability Pool
        _debtTerms=stab_debt_terms,
        _shouldBurnAsPayment=True,
    )
    setAssetConfig(
        green_token,
        _vaultIds=[1],
        _debtTerms=stab_debt_terms,
        _shouldBurnAsPayment=True,
    )

    # Set priority stability vaults for Phase 1
    setup_priority_configs(
        priority_stab_assets=[
            (stability_pool, savings_green),
            (stability_pool, green_token),
        ]
    )


def test_phase1_burns_users_sgreen_from_stability_pool(
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
    switchboard_alpha,
):
    # borrowed and received sGREEN
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=True,  # User receives sGREEN
    )

    # get user's sGREEN balance and deposit ALL into stability pool
    sgreen_balance = savings_green.balanceOf(bob)
    assert sgreen_balance > 0, "User should have sGREEN"

    # deposit into stability pool
    performDeposit(bob, sgreen_balance, savings_green, bob, stability_pool)

    # verify deposit succeeded
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    assert pre_debt > 0, "User should have debt"

    # pre-deleverage balances
    pre_sgreen_in_pool = stability_pool.getTotalAmountForUser(bob, savings_green)  # vault_id=1 is stability pool
    assert pre_sgreen_in_pool > 0, "User should have sGREEN in stability pool"

    # deleverage!
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # events
    logDetail = filter_logs(teller, "StabAssetBurntDuringDeleverage")[0]
    log = filter_logs(teller, "DeleverageUser")[0]

    # verify sGREEN was burned
    post_sgreen_in_pool = stability_pool.getTotalAmountForUser(bob, savings_green)
    sgreen_burned_from_pool = pre_sgreen_in_pool - post_sgreen_in_pool
    _test(sgreen_balance, sgreen_burned_from_pool)

    # verify debt was reduced
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    debt_reduction = pre_debt - post_debt
    _test(repaid_amount, debt_reduction)

    # verify detailed event
    assert logDetail.user == bob
    assert logDetail.vaultId == 1
    assert logDetail.stabAsset == savings_green.address
    assert logDetail.amountBurned == sgreen_burned_from_pool
    assert logDetail.usdValue == debt_reduction
    assert logDetail.isDepleted == True

    # verify event
    assert log.user == bob
    assert log.caller == switchboard_alpha.address  # caller is now the actual sender
    assert log.targetRepayAmount == pre_debt
    assert log.repaidAmount == repaid_amount
    assert log.hasGoodDebtHealth == True


def test_phase1_burns_users_green_from_stability_pool(
    teller,
    credit_engine,
    stability_pool,
    bob,
    alpha_token,
    alpha_token_whale,
    green_token,
    setupDeleverage,
    performDeposit,
    _test,
    switchboard_alpha,
):
    """
    Test that user's GREEN in stability pool is burned during Phase 1 deleveraging.
    Similar to sGREEN test but uses GREEN directly.
    """
    # borrowed and received GREEN (not sGREEN)
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,  # User receives GREEN
    )

    # get user's GREEN balance and deposit ALL into stability pool
    green_balance = green_token.balanceOf(bob)
    assert green_balance > 0, "User should have GREEN"

    # deposit into stability pool
    performDeposit(bob, green_balance, green_token, bob, stability_pool)

    # verify deposit succeeded
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    assert pre_debt > 0, "User should have debt"

    # pre-deleverage balances
    pre_green_in_pool = stability_pool.getTotalAmountForUser(bob, green_token)
    assert pre_green_in_pool > 0, "User should have GREEN in stability pool"

    # deleverage!
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # events
    logDetail = filter_logs(teller, "StabAssetBurntDuringDeleverage")[0]
    log = filter_logs(teller, "DeleverageUser")[0]

    # verify GREEN was burned
    post_green_in_pool = stability_pool.getTotalAmountForUser(bob, green_token)
    green_burned_from_pool = pre_green_in_pool - post_green_in_pool
    _test(green_balance, green_burned_from_pool)

    # verify debt was reduced
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    debt_reduction = pre_debt - post_debt
    _test(repaid_amount, debt_reduction)

    # verify detailed event
    assert logDetail.user == bob
    assert logDetail.vaultId == 1
    assert logDetail.stabAsset == green_token.address
    assert logDetail.amountBurned == green_burned_from_pool
    assert logDetail.usdValue == debt_reduction
    assert logDetail.isDepleted == True

    # verify event
    assert log.user == bob
    assert log.caller == switchboard_alpha.address  # caller is now the actual sender
    assert log.targetRepayAmount == pre_debt
    assert log.repaidAmount == repaid_amount
    assert log.hasGoodDebtHealth == True


def test_phase1_partial_burn_when_sgreen_exceeds_debt(
    teller,
    credit_engine,
    stability_pool,
    bob,
    alice,
    alpha_token,
    alpha_token_whale,
    savings_green,
    setupDeleverage,
    performDeposit,
    _test,
    switchboard_alpha,
):
    """
    Test that when user has MORE sGREEN than debt, only enough is burned
    to satisfy the target repay amount, leaving remaining sGREEN in the pool.
    """
    # Setup: User borrows less and has more sGREEN
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=200 * EIGHTEEN_DECIMALS,  # Smaller debt
        get_sgreen=True,
    )

    # Get sGREEN and deposit to pool
    sgreen_balance = savings_green.balanceOf(bob)
    performDeposit(bob, sgreen_balance, savings_green, bob, stability_pool)

    # Give user MORE sGREEN by transferring from another user
    setupDeleverage(
        alice,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=True,
    )
    alice_sgreen = savings_green.balanceOf(alice)
    savings_green.transfer(bob, alice_sgreen, sender=alice)
    performDeposit(bob, alice_sgreen, savings_green, bob, stability_pool)

    # Pre-state
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    pre_sgreen_in_pool = stability_pool.getTotalAmountForUser(bob, savings_green)

    # Convert sGREEN to underlying GREEN to compare with debt
    green_underlying = savings_green.convertToAssets(pre_sgreen_in_pool)
    assert green_underlying > pre_debt, "User should have more GREEN (from sGREEN) than debt"

    # Deleverage
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Get events immediately
    logDetail = filter_logs(teller, "StabAssetBurntDuringDeleverage")[0]
    log = filter_logs(teller, "DeleverageUser")[0]

    # Verify partial burn
    post_sgreen_in_pool = stability_pool.getTotalAmountForUser(bob, savings_green)
    sgreen_burned = pre_sgreen_in_pool - post_sgreen_in_pool

    # Should not burn all sGREEN
    assert sgreen_burned < pre_sgreen_in_pool, "Should not burn all sGREEN"
    assert post_sgreen_in_pool > 0, "Should have sGREEN remaining"

    # Verify debt was reduced (possibly to zero)
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    debt_reduction = pre_debt - post_debt
    _test(repaid_amount, debt_reduction)

    assert logDetail.user == bob
    assert logDetail.amountBurned == sgreen_burned
    assert logDetail.isDepleted == False  # Not fully depleted

    assert log.repaidAmount == repaid_amount
    assert log.hasGoodDebtHealth == True


def test_phase1_depletes_stab_asset_when_insufficient(
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
    switchboard_alpha,
):
    """
    Test that when user has insufficient stab pool assets to fully repay debt,
    Phase 1 depletes what's available and marks isDepleted=True.
    """
    # Setup user with debt
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=True,
    )

    # User deposits only HALF their sGREEN to pool
    sgreen_balance = savings_green.balanceOf(bob)
    half_sgreen = sgreen_balance // 2
    performDeposit(bob, half_sgreen, savings_green, bob, stability_pool)

    # Pre-state
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    pre_sgreen_in_pool = stability_pool.getTotalAmountForUser(bob, savings_green)

    green_underlying = savings_green.convertToAssets(pre_sgreen_in_pool)
    assert green_underlying < pre_debt, "User should have less sGREEN than debt"

    # Deleverage
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Get events
    logDetail = filter_logs(teller, "StabAssetBurntDuringDeleverage")[0]
    log = filter_logs(teller, "DeleverageUser")[0]

    # Verify full depletion
    post_sgreen_in_pool = stability_pool.getTotalAmountForUser(bob, savings_green)
    sgreen_burned = pre_sgreen_in_pool - post_sgreen_in_pool

    # Should burn all available sGREEN
    _test(sgreen_burned, pre_sgreen_in_pool)
    assert post_sgreen_in_pool == 0, "Should have no sGREEN remaining"

    # Verify debt was reduced but not fully repaid
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    assert post_debt < pre_debt, "Debt should be reduced"
    assert post_debt > 0, "Debt should still exist"

    # Verify events show depletion
    assert logDetail.isDepleted == True  # Fully depleted
    assert logDetail.amountBurned == sgreen_burned
    _test(repaid_amount, sgreen_burned)


def test_phase1_burns_both_sgreen_and_green_in_order(
    teller,
    credit_engine,
    stability_pool,
    bob,
    alpha_token,
    alpha_token_whale,
    savings_green,
    green_token,
    setupDeleverage,
    performDeposit,
    _test,
    switchboard_alpha,
):
    """
    Test that when user has both sGREEN and GREEN, Phase 1 processes
    them in priority order (sGREEN first, then GREEN).

    Setup ensures both assets WILL be burned by having debt that requires both.
    """
    # Setup user
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=300 * EIGHTEEN_DECIMALS,
        get_sgreen=True,
    )

    # Deposit only SMALL amount of sGREEN (not enough to cover debt)
    sgreen_balance = savings_green.balanceOf(bob)
    performDeposit(bob, sgreen_balance, savings_green, bob, stability_pool)

    # Borrow MORE and get GREEN (more than needed so it won't be depleted)
    teller.borrow(400 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    green_balance = green_token.balanceOf(bob)
    performDeposit(bob, green_balance, green_token, bob, stability_pool)

    # Pre-state
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    pre_sgreen = stability_pool.getTotalAmountForUser(bob, savings_green)
    pre_green = stability_pool.getTotalAmountForUser(bob, green_token)

    # Deleverage
    repaid_amount = teller.deleverageUser(bob, 400 * EIGHTEEN_DECIMALS, sender=switchboard_alpha.address)

    # Get events immediately
    burn_logs = filter_logs(teller, "StabAssetBurntDuringDeleverage")

    # BOTH assets must be burned (sGREEN depleted first, then GREEN used)
    assert len(burn_logs) == 2, "Should have exactly 2 burn events"

    # Verify priority order: sGREEN event comes FIRST
    assert burn_logs[0].stabAsset == savings_green.address, "First event must be sGREEN"
    assert burn_logs[0].isDepleted == True, "sGREEN must be fully depleted"

    # GREEN event comes SECOND
    assert burn_logs[1].stabAsset == green_token.address, "Second event must be GREEN"
    assert burn_logs[1].isDepleted == False

    # Verify both were actually burned from pool
    post_sgreen = stability_pool.getTotalAmountForUser(bob, savings_green)
    post_green = stability_pool.getTotalAmountForUser(bob, green_token)

    assert post_sgreen == 0, "sGREEN should be fully depleted"
    assert post_green < pre_green, "GREEN should be partially burned"
    assert post_green != 0

    # Verify debt reduction
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    debt_reduction = pre_debt - post_debt
    _test(repaid_amount, debt_reduction)


def test_phase1_with_target_repay_amount(
    teller,
    credit_engine,
    stability_pool,
    bob,
    alice,
    alpha_token,
    alpha_token_whale,
    savings_green,
    setupDeleverage,
    performDeposit,
    _test,
    switchboard_alpha,
):
    """
    Test that Phase 1 respects targetRepayAmount parameter and only burns
    up to that amount even if more is available.
    """
    # Setup user with plenty of sGREEN
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=200 * EIGHTEEN_DECIMALS,
        get_sgreen=True,
    )

    # Give user more sGREEN from alice
    setupDeleverage(
        alice,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=True,
    )
    alice_sgreen = savings_green.balanceOf(alice)
    savings_green.transfer(bob, alice_sgreen, sender=alice)

    # Deposit all sGREEN to pool
    sgreen_balance = savings_green.balanceOf(bob)
    performDeposit(bob, sgreen_balance, savings_green, bob, stability_pool)

    # Pre-state
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    pre_sgreen_in_pool = stability_pool.getTotalAmountForUser(bob, savings_green)

    # Set target repay to only 100 GREEN
    target_repay = 100 * EIGHTEEN_DECIMALS

    # Deleverage with target
    repaid_amount = teller.deleverageUser(bob, target_repay, sender=switchboard_alpha.address)

    # Get events
    logDetail = filter_logs(teller, "StabAssetBurntDuringDeleverage")[0]
    log = filter_logs(teller, "DeleverageUser")[0]

    # Verify only target amount was repaid
    assert repaid_amount <= target_repay, "Should not exceed target repay"
    _test(repaid_amount, target_repay)

    # Verify partial burn
    post_sgreen_in_pool = stability_pool.getTotalAmountForUser(bob, savings_green)
    sgreen_burned = pre_sgreen_in_pool - post_sgreen_in_pool

    assert sgreen_burned < pre_sgreen_in_pool, "Should not burn all sGREEN"
    assert post_sgreen_in_pool > 0, "Should have sGREEN remaining"

    # Verify event
    assert log.targetRepayAmount == target_repay
    _test(log.repaidAmount, target_repay)


def test_phase1_processes_green_after_sgreen_depleted(
    teller,
    credit_engine,
    stability_pool,
    bob,
    alpha_token,
    alpha_token_whale,
    savings_green,
    green_token,
    setupDeleverage,
    performDeposit,
    _test,
    switchboard_alpha,
):
    """
    Test that when sGREEN in pool is depleted but insufficient,
    Phase 1 continues to GREEN in priority order.
    """
    # Setup user with sGREEN
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=300 * EIGHTEEN_DECIMALS,
        get_sgreen=True,
    )

    # Deposit only SMALL amount of sGREEN
    sgreen_balance = savings_green.balanceOf(bob)
    small_sgreen = sgreen_balance // 4  # 25% only
    performDeposit(bob, small_sgreen, savings_green, bob, stability_pool)

    # Also borrow and deposit GREEN
    teller.borrow(400 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    green_balance = green_token.balanceOf(bob)
    performDeposit(bob, green_balance, green_token, bob, stability_pool)

    # Pre-state
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    pre_sgreen = stability_pool.getTotalAmountForUser(bob, savings_green)
    pre_green = stability_pool.getTotalAmountForUser(bob, green_token)

    # Deleverage
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Get events
    burn_logs = filter_logs(teller, "StabAssetBurntDuringDeleverage")
    log = filter_logs(teller, "DeleverageUser")[0]

    # Should have 2 burn events (sGREEN depleted, then GREEN used)
    assert len(burn_logs) == 2, "Should have 2 burn events"

    # Verify sGREEN event
    sgreen_event = burn_logs[0]
    assert sgreen_event.stabAsset == savings_green.address
    assert sgreen_event.isDepleted == True

    # Verify GREEN event
    green_event = burn_logs[1]
    assert green_event.stabAsset == green_token.address
    assert green_event.isDepleted == True

    # Verify both were burned
    post_sgreen = stability_pool.getTotalAmountForUser(bob, savings_green)
    post_green = stability_pool.getTotalAmountForUser(bob, green_token)

    assert post_sgreen == 0, "sGREEN should be fully depleted"
    assert post_green < pre_green, "GREEN should be partially burned"


def test_phase1_zero_balance_handled_gracefully(
    teller,
    credit_engine,
    stability_pool,
    bob,
    alpha_token,
    alpha_token_whale,
    savings_green,
    green_token,
    setupDeleverage,
    performDeposit,
    switchboard_alpha,
):
    """
    Test that if a priority asset has zero balance, Phase 1 skips it
    and continues to next asset without errors.
    """
    # Setup user with debt but only GREEN (no sGREEN)
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,  # Get GREEN only
    )

    # Deposit GREEN to pool
    green_balance = green_token.balanceOf(bob)
    performDeposit(bob, green_balance, green_token, bob, stability_pool)

    # Verify user has NO sGREEN in pool
    sgreen_in_pool = stability_pool.getTotalAmountForUser(bob, savings_green)
    assert sgreen_in_pool == 0, "User should have no sGREEN in pool"

    # Pre-state
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    pre_green = stability_pool.getTotalAmountForUser(bob, green_token)

    # Deleverage (should skip sGREEN, process GREEN)
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Get events
    burn_logs = filter_logs(teller, "StabAssetBurntDuringDeleverage")

    # Should only have 1 burn event for GREEN (sGREEN skipped)
    assert len(burn_logs) == 1, "Should have 1 burn event"
    assert burn_logs[0].stabAsset == green_token.address

    # Verify GREEN was burned
    post_green = stability_pool.getTotalAmountForUser(bob, green_token)
    assert post_green < pre_green, "GREEN should be burned"

    # Verify debt reduced
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount
    assert post_debt < pre_debt, "Debt should be reduced"


def test_phase1_skipped_when_priority_vaults_empty(
    teller,
    bob,
    alpha_token,
    alpha_token_whale,
    savings_green,
    setupDeleverage,
    setup_priority_configs,
    setAssetConfig,
    createDebtTerms,
    switchboard_alpha,
):
    """
    Test that Phase 1 is completely skipped when priority stab vaults list is empty.
    Tests line 244: if len(_priorityStabVaults) != 0
    """
    # Configure alpha_token for Endaoment transfer (Phase 3 will handle it)
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=60_00,
        _liqThreshold=70_00,
        _liqFee=10_00,
        _borrowRate=5_00,
    )
    setAssetConfig(
        alpha_token,
        _vaultIds=[3],
        _debtTerms=debt_terms,
        _shouldTransferToEndaoment=True,
    )

    # Setup user with debt
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=True,
    )

    # User has sGREEN but doesn't deposit to pool
    sgreen_balance = savings_green.balanceOf(bob)
    assert sgreen_balance > 0, "User should have sGREEN"

    # Configure EMPTY priority stab vaults (Phase 1 should be skipped)
    setup_priority_configs(
        priority_stab_assets=[],  # EMPTY LIST
        priority_liq_assets=[]
    )

    # Deleverage (Phase 1 should be skipped, Phase 3 should handle)
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Get events immediately
    burn_logs = filter_logs(teller, "StabAssetBurntDuringDeleverage")
    deleverage_logs = filter_logs(teller, "DeleverageUser")

    # Phase 1 skipped - NO burn events
    assert len(burn_logs) == 0, "Should have no burn events (Phase 1 skipped)"

    # Should still have DeleverageUser event (Phase 3 handled it)
    assert len(deleverage_logs) == 1, "Should have DeleverageUser event"

    # Verify deleverage still occurred via Phase 3
    log = deleverage_logs[0]
    assert log.user == bob
    assert repaid_amount > 0, "Should have repaid some debt via Phase 3"


def test_phase1_user_not_participating_in_any_priority_vault(
    teller,
    bob,
    alice,
    alpha_token,
    alpha_token_whale,
    savings_green,
    setupDeleverage,
    setup_priority_configs,
    performDeposit,
    stability_pool,
    setAssetConfig,
    createDebtTerms,
    switchboard_alpha,
):
    """
    Test that Phase 1 skips processing when user is not participating in any priority vault.

    Tests line 247: if not staticcall Ledger(_a.ledger).isParticipatingInVault(_user, stabPool.vaultId)

    Flow:
    1. Alice deposits to stability pool (becomes participating user)
    2. Bob has debt but NO deposits in stability pool (not participating)
    3. Configure priority stab vaults (stability pool with sGREEN)
    4. Bob's deleverage should skip Phase 1 (not participating)
    5. No burn events should occur
    """
    # Configure alpha_token for Phase 3 (Endaoment transfer)
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=60_00,
        _liqThreshold=70_00,
        _liqFee=10_00,
        _borrowRate=5_00,
    )
    setAssetConfig(
        alpha_token,
        _vaultIds=[3],  # Simple vault
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,  # Phase 3 will transfer to Endaoment
    )

    # Setup Alice with stability pool deposits (participating user)
    setupDeleverage(alice, alpha_token, alpha_token_whale, get_sgreen=True)
    alice_sgreen = savings_green.balanceOf(alice)
    performDeposit(alice, alice_sgreen, savings_green, alice, stability_pool)

    # Setup Bob with debt but NO stability pool deposits (not participating)
    setupDeleverage(bob, alpha_token, alpha_token_whale, get_sgreen=False)

    # Bob has GREEN but does NOT deposit to stability pool
    # Bob is NOT participating in stability pool vault

    # Configure priority stab vaults
    setup_priority_configs(
        priority_stab_assets=[
            (stability_pool, savings_green),
        ],
        priority_liq_assets=[]
    )

    # Bob has NO deposits in stability pool
    bob_sgreen_in_pool = stability_pool.getTotalAmountForUser(bob, savings_green)
    assert bob_sgreen_in_pool == 0, "Bob should have no sGREEN in stability pool"

    # Execute deleveraging
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Get events immediately
    burn_logs = filter_logs(teller, "StabAssetBurntDuringDeleverage")
    deleverage_logs = filter_logs(teller, "DeleverageUser")

    # Phase 1 skipped - NO burn events for Bob
    assert len(burn_logs) == 0, "Should have no burn events (Bob not participating in priority vault)"

    # Should still have DeleverageUser event (Phase 3 handled it)
    assert len(deleverage_logs) == 1, "Should have DeleverageUser event"

    # Verify deleverage still occurred via Phase 3
    log = deleverage_logs[0]
    assert log.user == bob
    assert repaid_amount > 0, "Should have repaid some debt via Phase 3"

    # Verify Alice's deposits were NOT affected
    alice_sgreen_after = stability_pool.getTotalAmountForUser(alice, savings_green)
    assert alice_sgreen_after == alice_sgreen, "Alice's deposits should be untouched"


def test_phase1_skips_non_green_stablecoin_assets(
    teller,
    bob,
    alpha_token,
    alpha_token_whale,
    savings_green,
    setupDeleverage,
    setup_priority_configs,
    performDeposit,
    stability_pool,
    setAssetConfig,
    createDebtTerms,
    switchboard_alpha,
):
    """
    Test that Phase 1 only processes GREEN/sGREEN assets and skips other
    assets in the stability pool (like alpha_token).

    Tests line 367: if config.shouldBurnAsPayment and _asset in [_a.greenToken, _a.savingsGreen]

    Flow:
    1. Configure alpha_token as a stability pool asset (non-GREEN stablecoin)
    2. User has alpha_token in stability pool
    3. User also has sGREEN in stability pool
    4. Phase 1 should ONLY burn sGREEN, skip alpha_token
    5. Alpha_token remains untouched in stability pool
    """
    # Configure alpha_token to work in BOTH simple vault (for collateral) and stability pool
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=60_00,
        _liqThreshold=70_00,
        _liqFee=10_00,
        _borrowRate=5_00,
    )
    setAssetConfig(
        alpha_token,
        _vaultIds=[1, 3],  # Stability pool AND simple vault
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,  # Not burnable in Phase 1
        _shouldTransferToEndaoment=False,
    )

    # Setup user with debt
    setupDeleverage(bob, alpha_token, alpha_token_whale,
                   borrow_amount=300 * EIGHTEEN_DECIMALS, get_sgreen=True)

    # User deposits sGREEN to stability pool
    bob_sgreen_balance = savings_green.balanceOf(bob)
    performDeposit(bob, bob_sgreen_balance, savings_green, bob, stability_pool)

    # Give user alpha_token and deposit to stability pool
    alpha_token.transfer(bob, 200 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, alpha_token, bob, stability_pool)

    # Configure priority: include both sGREEN and alpha_token
    setup_priority_configs(
        priority_stab_assets=[
            (stability_pool, savings_green),
            (stability_pool, alpha_token),  # Should be skipped in Phase 1
        ],
        priority_liq_assets=[]
    )

    # Get pre-deleverage state
    pre_sgreen = stability_pool.getTotalAmountForUser(bob, savings_green)
    pre_alpha = stability_pool.getTotalAmountForUser(bob, alpha_token)
    assert pre_sgreen > 0, "User should have sGREEN in pool"
    assert pre_alpha > 0, "User should have alpha_token in pool"

    # Execute deleveraging
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Get events immediately
    burn_logs = filter_logs(teller, "StabAssetBurntDuringDeleverage")

    # Should have exactly 1 burn event (only sGREEN)
    assert len(burn_logs) == 1, "Should have exactly 1 burn event"
    assert burn_logs[0].stabAsset == savings_green.address, "Only sGREEN should be burned"

    # Verify alpha_token was NOT touched (Phase 1 skipped it)
    post_alpha = stability_pool.getTotalAmountForUser(bob, alpha_token)
    assert post_alpha == pre_alpha, "Alpha_token should NOT be touched in Phase 1"

    # Verify sGREEN was burned
    post_sgreen = stability_pool.getTotalAmountForUser(bob, savings_green)
    assert post_sgreen < pre_sgreen, "sGREEN should be burned"

    # Verify debt was reduced
    assert repaid_amount > 0, "Should have repaid some debt"


def test_phase1_processes_multiple_stability_pools(
    teller,
    stability_pool,
    simple_erc20_vault,
    bob,
    alice,  # Use alice instead of charlie
    savings_green,
    green_token,
    alpha_token,
    alpha_token_whale,
    setupDeleverage,
    performDeposit,
    setup_priority_configs,
    credit_engine,
    setAssetConfig,
    createDebtTerms,
    _test,
    switchboard_alpha,
):
    """
    CRITICAL TEST: Verify Phase 1 correctly processes multiple stability pools.

    SCENARIO:
    - Configure 2 stability pools in priority order
    - User (bob) participates in pool 1, NOT in pool 2
    - Another user (alice) in pool 2 to verify no cross-contamination
    - Bob's pool 1 assets sufficient to cover debt

    EXPECTED:
    - Pool 1 processed (user participates, covers full debt)
    - Pool 2 SKIPPED (user doesn't participate)
    - Alice's assets untouched
    - Only 1 burn event

    VALIDATES: Lines 244-255 (multiple pool iteration and participation check)
    """
    # Configure GREEN token to be supported by simple_erc20_vault (vault ID 3)
    # This allows Alice to deposit GREEN there for the second pool
    setAssetConfig(green_token, _vaultIds=[1, 3], _debtTerms=createDebtTerms(), _shouldBurnAsPayment=True)
    # Setup bob with debt using alpha_token as collateral
    # Using standard borrow_amount=500 which creates 500 debt and yields 500 GREEN
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Bob borrowed GREEN, deposit some to stability pool (vault 1)
    green_balance = green_token.balanceOf(bob)
    assert green_balance == 500 * EIGHTEEN_DECIMALS, "Should have 500 GREEN"
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, green_token, bob, stability_pool)

    # Setup Alice with GREEN in simple_erc20_vault (vault 3) - Alice needs to borrow her own GREEN
    setupDeleverage(
        alice,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )
    alice_green = green_token.balanceOf(alice)
    assert alice_green == 500 * EIGHTEEN_DECIMALS
    # Alice deposits her GREEN to simple_erc20_vault using performDeposit fixture
    performDeposit(alice, 500 * EIGHTEEN_DECIMALS, green_token, alice, simple_erc20_vault)

    # Add more GREEN to stability pool (simulating different priority)
    # Bob has 300 GREEN remaining, deposit it
    performDeposit(bob, 300 * EIGHTEEN_DECIMALS, green_token, bob, stability_pool)

    # Configure multiple pools with priority order
    # Bob has 500 GREEN total in stability pool, Alice has 500 in simple_erc20_vault
    setup_priority_configs(
        priority_stab_assets=[
            (stability_pool, green_token),     # Priority 1: Bob has 500 GREEN total
            (simple_erc20_vault, green_token), # Priority 2: Alice has 500, Bob has 0
        ]
    )

    # Track balances before
    pre_bob_green_stab = stability_pool.getTotalAmountForUser(bob, green_token)
    pre_alice_green_vault = simple_erc20_vault.getTotalAmountForUser(alice, green_token)
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount

    # Verify initial state
    assert pre_bob_green_stab == 500 * EIGHTEEN_DECIMALS  # 200 + 300 deposited
    assert pre_alice_green_vault == 500 * EIGHTEEN_DECIMALS
    # Note: Bob borrowed 600 but only received 500 GREEN due to fees, however debt is still 500 not 600
    # The borrow amount includes fees, but the actual debt recorded is the net amount
    assert pre_debt == 500 * EIGHTEEN_DECIMALS

    # Deleverage bob
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Get burn events
    burn_logs = filter_logs(teller, "StabAssetBurntDuringDeleverage")

    # Track balances after
    post_bob_green_stab = stability_pool.getTotalAmountForUser(bob, green_token)
    post_alice_green_vault = simple_erc20_vault.getTotalAmountForUser(alice, green_token)
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount

    # CRITICAL ASSERTIONS:

    # 1. Should have exactly 1 burn event (pool 2 skipped, only pool 1 processed)
    assert len(burn_logs) == 1, f"Expected 1 burn (pool 2 skipped), got {len(burn_logs)}"

    # 2. Only burn: GREEN from pool 1 (500 burned, partial debt coverage)
    assert burn_logs[0].stabAsset == green_token.address
    assert burn_logs[0].vaultId == 1  # stability_pool
    assert burn_logs[0].amountBurned == 500 * EIGHTEEN_DECIMALS
    assert burn_logs[0].isDepleted == True  # All depleted

    # 4. Alice's assets in pool 2 UNTOUCHED (critical)
    assert post_alice_green_vault == pre_alice_green_vault, "Alice's assets should be untouched"

    # 5. Bob's balances updated correctly
    assert post_bob_green_stab == 0, "Bob's GREEN should be fully depleted"

    # 6. Debt fully repaid (500 GREEN covers 500 debt completely)
    assert post_debt == 0, "Debt should be fully repaid"
    _test(repaid_amount, 500 * EIGHTEEN_DECIMALS)


def test_phase1_exact_balance_equals_target(
    teller,
    stability_pool,
    bob,
    green_token,
    alpha_token,
    alpha_token_whale,
    setupDeleverage,
    performDeposit,
    setup_priority_configs,
    credit_engine,
    _test,
    switchboard_alpha,
):
    """
    Test Phase 1 when user balance EXACTLY equals debt amount.

    SCENARIO:
    - User has exactly 500 GREEN in stability pool
    - User has exactly 500 GREEN debt
    - No surplus, no deficit

    EXPECTED:
    - Exactly 500 GREEN burned
    - Position fully depleted (isDepleted=True)
    - Debt reduced to exactly 0
    - No remainder, no rounding issues

    VALIDATES: Edge case of exact match, rounding behavior
    """
    # Setup user with debt using alpha_token as collateral
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1000 * EIGHTEEN_DECIMALS,
        borrow_amount=500 * EIGHTEEN_DECIMALS,
        get_sgreen=False,
    )

    # Bob already has borrowed GREEN, deposit EXACTLY 500 GREEN to stability pool
    green_balance = green_token.balanceOf(bob)
    assert green_balance >= 500 * EIGHTEEN_DECIMALS, "Should have at least 500 GREEN"
    performDeposit(bob, 500 * EIGHTEEN_DECIMALS, green_token, bob, stability_pool)

    # Configure Phase 1
    setup_priority_configs(
        priority_stab_assets=[(stability_pool, green_token)]
    )

    # Track balances
    pre_green = stability_pool.getTotalAmountForUser(bob, green_token)
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount

    # Verify exact match
    assert pre_green == 500 * EIGHTEEN_DECIMALS, "Should have exactly 500 GREEN"
    assert pre_debt == 500 * EIGHTEEN_DECIMALS, "Should have exactly 500 debt"

    # Deleverage
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Get burn event
    burn_logs = filter_logs(teller, "StabAssetBurntDuringDeleverage")

    # Post balances
    post_green = stability_pool.getTotalAmountForUser(bob, green_token)
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount

    # CRITICAL ASSERTIONS for exact match:

    # 1. Exactly one burn event
    assert len(burn_logs) == 1, "Should have exactly 1 burn"

    # 2. Burned exactly the debt amount
    assert burn_logs[0].amountBurned == 500 * EIGHTEEN_DECIMALS, "Should burn exactly 500"
    assert burn_logs[0].usdValue == 500 * EIGHTEEN_DECIMALS, "USD value should be exactly 500"

    # 3. Position fully depleted
    assert burn_logs[0].isDepleted == True, "Position should be fully depleted"

    # 4. Balances exactly zero
    assert post_green == 0, "GREEN balance should be exactly 0"
    assert post_debt == 0, "Debt should be exactly 0"

    # 5. Repaid amount exact
    _test(repaid_amount, 500 * EIGHTEEN_DECIMALS)


def test_phase1_handles_dust_amounts(
    teller,
    stability_pool,
    bob,
    green_token,
    alpha_token,
    alpha_token_whale,
    setupDeleverage,
    performDeposit,
    setup_priority_configs,
    credit_engine,
    _test,
    switchboard_alpha,
):
    """
    Test Phase 1 with extremely small (dust) amounts.

    SCENARIO:
    - User has 1000 GREEN as collateral (for borrowing)
    - User has only 1 wei debt (smallest possible)
    - User has 1000 GREEN in stability pool

    EXPECTED:
    - Exactly 1 wei burned
    - No reverts or underflows
    - Correct event emission
    - No rounding errors

    VALIDATES: Handling of minimum amounts, rounding behavior
    """
    # Setup user with minimal debt (1 wei) using alpha_token as collateral
    setupDeleverage(
        bob,
        alpha_token,
        alpha_token_whale,
        deposit_amount=1000 * EIGHTEEN_DECIMALS,
        borrow_amount=1,  # 1 wei debt
        get_sgreen=False,
    )

    # Bob already has borrowed GREEN, deposit it to stability pool
    green_balance = green_token.balanceOf(bob)
    assert green_balance > 0, "Should have some GREEN from borrowing"
    performDeposit(bob, green_balance, green_token, bob, stability_pool)

    # Configure Phase 1
    setup_priority_configs(
        priority_stab_assets=[(stability_pool, green_token)]
    )

    # Track balances
    pre_green = stability_pool.getTotalAmountForUser(bob, green_token)
    pre_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount

    assert pre_green == 1, "Should have 1 wei GREEN from 1 wei borrow"
    assert pre_debt == 1, "Should have 1 wei debt"

    # Deleverage
    repaid_amount = teller.deleverageUser(bob, 0, sender=switchboard_alpha.address)

    # Get burn event
    burn_logs = filter_logs(teller, "StabAssetBurntDuringDeleverage")

    # Post balances
    post_green = stability_pool.getTotalAmountForUser(bob, green_token)
    post_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount

    # Assertions for dust amount:

    # 1. One burn event
    assert len(burn_logs) == 1

    # 2. Burned exactly 1 wei
    assert burn_logs[0].amountBurned == 1, "Should burn exactly 1 wei"
    assert burn_logs[0].usdValue == 1, "USD value should be 1 wei"

    # 3. Position fully depleted (only had 1 wei)
    assert burn_logs[0].isDepleted == True

    # 4. Correct balance changes
    assert post_green == 0, "Should be 0 after burning 1 wei"
    assert post_debt == 0, "Debt should be 0"

    # 5. Repaid exactly 1 wei
    _test(repaid_amount, 1)

