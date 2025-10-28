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
    repaid_amount = deleverage.deleverageUser(bob, bob, 0, sender=teller.address)

    # events
    logDetail = filter_logs(deleverage, "StabAssetBurntDuringDeleverage")[0]
    log = filter_logs(deleverage, "DeleverageUser")[0]

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
    assert log.caller == bob
    assert log.targetRepayAmount == pre_debt
    assert log.repaidAmount == repaid_amount
    assert log.hasGoodDebtHealth == True


def test_phase1_burns_users_green_from_stability_pool(
    deleverage,
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
    repaid_amount = deleverage.deleverageUser(bob, bob, 0, sender=teller.address)

    # events
    logDetail = filter_logs(deleverage, "StabAssetBurntDuringDeleverage")[0]
    log = filter_logs(deleverage, "DeleverageUser")[0]

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
    assert log.caller == bob
    assert log.targetRepayAmount == pre_debt
    assert log.repaidAmount == repaid_amount
    assert log.hasGoodDebtHealth == True


def test_phase1_partial_burn_when_sgreen_exceeds_debt(
    deleverage,
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
    repaid_amount = deleverage.deleverageUser(bob, bob, 0, sender=teller.address)

    # Get events immediately
    logDetail = filter_logs(deleverage, "StabAssetBurntDuringDeleverage")[0]
    log = filter_logs(deleverage, "DeleverageUser")[0]

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
    repaid_amount = deleverage.deleverageUser(bob, bob, 0, sender=teller.address)

    # Get events
    logDetail = filter_logs(deleverage, "StabAssetBurntDuringDeleverage")[0]
    log = filter_logs(deleverage, "DeleverageUser")[0]

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
    deleverage,
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
    repaid_amount = deleverage.deleverageUser(bob, bob, 400 * EIGHTEEN_DECIMALS, sender=teller.address)

    # Get events immediately
    burn_logs = filter_logs(deleverage, "StabAssetBurntDuringDeleverage")

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
    deleverage,
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
    repaid_amount = deleverage.deleverageUser(bob, bob, target_repay, sender=teller.address)

    # Get events
    logDetail = filter_logs(deleverage, "StabAssetBurntDuringDeleverage")[0]
    log = filter_logs(deleverage, "DeleverageUser")[0]

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
    deleverage,
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
    repaid_amount = deleverage.deleverageUser(bob, bob, 0, sender=teller.address)

    # Get events
    burn_logs = filter_logs(deleverage, "StabAssetBurntDuringDeleverage")
    log = filter_logs(deleverage, "DeleverageUser")[0]

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
    deleverage,
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
    repaid_amount = deleverage.deleverageUser(bob, bob, 0, sender=teller.address)

    # Get events
    burn_logs = filter_logs(deleverage, "StabAssetBurntDuringDeleverage")

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
    deleverage,
    teller,
    bob,
    alpha_token,
    alpha_token_whale,
    savings_green,
    setupDeleverage,
    setup_priority_configs,
    setAssetConfig,
    createDebtTerms,
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
    repaid_amount = deleverage.deleverageUser(bob, bob, 0, sender=teller.address)

    # Get events immediately
    burn_logs = filter_logs(deleverage, "StabAssetBurntDuringDeleverage")
    deleverage_logs = filter_logs(deleverage, "DeleverageUser")

    # Phase 1 skipped - NO burn events
    assert len(burn_logs) == 0, "Should have no burn events (Phase 1 skipped)"

    # Should still have DeleverageUser event (Phase 3 handled it)
    assert len(deleverage_logs) == 1, "Should have DeleverageUser event"

    # Verify deleverage still occurred via Phase 3
    log = deleverage_logs[0]
    assert log.user == bob
    assert repaid_amount > 0, "Should have repaid some debt via Phase 3"


def test_phase1_user_not_participating_in_any_priority_vault(
    deleverage,
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
    repaid_amount = deleverage.deleverageUser(bob, bob, 0, sender=teller.address)

    # Get events immediately
    burn_logs = filter_logs(deleverage, "StabAssetBurntDuringDeleverage")
    deleverage_logs = filter_logs(deleverage, "DeleverageUser")

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
    deleverage,
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
    repaid_amount = deleverage.deleverageUser(bob, bob, 0, sender=teller.address)

    # Get events immediately
    burn_logs = filter_logs(deleverage, "StabAssetBurntDuringDeleverage")

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

