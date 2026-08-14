import json

import boa
import pytest

from conf_utils import filter_logs, set_full_payoff_params
from config.robinhood_launch import (
    DELEVERAGE_FULL_PAYOFF_BUFFER as ROBINHOOD_FULL_PAYOFF_BUFFER,
)
from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS


HUNDRED_PERCENT = 100_00
SIX_DECIMALS = 10**6
UNDERSCORE_LEGO_BOOK_ID = 3


@pytest.fixture(autouse=True)
def configure_withdrawal_assessment(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    alpha_token,
    charlie_token,
    mock_price_source,
    mission_control,
    deleverage,
    switchboard_alpha,
):
    """Use deterministic, zero-interest terms and reset every relevant policy knob."""
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)

    alpha_terms = createDebtTerms(
        _ltv=70_00,
        _redemptionThreshold=80_00,
        _liqThreshold=85_00,
        _liqFee=10_00,
        _borrowRate=0,
    )
    setAssetConfig(
        alpha_token,
        _vaultIds=[3],
        _debtTerms=alpha_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
    )

    charlie_terms = createDebtTerms(
        _ltv=90_00,
        _redemptionThreshold=92_00,
        _liqThreshold=95_00,
        _liqFee=5_00,
        _borrowRate=0,
    )
    setAssetConfig(
        charlie_token,
        _vaultIds=[3],
        _debtTerms=charlie_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,
    )

    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, EIGHTEEN_DECIMALS)
    mission_control.setUnderscoreRegistry(
        ZERO_ADDRESS,
        sender=switchboard_alpha.address,
    )
    deleverage.setMinDeleverageBps(0, sender=switchboard_alpha.address)
    deleverage.setDeleverageBuffer(0, sender=switchboard_alpha.address)
    deleverage.setDeleverageCooldown(0, sender=switchboard_alpha.address)
    set_full_payoff_params(deleverage, switchboard_alpha)


@pytest.fixture
def build_position(
    teller,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    charlie_token,
    charlie_token_whale,
    performDeposit,
    setup_priority_configs,
):
    def build(
        user,
        *,
        target_amount=1_000 * EIGHTEEN_DECIMALS,
        debt_amount=500 * EIGHTEEN_DECIMALS,
        deleveragable_amount=700 * SIX_DECIMALS,
    ):
        performDeposit(
            user,
            target_amount,
            alpha_token,
            alpha_token_whale,
            simple_erc20_vault,
        )
        performDeposit(
            user,
            deleveragable_amount,
            charlie_token,
            charlie_token_whale,
            simple_erc20_vault,
        )
        teller.borrow(debt_amount, user, False, sender=user)
        setup_priority_configs(
            priority_stab_assets=[],
            priority_liq_assets=[(simple_erc20_vault, charlie_token)],
        )

    return build


def _state(
    user,
    *,
    deleverage,
    credit_engine,
    simple_erc20_vault,
    alpha_token,
    charlie_token,
    endaoment_funds,
):
    return {
        "target": simple_erc20_vault.getTotalAmountForUser(user, alpha_token),
        "deleveragable": simple_erc20_vault.getTotalAmountForUser(user, charlie_token),
        # Match deleverageForWithdrawal's strict debt/portfolio price read.
        "debt": credit_engine.getLatestUserDebtAndTerms(user, True)[0].amount,
        "endaoment": charlie_token.balanceOf(endaoment_funds),
        "last_block": deleverage.lastDeleverageBlock(user),
    }


def _expected_target(
    amount,
    user,
    *,
    deleverage,
    credit_engine,
    simple_erc20_vault,
    alpha_token,
):
    debt, terms, _ = credit_engine.getLatestUserDebtAndTerms(user, True)
    user_balance = simple_erc20_vault.getTotalAmountForUser(user, alpha_token)
    user_usd_value = user_balance
    withdraw_usd_value = user_usd_value
    if amount < user_balance:
        withdraw_usd_value = user_usd_value * amount // user_balance

    max_deleveragable, effective_ltv = deleverage.getDeleverageInfo(user)
    lost_capacity = withdraw_usd_value * 70_00 // HUNDRED_PERCENT
    denominator = terms.totalMaxDebt - debt.amount * effective_ltv // HUNDRED_PERCENT
    target = debt.amount * lost_capacity // denominator if denominator else 0
    buffer_bps = deleverage.deleverageBuffer()
    if buffer_bps:
        target = target * (HUNDRED_PERCENT + buffer_bps) // HUNDRED_PERCENT
    target = min(target, max_deleveragable, debt.amount)
    return {
        "user_balance": user_balance,
        "withdraw_usd_value": withdraw_usd_value,
        "lost_capacity": lost_capacity,
        "max_deleveragable": max_deleveragable,
        "debt": debt.amount,
        "total_max_debt": terms.totalMaxDebt,
        "effective_ltv": effective_ltv,
        "denominator": denominator,
        "target": target,
    }


def _call_and_measure(
    amount,
    user,
    caller,
    *,
    deleverage,
    credit_engine,
    simple_erc20_vault,
    alpha_token,
    charlie_token,
    endaoment_funds,
):
    before = _state(
        user,
        deleverage=deleverage,
        credit_engine=credit_engine,
        simple_erc20_vault=simple_erc20_vault,
        alpha_token=alpha_token,
        charlie_token=charlie_token,
        endaoment_funds=endaoment_funds,
    )
    formula = _expected_target(
        amount,
        user,
        deleverage=deleverage,
        credit_engine=credit_engine,
        simple_erc20_vault=simple_erc20_vault,
        alpha_token=alpha_token,
    )
    caller_before = (
        alpha_token.balanceOf(caller),
        charlie_token.balanceOf(caller),
    )
    result = deleverage.deleverageForWithdrawal(
        user,
        3,
        alpha_token,
        amount,
        sender=caller,
    )
    # Contract.get_logs() is scoped to the most recent Boa computation, so
    # capture the event before the read-only state queries below replace it.
    logs = filter_logs(deleverage, "DeleverageUser")
    event = logs[-1] if logs else None
    caller_after = (
        alpha_token.balanceOf(caller),
        charlie_token.balanceOf(caller),
    )
    after = _state(
        user,
        deleverage=deleverage,
        credit_engine=credit_engine,
        simple_erc20_vault=simple_erc20_vault,
        alpha_token=alpha_token,
        charlie_token=charlie_token,
        endaoment_funds=endaoment_funds,
    )
    return {
        "amount": amount,
        "result": result,
        "formula": formula,
        "target_delta": before["target"] - after["target"],
        "collateral_consumed": before["deleveragable"] - after["deleveragable"],
        "debt_cleared": before["debt"] - after["debt"],
        "endaoment_delta": after["endaoment"] - before["endaoment"],
        "caller_direct_delta": tuple(
            after_balance - before_balance
            for before_balance, after_balance in zip(caller_before, caller_after)
        ),
        "last_before": before["last_block"],
        "last_after": after["last_block"],
        "event_target": event.targetRepayAmount if event else 0,
        "event_target_with_buffer": event.targetRepayAmountWithBuffer if event else 0,
        "event_collateral_value": event.collateralValueRepaid if event else 0,
        "event_debt_clear": event.debtToClear if event else 0,
    }


def _print_measurements(label, measurements):
    print(label, json.dumps(measurements, sort_keys=True))


def test_amount_controls_deleveraging_from_identical_state(
    deleverage,
    teller,
    credit_engine,
    simple_erc20_vault,
    bob,
    alpha_token,
    charlie_token,
    endaoment_funds,
    build_position,
):
    build_position(bob)
    amounts = [
        0,
        100 * EIGHTEEN_DECIMALS,
        400 * EIGHTEEN_DECIMALS,
        1_000 * EIGHTEEN_DECIMALS,
        1_001 * EIGHTEEN_DECIMALS,
    ]
    measurements = []
    for amount in amounts:
        with boa.env.anchor():
            measurements.append(
                _call_and_measure(
                    amount,
                    bob,
                    teller.address,
                    deleverage=deleverage,
                    credit_engine=credit_engine,
                    simple_erc20_vault=simple_erc20_vault,
                    alpha_token=alpha_token,
                    charlie_token=charlie_token,
                    endaoment_funds=endaoment_funds,
                )
            )

    zero, small, large, full, over = measurements
    assert zero["result"] is False
    assert zero["formula"]["withdraw_usd_value"] == 0
    assert zero["debt_cleared"] == zero["collateral_consumed"] == 0
    assert zero["target_delta"] == zero["endaoment_delta"] == 0
    assert zero["last_before"] == zero["last_after"]

    assert 0 < small["debt_cleared"] < large["debt_cleared"] < full["debt_cleared"]
    for measurement in measurements[1:]:
        assert measurement["result"] is True
        assert measurement["target_delta"] == 0
        assert measurement["formula"]["withdraw_usd_value"] <= measurement["formula"]["user_balance"]
        assert measurement["event_target"] == measurement["formula"]["target"]
        assert measurement["event_target_with_buffer"] == measurement["formula"]["target"]
        assert measurement["event_collateral_value"] == measurement["debt_cleared"]
        assert measurement["event_debt_clear"] == measurement["debt_cleared"]
        assert measurement["endaoment_delta"] == measurement["collateral_consumed"]
        assert measurement["last_after"] != 0

    assert full["formula"]["withdraw_usd_value"] == full["formula"]["user_balance"]
    assert over["formula"]["withdraw_usd_value"] == full["formula"]["withdraw_usd_value"]
    assert over["debt_cleared"] == full["debt_cleared"]
    assert over["collateral_consumed"] == full["collateral_consumed"]
    _print_measurements("AMOUNT_BINDING", measurements)


def test_false_report_changes_debt_and_other_collateral_without_withdrawal(
    deleverage,
    teller,
    credit_engine,
    simple_erc20_vault,
    bob,
    alpha_token,
    charlie_token,
    endaoment_funds,
    build_position,
):
    build_position(bob)
    measurement = _call_and_measure(
        400 * EIGHTEEN_DECIMALS,
        bob,
        teller.address,
        deleverage=deleverage,
        credit_engine=credit_engine,
        simple_erc20_vault=simple_erc20_vault,
        alpha_token=alpha_token,
        charlie_token=charlie_token,
        endaoment_funds=endaoment_funds,
    )
    assert measurement["result"] is True
    assert measurement["target_delta"] == 0
    assert measurement["debt_cleared"] > 0
    assert measurement["collateral_consumed"] > 0
    assert measurement["endaoment_delta"] > 0
    assert measurement["caller_direct_delta"] == (0, 0)
    assert measurement["event_target"] == measurement["formula"]["target"]
    assert measurement["event_debt_clear"] == measurement["debt_cleared"]
    assert measurement["formula"]["target"] < measurement["formula"]["max_deleveragable"]
    assert measurement["formula"]["target"] < measurement["formula"]["debt"]
    _print_measurements("FALSE_REPORT", measurement)


def test_inflated_report_activates_robinhood_full_payoff_buffer_for_ordinary_owner(
    deleverage,
    teller,
    credit_engine,
    simple_erc20_vault,
    bob,
    alpha_token,
    charlie_token,
    endaoment_funds,
    build_position,
    switchboard_alpha,
):
    deleverage.setDeleverageBuffer(2_00, sender=switchboard_alpha.address)
    set_full_payoff_params(
        deleverage,
        switchboard_alpha,
        buffer_amount=ROBINHOOD_FULL_PAYOFF_BUFFER,
        overage_bps=100,
        dust_threshold=0,
        dust_bps=0,
    )
    build_position(
        bob,
        debt_amount=700 * EIGHTEEN_DECIMALS,
        deleveragable_amount=710 * SIX_DECIMALS,
    )

    measurements = []
    for amount in [100 * EIGHTEEN_DECIMALS, 1_000 * EIGHTEEN_DECIMALS]:
        with boa.env.anchor():
            measurements.append(
                _call_and_measure(
                    amount,
                    bob,
                    teller.address,
                    deleverage=deleverage,
                    credit_engine=credit_engine,
                    simple_erc20_vault=simple_erc20_vault,
                    alpha_token=alpha_token,
                    charlie_token=charlie_token,
                    endaoment_funds=endaoment_funds,
                )
            )

    honest, inflated = measurements
    assert honest["event_target"] < honest["formula"]["debt"]
    assert honest["event_target_with_buffer"] == honest["event_target"]
    assert inflated["event_target"] == inflated["formula"]["debt"]
    assert (
        inflated["event_target_with_buffer"]
        == inflated["event_target"] + ROBINHOOD_FULL_PAYOFF_BUFFER
    )
    assert inflated["event_collateral_value"] == inflated["event_target_with_buffer"]
    assert inflated["event_debt_clear"] == inflated["event_target"]
    assert inflated["collateral_consumed"] * 10**12 > inflated["debt_cleared"]
    assert honest["caller_direct_delta"] == inflated["caller_direct_delta"] == (0, 0)
    assert inflated["formula"]["target"] == inflated["formula"]["debt"]
    assert inflated["formula"]["max_deleveragable"] > inflated["formula"]["debt"]
    _print_measurements("INFLATED_FULL_PAYOFF", measurements)


def test_bounded_dust_forgiveness_is_reachable_only_after_explicit_enablement(
    deleverage,
    teller,
    credit_engine,
    simple_erc20_vault,
    bob,
    charlie_token,
    green_token,
    endaoment_funds,
    build_position,
    switchboard_alpha,
):
    """Exercise the shared trusted full-payoff primitive with bounded dust enabled.

    The withdrawal formula caps its target at maxDeleveragable, so a position
    whose real deleveragable collateral is short of total debt cannot enter the
    dust branch through deleverageForWithdrawal itself. The sibling trusted
    route reaches the same _getDebtToClear primitive and proves the latent
    write-off behavior without claiming it is active under launch defaults.
    """
    dust = 10**12  # one raw unit of the six-decimal $1 Charlie fixture
    set_full_payoff_params(
        deleverage,
        switchboard_alpha,
        buffer_amount=0,
        overage_bps=0,
        dust_threshold=dust,
        dust_bps=1,
    )
    build_position(
        bob,
        debt_amount=500 * EIGHTEEN_DECIMALS,
        deleveragable_amount=500 * SIX_DECIMALS - 1,
    )

    before_debt = credit_engine.getLatestUserDebtAndTerms(bob, True)[0].amount
    before_collateral = simple_erc20_vault.getTotalAmountForUser(bob, charlie_token)
    before_endaoment = charlie_token.balanceOf(endaoment_funds)
    before_green_supply = green_token.totalSupply()
    repaid = teller.deleverageWithSpecificAssets(
        [(3, charlie_token.address, before_debt)],
        bob,
        sender=switchboard_alpha.address,
    )
    event = filter_logs(teller, "DeleverageUser")[-1]
    after_debt = credit_engine.getLatestUserDebtAndTerms(bob, True)[0].amount
    after_collateral = simple_erc20_vault.getTotalAmountForUser(bob, charlie_token)
    after_endaoment = charlie_token.balanceOf(endaoment_funds)
    after_green_supply = green_token.totalSupply()

    assert before_debt == 500 * EIGHTEEN_DECIMALS
    assert before_collateral == 500 * SIX_DECIMALS - 1
    assert after_collateral == 0
    assert after_endaoment - before_endaoment == before_collateral
    assert event.targetRepayAmount == before_debt
    assert event.targetRepayAmountWithBuffer == before_debt
    assert event.collateralValueRepaid == before_debt - dust
    assert event.debtToClear == before_debt
    assert repaid == before_debt
    assert after_debt == 0
    assert event.debtToClear - event.collateralValueRepaid == dust
    # Department repayment performs no GREEN burn, including for this dust.
    assert after_green_supply == before_green_supply


def test_earn_vault_position_owner_disables_full_payoff_extras(
    deleverage,
    teller,
    credit_engine,
    simple_erc20_vault,
    bob,
    alpha_token,
    charlie_token,
    endaoment_funds,
    build_position,
    switchboard_alpha,
    mission_control,
    mock_undy_v2,
):
    deleverage.setDeleverageBuffer(2_00, sender=switchboard_alpha.address)
    set_full_payoff_params(
        deleverage,
        switchboard_alpha,
        buffer_amount=ROBINHOOD_FULL_PAYOFF_BUFFER,
        overage_bps=100,
        dust_threshold=10**16,
        dust_bps=500,
    )
    build_position(
        bob,
        debt_amount=700 * EIGHTEEN_DECIMALS,
        deleveragable_amount=710 * SIX_DECIMALS,
    )
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_undy_v2.setAllAddressesAreVaults(False)
    mock_undy_v2.setEarnVault(bob, True)
    mock_undy_v2.setBasicEarnVault(bob, False)
    mock_undy_v2.setEarnVault(teller.address, False)

    measurement = _call_and_measure(
        1_000 * EIGHTEEN_DECIMALS,
        bob,
        teller.address,
        deleverage=deleverage,
        credit_engine=credit_engine,
        simple_erc20_vault=simple_erc20_vault,
        alpha_token=alpha_token,
        charlie_token=charlie_token,
        endaoment_funds=endaoment_funds,
    )
    assert mock_undy_v2.isEarnVault(bob) is True
    assert mock_undy_v2.isEarnVault(teller.address) is False
    assert measurement["event_target"] == measurement["formula"]["debt"]
    assert measurement["event_target_with_buffer"] == measurement["event_target"]
    assert measurement["event_collateral_value"] == measurement["event_debt_clear"]
    assert measurement["collateral_consumed"] * 10**12 == measurement["debt_cleared"]
    assert measurement["target_delta"] == 0
    _print_measurements("EARN_VAULT_OWNER", measurement)


@pytest.mark.parametrize("underscore_caller_type", ("earn_vault", "lego"))
def test_recognized_underscore_caller_can_select_undelegated_victim(
    deleverage,
    credit_engine,
    simple_erc20_vault,
    bob,
    alice,
    alpha_token,
    charlie_token,
    green_token,
    savings_green,
    endaoment_funds,
    build_position,
    switchboard_alpha,
    mission_control,
    mock_undy_v2,
    ripe_hq,
    underscore_caller_type,
):
    """Exercise both caller types Ripe recognizes, not real admission policy."""
    build_position(bob)
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_undy_v2.setAllAddressesAreVaults(False)
    is_earn_vault = underscore_caller_type == "earn_vault"
    mock_undy_v2.setEarnVault(alice, is_earn_vault)
    mock_undy_v2.setBasicEarnVault(alice, False)
    mock_undy_v2.setEarnVault(bob, False)

    assert ripe_hq.isValidAddr(alice) is False
    assert mock_undy_v2.isEarnVault(alice) is is_earn_vault
    if underscore_caller_type == "lego":
        assert (
            mock_undy_v2.getAddr(UNDERSCORE_LEGO_BOOK_ID)
            == mock_undy_v2.address
        )
        assert mock_undy_v2.isValidAddr(alice) is True
    assert mission_control.userDelegation(bob, alice).canBorrow is False
    caller_before = (
        alpha_token.balanceOf(alice),
        charlie_token.balanceOf(alice),
        green_token.balanceOf(alice),
        savings_green.balanceOf(alice),
    )
    measurement = _call_and_measure(
        400 * EIGHTEEN_DECIMALS,
        bob,
        alice,
        deleverage=deleverage,
        credit_engine=credit_engine,
        simple_erc20_vault=simple_erc20_vault,
        alpha_token=alpha_token,
        charlie_token=charlie_token,
        endaoment_funds=endaoment_funds,
    )
    caller_after = (
        alpha_token.balanceOf(alice),
        charlie_token.balanceOf(alice),
        green_token.balanceOf(alice),
        savings_green.balanceOf(alice),
    )
    assert measurement["result"] is True
    assert measurement["target_delta"] == 0
    assert measurement["debt_cleared"] > 0
    assert measurement["collateral_consumed"] > 0
    assert caller_after == caller_before
    _print_measurements(
        f"CROSS_USER_UNDERSCORE_{underscore_caller_type.upper()}",
        measurement,
    )


def test_trusted_caller_cross_user_model_is_shared_by_both_sibling_routes(
    deleverage,
    teller,
    credit_engine,
    simple_erc20_vault,
    bob,
    alice,
    alpha_token,
    charlie_token,
    endaoment_funds,
    build_position,
    switchboard_alpha,
    mission_control,
    mock_undy_v2,
    ripe_hq,
):
    """Ripe/Underscore trust bypasses victim delegation on all three routes."""
    build_position(bob)
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_undy_v2.setAllAddressesAreVaults(False)
    mock_undy_v2.setEarnVault(alice, True)
    mock_undy_v2.setBasicEarnVault(alice, False)
    mock_undy_v2.setEarnVault(bob, False)

    assert ripe_hq.isValidAddr(alice) is False
    assert mock_undy_v2.isEarnVault(alice) is True
    assert mission_control.userDelegation(bob, alice).canBorrow is False

    measurements = []
    for route in ("many", "specific"):
        with boa.env.anchor():
            before = _state(
                bob,
                deleverage=deleverage,
                credit_engine=credit_engine,
                simple_erc20_vault=simple_erc20_vault,
                alpha_token=alpha_token,
                charlie_token=charlie_token,
                endaoment_funds=endaoment_funds,
            )
            caller_before = (
                alpha_token.balanceOf(alice),
                charlie_token.balanceOf(alice),
            )
            target = 100 * EIGHTEEN_DECIMALS
            if route == "many":
                repaid = teller.deleverageManyUsers(
                    [(bob, target)],
                    sender=alice,
                )
            else:
                repaid = teller.deleverageWithSpecificAssets(
                    [(3, charlie_token.address, target)],
                    bob,
                    sender=alice,
                )
            event = filter_logs(teller, "DeleverageUser")[-1]
            caller_after = (
                alpha_token.balanceOf(alice),
                charlie_token.balanceOf(alice),
            )
            after = _state(
                bob,
                deleverage=deleverage,
                credit_engine=credit_engine,
                simple_erc20_vault=simple_erc20_vault,
                alpha_token=alpha_token,
                charlie_token=charlie_token,
                endaoment_funds=endaoment_funds,
            )
            measurements.append(
                {
                    "route": route,
                    "repaid": repaid,
                    "target_delta": before["target"] - after["target"],
                    "collateral_consumed": (
                        before["deleveragable"] - after["deleveragable"]
                    ),
                    "debt_cleared": before["debt"] - after["debt"],
                    "endaoment_delta": after["endaoment"] - before["endaoment"],
                    "caller_direct_delta": tuple(
                        after_balance - before_balance
                        for before_balance, after_balance in zip(
                            caller_before,
                            caller_after,
                        )
                    ),
                    "event_target": event.targetRepayAmount,
                    "event_debt_clear": event.debtToClear,
                }
            )

    for measurement in measurements:
        assert measurement["repaid"] == 100 * EIGHTEEN_DECIMALS
        assert measurement["target_delta"] == 0
        assert measurement["collateral_consumed"] == 100 * SIX_DECIMALS
        assert measurement["debt_cleared"] == 100 * EIGHTEEN_DECIMALS
        assert measurement["endaoment_delta"] == 100 * SIX_DECIMALS
        assert measurement["caller_direct_delta"] == (0, 0)
        assert measurement["event_target"] == 100 * EIGHTEEN_DECIMALS
        assert measurement["event_debt_clear"] == 100 * EIGHTEEN_DECIMALS
    _print_measurements("SIBLING_CROSS_USER_TRUST", measurements)


def test_registered_ripe_address_can_select_undelegated_victim(
    deleverage,
    credit_engine,
    simple_erc20_vault,
    bob,
    auction_house,
    alpha_token,
    charlie_token,
    endaoment_funds,
    build_position,
    mission_control,
    ripe_hq,
):
    build_position(bob)
    assert ripe_hq.isValidAddr(auction_house.address) is True
    assert mission_control.userDelegation(bob, auction_house.address).canBorrow is False
    measurement = _call_and_measure(
        400 * EIGHTEEN_DECIMALS,
        bob,
        auction_house.address,
        deleverage=deleverage,
        credit_engine=credit_engine,
        simple_erc20_vault=simple_erc20_vault,
        alpha_token=alpha_token,
        charlie_token=charlie_token,
        endaoment_funds=endaoment_funds,
    )
    assert measurement["result"] is True
    assert measurement["target_delta"] == 0
    assert measurement["debt_cleared"] > 0
    _print_measurements("CROSS_USER_RIPE", measurement)


def test_completely_unregistered_caller_reverts_no_perms(
    deleverage,
    bob,
    alice,
    alpha_token,
    build_position,
    ripe_hq,
    mission_control,
):
    build_position(bob)
    assert ripe_hq.isValidAddr(alice) is False
    assert mission_control.underscoreRegistry() == ZERO_ADDRESS
    with boa.reverts("no perms"):
        deleverage.deleverageForWithdrawal(
            bob,
            3,
            alpha_token,
            400 * EIGHTEEN_DECIMALS,
            sender=alice,
        )


def test_repeated_same_block_false_reports_bypass_cooldown(
    deleverage,
    teller,
    credit_engine,
    simple_erc20_vault,
    bob,
    alpha_token,
    charlie_token,
    endaoment_funds,
    build_position,
    switchboard_alpha,
):
    deleverage.setDeleverageCooldown(10, sender=switchboard_alpha.address)
    build_position(bob)
    action_block = boa.env.evm.patch.block_number
    measurements = []

    for _ in range(3):
        # Titanoboa 0.2.7 does not clear EIP-1153 storage between simulated
        # transactions. Explicit clearing models separate transactions in the
        # same block without advancing the block clock.
        boa.env.evm.vm.state.clear_transient_storage()
        measurements.append(
            _call_and_measure(
                100 * EIGHTEEN_DECIMALS,
                bob,
                teller.address,
                deleverage=deleverage,
                credit_engine=credit_engine,
                simple_erc20_vault=simple_erc20_vault,
                alpha_token=alpha_token,
                charlie_token=charlie_token,
                endaoment_funds=endaoment_funds,
            )
        )
        assert boa.env.evm.patch.block_number == action_block

    assert all(m["result"] is True for m in measurements)
    assert all(m["target_delta"] == 0 for m in measurements)
    assert all(m["debt_cleared"] > 0 for m in measurements)
    assert all(m["collateral_consumed"] > 0 for m in measurements)
    assert all(m["last_after"] == action_block for m in measurements)
    assert measurements[1]["last_before"] == action_block
    assert sum(m["debt_cleared"] for m in measurements) > measurements[0]["debt_cleared"]
    _print_measurements("REPEATED_SAME_BLOCK", measurements)


def test_live_fixture_full_payoff_parameters_are_zero(deleverage):
    assert deleverage.deleverageFullPayoffBuffer() == 0
    assert deleverage.deleverageOverageBps() == 0
    assert deleverage.deleverageDustThreshold() == 0
    assert deleverage.deleverageDustBps() == 0


def test_strict_price_read_reverts_entire_withdrawal_deleverage(
    deleverage,
    teller,
    bob,
    alpha_token,
    mock_price_source,
    build_position,
):
    build_position(bob)
    mock_price_source.setPrice(alpha_token, 0)
    with boa.reverts("has price config, no price"):
        deleverage.deleverageForWithdrawal(
            bob,
            3,
            alpha_token,
            100 * EIGHTEEN_DECIMALS,
            sender=teller.address,
        )
