import boa
import pytest

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS
from conf_utils import filter_logs


POSITION = 100 * EIGHTEEN_DECIMALS
DEBT = 10 * EIGHTEEN_DECIMALS
CONTROL_WITHDRAWAL = EIGHTEEN_DECIMALS


def _setup_victim(
    victim,
    teller,
    vault_book,
    vault,
    asset,
    asset_whale,
    mock_price_source,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    performDeposit,
):
    setGeneralConfig()
    setGeneralDebtConfig()
    setAssetConfig(asset)
    performDeposit(victim, POSITION, asset, asset_whale, vault)
    mock_price_source.setPrice(asset, EIGHTEEN_DECIMALS)
    assert teller.borrow(DEBT, victim, False, False, sender=victim) == DEBT
    vault_id = vault_book.getRegId(vault)
    assert vault_id != 0
    return vault_id


def _start_fresh_action_block(mission_control, switchboard_alpha, ledger, subject):
    boa.env.time_travel(blocks=1)
    mission_control.setShouldCheckLastTouch(
        True,
        sender=switchboard_alpha.address,
    )
    action_block = boa.env.evm.patch.block_number
    assert ledger.lastTouch(subject) != action_block
    return action_block


def _higher_risk_control(teller, subject, asset, vault, vault_id):
    return teller.withdraw(
        asset,
        CONTROL_WITHDRAWAL,
        subject,
        vault,
        vault_id,
        sender=subject,
    )


def _permission_tuple(mission_control, user):
    config = mission_control.userConfig(user)
    return (
        config.canAnyoneDeposit,
        config.canAnyoneRepayDebt,
        config.canAnyoneBondForUser,
    )


@pytest.mark.parametrize(
    ("args", "expected"),
    (
        pytest.param((), (False, False, False), id="no-arguments"),
        pytest.param((True,), (True, False, False), id="deposit-only"),
        pytest.param((True, True), (True, True, False), id="deposit-and-repay"),
        pytest.param((True, True, True), (True, True, True), id="all-explicit"),
    ),
)
def test_set_user_config_defaults_are_fail_closed(
    args,
    expected,
    teller,
    mission_control,
    bob,
):
    assert teller.setUserConfig(bob, *args, sender=bob)
    assert _permission_tuple(mission_control, bob) == expected


def test_set_undy_lego_access_keeps_explicit_all_true_permissions(
    teller,
    mission_control,
    switchboard_alpha,
    mock_undy_v2,
    bob,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_undy_v2.setAllAddressesAreVaults(True)

    assert teller.setUndyLegoAccess(bob, sender=mock_undy_v2.address)
    assert _permission_tuple(mission_control, mock_undy_v2.address) == (
        True,
        True,
        True,
    )
    delegation = mission_control.userDelegation(mock_undy_v2.address, bob)
    assert (
        delegation.canWithdraw,
        delegation.canBorrow,
        delegation.canClaimFromStabPool,
        delegation.canClaimLoot,
    ) == (True, True, True, True)


ONE_WEI_ROUTES = (
    pytest.param("deposit", id="deposit"),
    pytest.param("depositMany", id="deposit-many"),
    pytest.param(
        "convertToSavingsGreenAndDepositIntoStabPool",
        id="convert-and-deposit",
    ),
    pytest.param("repay", id="repay"),
)


def _invoke_one_wei_route(route, teller, caller, victim, asset, vault, vault_id):
    if route == "deposit":
        return teller.deposit(asset, 1, victim, vault, vault_id, sender=caller)
    if route == "depositMany":
        return teller.depositMany(
            victim,
            [(asset.address, 1, vault.address, vault_id)],
            sender=caller,
        )
    if route == "convertToSavingsGreenAndDepositIntoStabPool":
        return teller.convertToSavingsGreenAndDepositIntoStabPool(
            victim,
            1,
            sender=caller,
        )
    if route == "repay":
        return teller.repay(1, victim, False, True, sender=caller)
    raise AssertionError(route)


@pytest.mark.parametrize("route", ONE_WEI_ROUTES)
def test_one_wei_routes_preserve_self_touch_but_suppress_authorized_helper_touch(
    route,
    teller,
    ledger,
    mission_control,
    switchboard_alpha,
    vault_book,
    simple_erc20_vault,
    stability_pool,
    alpha_token,
    alpha_token_whale,
    green_token,
    savings_green,
    whale,
    mock_price_source,
    bob,
    sally,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    performDeposit,
):
    victim = bob
    helper = sally
    vault_id = _setup_victim(
        victim,
        teller,
        vault_book,
        simple_erc20_vault,
        alpha_token,
        alpha_token_whale,
        mock_price_source,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        performDeposit,
    )
    if route == "convertToSavingsGreenAndDepositIntoStabPool":
        stab_vault_id = vault_book.getRegId(stability_pool)
        assert stab_vault_id == mission_control.preferredStabVaultId()
        setAssetConfig(savings_green, _vaultIds=[stab_vault_id])

    payment_asset = (
        green_token
        if route in ("convertToSavingsGreenAndDepositIntoStabPool", "repay")
        else alpha_token
    )
    payment_whale = whale if payment_asset == green_token else alpha_token_whale
    action_block = _start_fresh_action_block(
        mission_control,
        switchboard_alpha,
        ledger,
        victim,
    )

    # A self-performed low-risk action still arms the action block.
    with boa.env.anchor():
        payment_asset.transfer(victim, 1, sender=payment_whale)
        payment_asset.approve(teller, 1, sender=victim)
        _invoke_one_wei_route(
            route,
            teller,
            victim,
            victim,
            alpha_token,
            simple_erc20_vault,
            vault_id,
        )
        assert ledger.lastTouch(victim) == action_block
        with boa.reverts("one action per block"):
            _higher_risk_control(
                teller,
                victim,
                alpha_token,
                simple_erc20_vault,
                vault_id,
            )

    # Explicitly open only the capability needed by this helper route.
    if route == "repay":
        teller.setUserConfig(victim, False, True, False, sender=victim)
    else:
        teller.setUserConfig(victim, True, False, False, sender=victim)
    payment_asset.transfer(helper, 1, sender=payment_whale)
    payment_asset.approve(teller, 1, sender=helper)
    touch_before = ledger.lastTouch(victim)

    result = _invoke_one_wei_route(
        route,
        teller,
        helper,
        victim,
        alpha_token,
        simple_erc20_vault,
        vault_id,
    )
    assert result
    assert ledger.lastTouch(victim) == touch_before
    assert ledger.lastTouch(victim) != action_block
    assert _higher_risk_control(
        teller,
        victim,
        alpha_token,
        simple_erc20_vault,
        vault_id,
    ) == CONTROL_WITHDRAWAL
    assert ledger.lastTouch(victim) == action_block


@pytest.mark.parametrize(
    ("safety_gate", "reason"),
    (
        pytest.param("paused", "not activated", id="ledger-paused"),
        pytest.param("locked", "account locked", id="beneficiary-locked"),
    ),
)
def test_suppressed_touch_still_enforces_ledger_safety_gates_atomically(
    safety_gate,
    reason,
    teller,
    ledger,
    switchboard_alpha,
    vault_book,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    green_token,
    whale,
    mock_price_source,
    bob,
    sally,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    performDeposit,
):
    _setup_victim(
        bob,
        teller,
        vault_book,
        simple_erc20_vault,
        alpha_token,
        alpha_token_whale,
        mock_price_source,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        performDeposit,
    )
    teller.setUserConfig(bob, False, True, False, sender=bob)
    green_token.transfer(sally, 1, sender=whale)
    green_token.approve(teller, 1, sender=sally)
    if safety_gate == "paused":
        ledger.pause(True, sender=switchboard_alpha.address)
    else:
        ledger.setLockedAccount(bob, True, sender=switchboard_alpha.address)

    before = (
        ledger.lastTouch(bob),
        ledger.userDebt(bob).amount,
        green_token.balanceOf(sally),
        green_token.allowance(sally, teller),
    )
    with boa.reverts(reason):
        # Repay reaches suppressed-touch housekeeping before its first payment
        # or other Ledger interaction, so this revert can only originate from
        # the safety assertions on that branch.
        teller.repay(1, bob, False, True, sender=sally)
    assert (
        ledger.lastTouch(bob),
        ledger.userDebt(bob).amount,
        green_token.balanceOf(sally),
        green_token.allowance(sally, teller),
    ) == before


def test_delegated_zero_payout_claim_preserves_housekeeping_without_victim_touch(
    teller,
    ledger,
    lootbox,
    mission_control,
    switchboard_alpha,
    vault_book,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    ripe_token,
    mock_price_source,
    bob,
    sally,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
):
    setRipeRewardsConfig(_arePointsEnabled=True, _ripePerBlock=0)
    vault_id = _setup_victim(
        bob,
        teller,
        vault_book,
        simple_erc20_vault,
        alpha_token,
        alpha_token_whale,
        mock_price_source,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        performDeposit,
    )
    assert teller.setUserDelegation(
        sally,
        bob,
        False,
        False,
        False,
        True,
        sender=bob,
    )
    assert mission_control.getClaimLootConfig(
        bob,
        sally,
        ripe_token,
    ).canClaimLootForUser
    assert lootbox.getClaimableLoot(bob) == 0
    boa.env.time_travel(seconds=24 * 60 * 60)
    action_block = _start_fresh_action_block(
        mission_control,
        switchboard_alpha,
        ledger,
        bob,
    )
    debt_before = ledger.userDebt(bob)
    borrow_points_before = ledger.getBorrowPointsBundle(bob)
    deposit_points_before = ledger.getDepositPointsBundle(
        bob,
        vault_id,
        alpha_token,
    )
    balance_before = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    touch_before = ledger.lastTouch(bob)

    assert teller.claimLoot(bob, False, sender=sally) == 0

    debt_after = ledger.userDebt(bob)
    borrow_points_after = ledger.getBorrowPointsBundle(bob)
    deposit_points_after = ledger.getDepositPointsBundle(bob, vault_id, alpha_token)
    assert ledger.lastTouch(bob) == touch_before
    assert ledger.lastTouch(bob) != action_block
    assert debt_after.amount > debt_before.amount
    assert debt_after.principal == debt_before.principal
    assert borrow_points_after.userPoints != borrow_points_before.userPoints
    assert deposit_points_after.userPoints != deposit_points_before.userPoints
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == balance_before
    assert _higher_risk_control(
        teller,
        bob,
        alpha_token,
        simple_erc20_vault,
        vault_id,
    ) == CONTROL_WITHDRAWAL


def test_real_bond_is_fail_closed_then_bond_only_and_does_not_touch_recipient(
    teller,
    ledger,
    bond_room,
    mission_control,
    switchboard_alpha,
    switchboard_delta,
    vault_book,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    ripe_token,
    mock_price_source,
    bob,
    sally,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    performDeposit,
):
    vault_id = _setup_victim(
        bob,
        teller,
        vault_book,
        simple_erc20_vault,
        alpha_token,
        alpha_token_whale,
        mock_price_source,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        performDeposit,
    )
    one_unit = 10 ** alpha_token.decimals()
    mission_control.setRipeBondConfig(
        (
            alpha_token.address,
            10 * one_unit,
            True,
            EIGHTEEN_DECIMALS,
            EIGHTEEN_DECIMALS,
            0,
            100,
            False,
            0,
        ),
        sender=switchboard_delta.address,
    )
    bond_room.refreshBondEpoch(sender=switchboard_delta.address)
    alpha_token.transfer(sally, one_unit, sender=alpha_token_whale)
    alpha_token.approve(teller, one_unit, sender=sally)
    action_block = _start_fresh_action_block(
        mission_control,
        switchboard_alpha,
        ledger,
        bob,
    )

    assert teller.setUserConfig(sender=bob)
    assert _permission_tuple(mission_control, bob) == (False, False, False)
    with boa.reverts("cannot bond for user"):
        teller.purchaseRipeBond(alpha_token, one_unit, 0, bob, sender=sally)

    assert teller.setUserConfig(bob, False, False, True, sender=bob)
    assert _permission_tuple(mission_control, bob) == (False, False, True)
    ripe_before = ripe_token.balanceOf(bob)
    touch_before = ledger.lastTouch(bob)
    payout = teller.purchaseRipeBond(
        alpha_token,
        one_unit,
        0,
        bob,
        sender=sally,
    )
    assert payout == EIGHTEEN_DECIMALS
    assert ripe_token.balanceOf(bob) == ripe_before + payout
    assert ledger.lastTouch(bob) == touch_before
    assert ledger.lastTouch(bob) != action_block
    assert _higher_risk_control(
        teller,
        bob,
        alpha_token,
        simple_erc20_vault,
        vault_id,
    ) == CONTROL_WITHDRAWAL


def test_delegated_withdraw_remains_always_touch(
    teller,
    ledger,
    mission_control,
    switchboard_alpha,
    vault_book,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    mock_price_source,
    bob,
    sally,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    performDeposit,
):
    vault_id = _setup_victim(
        bob,
        teller,
        vault_book,
        simple_erc20_vault,
        alpha_token,
        alpha_token_whale,
        mock_price_source,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        performDeposit,
    )
    teller.setUserDelegation(
        sally,
        bob,
        True,
        False,
        False,
        False,
        sender=bob,
    )
    action_block = _start_fresh_action_block(
        mission_control,
        switchboard_alpha,
        ledger,
        bob,
    )
    assert teller.withdraw(
        alpha_token,
        1,
        bob,
        simple_erc20_vault,
        vault_id,
        sender=sally,
    ) == 1
    assert ledger.lastTouch(bob) == action_block
    assert ledger.lastTouch(sally) != action_block


@pytest.mark.parametrize("route", ("liquidateManyUsers", "claimLootForManyUsers"))
def test_nonempty_caller_only_routes_touch_caller_not_listed_users(
    route,
    teller,
    ledger,
    lootbox,
    mission_control,
    switchboard_alpha,
    vault_book,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
):
    setGeneralConfig()
    if route == "claimLootForManyUsers":
        setAssetConfig(alpha_token)
        setRipeRewardsConfig()
        performDeposit(
            bob,
            POSITION,
            alpha_token,
            alpha_token_whale,
            simple_erc20_vault,
        )
        boa.env.time_travel(blocks=20)
        vault_id = vault_book.getRegId(simple_erc20_vault)
        lootbox.updateDepositPoints(
            bob,
            vault_id,
            simple_erc20_vault,
            alpha_token,
            sender=teller.address,
        )
        assert teller.setUserDelegation(
            sally,
            bob,
            False,
            False,
            False,
            True,
            sender=bob,
        )
        assert lootbox.getClaimableLoot(bob) > 0

    action_block = _start_fresh_action_block(
        mission_control,
        switchboard_alpha,
        ledger,
        bob,
    )
    if route == "liquidateManyUsers":
        assert teller.liquidateManyUsers([bob], False, sender=sally) == 0
    else:
        assert teller.claimLootForManyUsers([bob], False, sender=sally) > 0
    assert ledger.lastTouch(sally) == action_block
    assert ledger.lastTouch(bob) != action_block


def test_external_housekeeping_wrapper_authorization_is_unchanged(
    teller,
    ledger,
    mission_control,
    switchboard_alpha,
    deleverage,
    bob,
    sally,
):
    action_block = _start_fresh_action_block(
        mission_control,
        switchboard_alpha,
        ledger,
        bob,
    )
    with boa.reverts("only ripe addr allowed"):
        teller.performHousekeeping(False, bob, False, sender=sally)
    assert ledger.lastTouch(bob) != action_block
    teller.performHousekeeping(False, bob, False, sender=deleverage.address)
    assert ledger.lastTouch(bob) == action_block


def _configure_ripe_gov_vault(
    mission_control,
    switchboard_alpha,
    setAssetConfig,
    ripe_token,
):
    mission_control.setRipeGovVaultConfig(
        ripe_token,
        100_00,
        False,
        (100, 1000, 200_00, True, 10_00),
        sender=switchboard_alpha.address,
    )
    setAssetConfig(ripe_token, _vaultIds=[2])


def test_real_gov_vault_shared_deposit_self_vs_authorized_helper(
    teller,
    ledger,
    mission_control,
    switchboard_alpha,
    vault_book,
    simple_erc20_vault,
    ripe_gov_vault,
    alpha_token,
    alpha_token_whale,
    ripe_token,
    whale,
    mock_price_source,
    mock_undy_v2,
    bob,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    performDeposit,
):
    vault_id = _setup_victim(
        bob,
        teller,
        vault_book,
        simple_erc20_vault,
        alpha_token,
        alpha_token_whale,
        mock_price_source,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        performDeposit,
    )
    _configure_ripe_gov_vault(
        mission_control,
        switchboard_alpha,
        setAssetConfig,
        ripe_token,
    )
    mock_price_source.setPrice(ripe_token, EIGHTEEN_DECIMALS)
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    # Recognize only the helper as an Underscore vault. Keeping Bob ordinary is
    # essential: otherwise Ledger intentionally exempts him from action-block
    # enforcement and the self-call contrast would be a false negative.
    mock_undy_v2.setAllAddressesAreVaults(False)
    mock_undy_v2.setEarnVault(mock_undy_v2.address, True)
    amount = EIGHTEEN_DECIMALS
    action_block = _start_fresh_action_block(
        mission_control,
        switchboard_alpha,
        ledger,
        bob,
    )

    with boa.env.anchor():
        ripe_token.transfer(bob, amount, sender=whale)
        ripe_token.approve(teller, amount, sender=bob)
        assert teller.depositIntoGovVault(
            ripe_token,
            amount,
            500,
            bob,
            sender=bob,
        ) == amount
        assert ledger.lastTouch(bob) == action_block
        with boa.reverts("one action per block"):
            teller.borrow(DEBT, bob, False, False, sender=bob)

    ripe_token.transfer(mock_undy_v2, amount, sender=whale)
    ripe_token.approve(teller, amount, sender=mock_undy_v2.address)
    touch_before = ledger.lastTouch(bob)
    assert teller.depositIntoGovVault(
        ripe_token,
        amount,
        500,
        bob,
        sender=mock_undy_v2.address,
    ) == amount
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == amount
    assert ledger.lastTouch(bob) == touch_before
    assert ledger.lastTouch(bob) != action_block
    assert teller.borrow(DEBT, bob, False, False, sender=bob) == DEBT


def test_adjust_lock_real_path_remains_always_touch(
    teller,
    ledger,
    mission_control,
    switchboard_alpha,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
):
    setGeneralConfig()
    _configure_ripe_gov_vault(
        mission_control,
        switchboard_alpha,
        setAssetConfig,
        ripe_token,
    )
    amount = EIGHTEEN_DECIMALS
    ripe_token.transfer(ripe_gov_vault, amount, sender=whale)
    assert ripe_gov_vault.depositTokensInVault(
        bob,
        ripe_token,
        amount,
        sender=teller.address,
    ) == amount
    action_block = _start_fresh_action_block(
        mission_control,
        switchboard_alpha,
        ledger,
        bob,
    )
    teller.adjustLock(ripe_token, 800, bob, sender=bob)
    assert ripe_gov_vault.userGovData(bob, ripe_token).unlock == action_block + 800
    assert ledger.lastTouch(bob) == action_block


def test_real_stability_redemption_helper_does_not_touch_recipient(
    teller,
    ledger,
    mission_control,
    switchboard_alpha,
    vault_book,
    simple_erc20_vault,
    stability_pool,
    auction_house,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    savings_green,
    whale,
    mock_price_source,
    bob,
    sally,
    alice,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    performDeposit,
):
    control_vault_id = _setup_victim(
        bob,
        teller,
        vault_book,
        simple_erc20_vault,
        alpha_token,
        alpha_token_whale,
        mock_price_source,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        performDeposit,
    )
    setAssetConfig(bravo_token)
    for token in (alpha_token, bravo_token, green_token):
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(
        alice,
        alpha_token,
        deposit_amount,
        sender=teller.address,
    )
    claimable = 50 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        deposit_amount,
        bravo_token,
        claimable,
        ZERO_ADDRESS,
        alpha_token,
        savings_green,
        sender=auction_house.address,
    )
    teller.setUserConfig(bob, True, False, False, sender=bob)
    green_token.transfer(sally, claimable, sender=whale)
    green_token.approve(teller, claimable, sender=sally)
    action_block = _start_fresh_action_block(
        mission_control,
        switchboard_alpha,
        ledger,
        bob,
    )
    touch_before = ledger.lastTouch(bob)
    bob_balance_before = bravo_token.balanceOf(bob)
    stab_vault_id = vault_book.getRegId(stability_pool)

    spent = teller.redeemManyFromStabilityPool(
        stab_vault_id,
        [(bravo_token.address, claimable)],
        claimable,
        bob,
        False,
        False,
        True,
        sender=sally,
    )
    assert spent == claimable
    assert bravo_token.balanceOf(bob) == bob_balance_before + claimable
    assert ledger.lastTouch(bob) == touch_before
    assert ledger.lastTouch(bob) != action_block
    assert _higher_risk_control(
        teller,
        bob,
        alpha_token,
        simple_erc20_vault,
        control_vault_id,
    ) == CONTROL_WITHDRAWAL


def test_real_collateral_redemption_helper_does_not_touch_recipient(
    teller,
    ledger,
    mission_control,
    switchboard_alpha,
    vault_book,
    simple_erc20_vault,
    credit_engine,
    alpha_token,
    alpha_token_whale,
    green_token,
    whale,
    mock_price_source,
    bob,
    sally,
    alice,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    performDeposit,
    createDebtTerms,
):
    setGeneralConfig()
    setGeneralDebtConfig()
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=70_00,
        _liqThreshold=80_00,
        _borrowRate=0,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    performDeposit(bob, POSITION, alpha_token, alpha_token_whale)
    performDeposit(alice, 200 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    assert teller.borrow(100 * EIGHTEEN_DECIMALS, alice, False, sender=alice)
    mock_price_source.setPrice(alpha_token, 70 * EIGHTEEN_DECIMALS // 100)
    assert credit_engine.canRedeemUserCollateral(alice)
    teller.setUserConfig(bob, True, False, False, sender=bob)
    payment = 20 * EIGHTEEN_DECIMALS
    green_token.transfer(sally, payment, sender=whale)
    green_token.approve(teller, payment, sender=sally)
    action_block = _start_fresh_action_block(
        mission_control,
        switchboard_alpha,
        ledger,
        bob,
    )
    touch_before = ledger.lastTouch(bob)
    balance_before = alpha_token.balanceOf(bob)
    vault_id = vault_book.getRegId(simple_erc20_vault)

    spent = teller.redeemCollateralFromMany(
        [(alice, vault_id, alpha_token.address, payment)],
        payment,
        False,
        False,
        True,
        bob,
        sender=sally,
    )
    assert spent == payment
    assert alpha_token.balanceOf(bob) > balance_before
    assert ledger.lastTouch(bob) == touch_before
    assert ledger.lastTouch(bob) != action_block
    assert _higher_risk_control(
        teller,
        bob,
        alpha_token,
        simple_erc20_vault,
        vault_id,
    ) == CONTROL_WITHDRAWAL


def test_real_auction_helper_does_not_touch_recipient(
    teller,
    ledger,
    mission_control,
    switchboard_alpha,
    vault_book,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    green_token,
    whale,
    mock_price_source,
    bob,
    sally,
    alice,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    performDeposit,
    createDebtTerms,
):
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _liqThreshold=80_00,
        _liqFee=10_00,
        _borrowRate=0,
    )
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=True,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
    performDeposit(bob, POSITION, alpha_token, alpha_token_whale)
    performDeposit(alice, 200 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    assert teller.borrow(100 * EIGHTEEN_DECIMALS, alice, False, sender=alice)
    mock_price_source.setPrice(alpha_token, 625 * EIGHTEEN_DECIMALS // 1000)
    teller.liquidateUser(alice, False, sender=sally)
    auction = filter_logs(teller, "FungibleAuctionUpdated")[0]
    teller.setUserConfig(bob, True, False, False, sender=bob)
    payment = 10 * EIGHTEEN_DECIMALS
    green_token.transfer(sally, payment, sender=whale)
    green_token.approve(teller, payment, sender=sally)
    action_block = _start_fresh_action_block(
        mission_control,
        switchboard_alpha,
        ledger,
        bob,
    )
    touch_before = ledger.lastTouch(bob)
    balance_before = alpha_token.balanceOf(bob)
    vault_id = vault_book.getRegId(simple_erc20_vault)

    spent = teller.buyManyFungibleAuctions(
        [(auction.liqUser, auction.vaultId, auction.asset, payment)],
        payment,
        False,
        False,
        True,
        bob,
        sender=sally,
    )
    # Real auction math can round the capped payment down by a wei.
    assert 0 < spent <= payment
    assert alpha_token.balanceOf(bob) > balance_before
    assert ledger.lastTouch(bob) == touch_before
    assert ledger.lastTouch(bob) != action_block
    assert _higher_risk_control(
        teller,
        bob,
        alpha_token,
        simple_erc20_vault,
        vault_id,
    ) == CONTROL_WITHDRAWAL
