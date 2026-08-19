"""Preserved focused proofs for the B-OBS-008 Teller assessment.

This module is assessment evidence only. Temporary Teller candidates are
compiled from in-memory source strings; the tracked production contract is not
changed.
"""

from importlib.metadata import version
from pathlib import Path

import boa
import pytest
from boa.contracts.base_evm_contract import BoaError

from constants import EIGHTEEN_DECIMALS
from conf_utils import filter_logs
from test_teller_deposit import (
    M1_PRICE_CALLBACK_SOURCE,
    _boa_error_has_dev_reason,
    _m1_configure_gov_asset,
    _m1_replace_hq_address,
    _m1_token,
)


REVERTING_PRICE_CALLBACK_SOURCE = """
# @version 0.4.3

from ethereum.ercs import IERC20

callback_target: public(address)
callback_data: public(Bytes[1024])
callback_enabled: public(bool)

@external
def configure(_target: address, _data: Bytes[1024]):
    self.callback_target = _target
    self.callback_data = _data
    self.callback_enabled = True

@external
def approve_teller(_asset: address, _teller: address, _amount: uint256):
    assert extcall IERC20(_asset).approve(_teller, _amount)

@external
def addPriceSnapshot(_asset: address) -> bool:
    if self.callback_enabled:
        self.callback_enabled = False
        success: bool = False
        response: Bytes[1] = b""
        success, response = raw_call(
            self.callback_target,
            self.callback_data,
            max_outsize=1,
            revert_on_failure=False,
        )
        assert success # dev: nested callback failed
        raise
    return True
"""


GOVERNANCE_PRICE_CALLBACK_SOURCE = M1_PRICE_CALLBACK_SOURCE + """
@view
@external
def getAddr(_reg_id: uint256) -> address:
    # CurvePrices is intentionally configured off in this focused harness.
    return empty(address)

@view
@external
def getUsdValue(
    _asset: address,
    _amount: uint256,
    _should_raise: bool,
) -> uint256:
    return _amount
"""


GOVERNANCE_REVERTING_PRICE_CALLBACK_SOURCE = (
    REVERTING_PRICE_CALLBACK_SOURCE
    + """
@view
@external
def getAddr(_reg_id: uint256) -> address:
    # CurvePrices is intentionally configured off in this focused harness.
    return empty(address)

@view
@external
def getUsdValue(
    _asset: address,
    _amount: uint256,
    _should_raise: bool,
) -> uint256:
    return _amount
"""
)


TRACE_SIGNATURE_TOOLCHAIN = {
    "titanoboa": "0.2.7",
    "vyper": "0.4.3",
}


def _load_teller_variant(variant, ripe_hq_deploy):
    source = Path("contracts/core/Teller.vy").read_text()
    route = {
        "trusted_guard": "depositFromTrusted",
        "governance_guard": "depositIntoGovVault",
    }[variant]
    marker = f"@external\ndef {route}("
    assert source.count(marker) == 1
    source = source.replace(marker, f"@nonreentrant\n{marker}", 1)
    return boa.loads(
        source,
        ripe_hq_deploy,
        False,
        name=f"teller_{variant}",
        override_address=boa.env.generate_address(),
    )


def _active_teller(variant, teller, ripe_hq_deploy, ripe_hq, governance):
    if variant == "baseline":
        return teller
    candidate = _load_teller_variant(variant, ripe_hq_deploy)
    _m1_replace_hq_address(ripe_hq, governance, 17, candidate)
    return candidate


def _dev_reasons(error):
    return [
        frame.dev_reason.reason_str
        for frame in error.stack_trace
        if not isinstance(frame, str)
        and getattr(frame, "dev_reason", None) is not None
    ]


def _assert_rejection_guard(error, expected):
    if expected == "receipt measurement active":
        assert _boa_error_has_dev_reason(error, expected), {
            "dev_reasons": _dev_reasons(error),
            "error_details": [
                frame if isinstance(frame, str) else frame.error_detail
                for frame in error.stack_trace
            ],
        }
        return
    # Vyper's generated nonreentrant check has no source dev annotation.
    assert not _boa_error_has_dev_reason(error, "receipt measurement active")
    actual_toolchain = {
        package: version(package) for package in TRACE_SIGNATURE_TOOLCHAIN
    }
    assert actual_toolchain == TRACE_SIGNATURE_TOOLCHAIN, (
        "The generated nonreentrant trace signature is frozen to the assessment "
        f"toolchain; expected {TRACE_SIGNATURE_TOOLCHAIN}, got {actual_toolchain}."
    )
    # Boa 0.2.7 maps this zero-data compiler-generated prologue revert to the
    # route FunctionDef and labels it "uint160 bounds check". It also inherits
    # the first body assertion's dev reason even though that body was not
    # entered. Pin the raw prologue signature and separately exclude the
    # receipt-mutex reason; do not stringify the trace because Boa tries to ABI
    # decode a raw ERC20 return word as Bytes and raises DecodeError.
    inner = error.stack_trace[0]
    assert inner.error_detail == "uint160 bounds check"
    assert inner.ast_source.name in (
        "depositFromTrusted",
        "depositIntoGovVault",
    )
    assert inner.vm_error.args == (b"",)


def _configure_gov_and_simple_asset(
    token,
    mission_control,
    switchboard_alpha,
    setAssetConfig,
    vault_book,
    simple_erc20_vault,
):
    gov_id = mission_control.coreRipeGovVaultId()
    simple_id = vault_book.getRegId(simple_erc20_vault)
    mission_control.setRipeGovVaultConfig(
        token,
        100_00,
        False,
        (100, 1000, 200_00, True, 10_00),
        sender=switchboard_alpha.address,
    )
    setAssetConfig(token, _vaultIds=[gov_id, simple_id])
    return gov_id, simple_id


@pytest.mark.parametrize(
    ("variant", "expected_guard"),
    (
        pytest.param("baseline", "receipt measurement active", id="baseline"),
        pytest.param("trusted_guard", "nonreentrant", id="trusted-guard"),
        pytest.param(
            "governance_guard",
            "receipt measurement active",
            id="sibling-governance-guard",
        ),
    ),
)
def test_trusted_active_window_guard_attribution(
    variant,
    expected_guard,
    ripe_hq_deploy,
    ripe_hq,
    governance,
    credit_engine,
    simple_erc20_vault,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    ledger,
    vault_book,
):
    active_teller = _active_teller(
        variant, teller, ripe_hq_deploy, ripe_hq, governance
    )
    setGeneralConfig()
    token = _m1_token()
    setAssetConfig(token)
    _m1_replace_hq_address(ripe_hq, governance, 15, token)

    amount = 100 * EIGHTEEN_DECIMALS
    nested_amount = 1
    vault_id = vault_book.getRegId(simple_erc20_vault)
    token.mint(credit_engine, amount)
    token.approve(active_teller, amount, sender=credit_engine.address)
    token.mint(token, nested_amount)
    token.set_self_allowance(active_teller, nested_amount)
    nested = active_teller.depositFromTrusted.prepare_calldata(
        bob, vault_id, token, nested_amount, 0
    )
    token.configure_callback(active_teller, nested, True)
    token.configure_callback_rejection_policy(False)
    token.configure_transfer(0)

    before = (
        token.balanceValue(credit_engine),
        token.balanceValue(token),
        token.balanceValue(simple_erc20_vault),
        simple_erc20_vault.getTotalAmountForUser(bob, token),
        ledger.getNumUserVaults(bob),
    )
    with pytest.raises(BoaError) as exc_info:
        active_teller.depositFromTrusted(
            bob,
            vault_id,
            token,
            amount,
            0,
            sender=credit_engine.address,
        )

    _assert_rejection_guard(exc_info.value, expected_guard)
    assert before == (
        token.balanceValue(credit_engine),
        token.balanceValue(token),
        token.balanceValue(simple_erc20_vault),
        simple_erc20_vault.getTotalAmountForUser(bob, token),
        ledger.getNumUserVaults(bob),
    )
    assert filter_logs(active_teller, "TellerDeposit") == []


@pytest.mark.parametrize(
    ("variant", "expected_guard"),
    (
        pytest.param("baseline", "receipt measurement active", id="baseline"),
        pytest.param(
            "trusted_guard",
            "receipt measurement active",
            id="sibling-trusted-guard",
        ),
        pytest.param("governance_guard", "nonreentrant", id="governance-guard"),
    ),
)
def test_governance_active_window_guard_attribution(
    variant,
    expected_guard,
    ripe_hq_deploy,
    ripe_hq,
    governance,
    ripe_gov_vault,
    setGeneralConfig,
    setAssetConfig,
    mission_control,
    switchboard_alpha,
    teller,
    ledger,
):
    active_teller = _active_teller(
        variant, teller, ripe_hq_deploy, ripe_hq, governance
    )
    setGeneralConfig()
    token = _m1_token()
    _m1_configure_gov_asset(
        token, mission_control, switchboard_alpha, setAssetConfig
    )

    user = token.address
    amount = 100 * EIGHTEEN_DECIMALS
    nested_amount = 1
    token.mint(token, amount + nested_amount)
    token.set_self_allowance(active_teller, amount + nested_amount)
    nested = active_teller.depositIntoGovVault.prepare_calldata(
        token, nested_amount, 500, user
    )
    token.configure_callback(active_teller, nested, True)
    token.configure_callback_rejection_policy(False)
    token.configure_transfer(0)

    before = (
        token.balanceValue(token),
        token.balanceValue(ripe_gov_vault),
        ripe_gov_vault.getTotalAmountForUser(user, token),
        ledger.getNumUserVaults(user),
    )
    with pytest.raises(BoaError) as exc_info:
        active_teller.depositIntoGovVault(
            token, amount, 500, user, sender=user
        )

    _assert_rejection_guard(exc_info.value, expected_guard)
    assert before == (
        token.balanceValue(token),
        token.balanceValue(ripe_gov_vault),
        ripe_gov_vault.getTotalAmountForUser(user, token),
        ledger.getNumUserVaults(user),
    )
    assert filter_logs(active_teller, "TellerDeposit") == []


@pytest.mark.parametrize(
    ("variant", "outer_route"),
    (
        pytest.param(
            "trusted_guard",
            "trusted_to_governance",
            id="trusted-guard-outer-to-governance",
        ),
        pytest.param(
            "governance_guard",
            "governance_to_trusted",
            id="governance-guard-outer-to-trusted",
        ),
    ),
)
def test_decorated_outer_cross_route_entry_still_reaches_receipt_mutex(
    variant,
    outer_route,
    ripe_hq_deploy,
    ripe_hq,
    governance,
    credit_engine,
    simple_erc20_vault,
    ripe_gov_vault,
    setGeneralConfig,
    setAssetConfig,
    mission_control,
    switchboard_alpha,
    teller,
    ledger,
    vault_book,
):
    active_teller = _active_teller(
        variant, teller, ripe_hq_deploy, ripe_hq, governance
    )
    setGeneralConfig()
    token = _m1_token()
    gov_id, simple_id = _configure_gov_and_simple_asset(
        token,
        mission_control,
        switchboard_alpha,
        setAssetConfig,
        vault_book,
        simple_erc20_vault,
    )

    user = token.address
    amount = 100 * EIGHTEEN_DECIMALS
    nested_amount = 1
    if outer_route == "trusted_to_governance":
        token.mint(credit_engine, amount)
        token.approve(active_teller, amount, sender=credit_engine.address)
        token.mint(token, nested_amount)
        token.set_self_allowance(active_teller, nested_amount)
        nested = active_teller.depositIntoGovVault.prepare_calldata(
            token, nested_amount, 500, user
        )
        token.configure_callback(active_teller, nested, True)
    else:
        _m1_replace_hq_address(ripe_hq, governance, 15, token)
        token.mint(token, amount + nested_amount)
        token.set_self_allowance(active_teller, amount + nested_amount)
        nested = active_teller.depositFromTrusted.prepare_calldata(
            user, simple_id, token, nested_amount, 0
        )
        token.configure_callback(active_teller, nested, True)
    token.configure_callback_rejection_policy(False)
    token.configure_transfer(0)

    before = (
        token.balanceValue(credit_engine),
        token.balanceValue(token),
        token.balanceValue(simple_erc20_vault),
        token.balanceValue(ripe_gov_vault),
        simple_erc20_vault.getTotalAmountForUser(user, token),
        ripe_gov_vault.getTotalAmountForUser(user, token),
        ledger.getNumUserVaults(user),
    )
    with pytest.raises(BoaError) as exc_info:
        if outer_route == "trusted_to_governance":
            active_teller.depositFromTrusted(
                user,
                simple_id,
                token,
                amount,
                0,
                sender=credit_engine.address,
            )
        else:
            active_teller.depositIntoGovVault(
                token, amount, 500, user, sender=user
            )

    _assert_rejection_guard(exc_info.value, "receipt measurement active")
    assert before == (
        token.balanceValue(credit_engine),
        token.balanceValue(token),
        token.balanceValue(simple_erc20_vault),
        token.balanceValue(ripe_gov_vault),
        simple_erc20_vault.getTotalAmountForUser(user, token),
        ripe_gov_vault.getTotalAmountForUser(user, token),
        ledger.getNumUserVaults(user),
    )
    assert gov_id != simple_id
    assert filter_logs(active_teller, "TellerDeposit") == []


def _setup_post_clear_callback(
    source,
    name,
    ripe_hq,
    governance,
    credit_engine,
    simple_erc20_vault,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    vault_book,
):
    setGeneralConfig()
    token = _m1_token()
    setAssetConfig(token)
    callback_price_desk = boa.loads(
        source,
        name=name,
        override_address=boa.env.generate_address(),
    )
    _m1_replace_hq_address(ripe_hq, governance, 7, callback_price_desk)

    amount = 100 * EIGHTEEN_DECIMALS
    nested_amount = 1
    vault_id = vault_book.getRegId(simple_erc20_vault)
    token.mint(credit_engine, amount)
    token.approve(teller, amount, sender=credit_engine.address)
    token.mint(callback_price_desk, nested_amount)
    callback_price_desk.approve_teller(token, teller, nested_amount)
    nested = teller.depositFromTrusted.prepare_calldata(
        bob, vault_id, token, nested_amount, 0
    )
    callback_price_desk.configure(teller, nested)
    return token, callback_price_desk, amount, nested_amount, vault_id


def test_post_clear_nested_deposit_preserves_complete_accounting(
    ripe_hq,
    governance,
    credit_engine,
    simple_erc20_vault,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    teller,
    ledger,
    vault_book,
):
    token, callback_price_desk, amount, nested_amount, vault_id = (
        _setup_post_clear_callback(
            M1_PRICE_CALLBACK_SOURCE,
            "assessment_success_price_callback",
            ripe_hq,
            governance,
            credit_engine,
            simple_erc20_vault,
            bob,
            setGeneralConfig,
            setAssetConfig,
            teller,
            vault_book,
        )
    )
    setRipeRewardsConfig()
    custody_before = token.balanceValue(simple_erc20_vault)
    last_touch_before = ledger.lastTouch(bob)
    debt_before = ledger.userDebt(bob)
    assert teller.depositFromTrusted(
        bob,
        vault_id,
        token,
        amount,
        0,
        sender=credit_engine.address,
    ) == amount

    expected_total = amount + nested_amount
    assert not callback_price_desk.callback_enabled()
    assert token.balanceValue(simple_erc20_vault) - custody_before == expected_total
    assert simple_erc20_vault.getTotalAmountForUser(bob, token) == expected_total
    assert ledger.getNumUserVaults(bob) == 1

    user_points = ledger.userDepositPoints(bob, vault_id, token)
    asset_points = ledger.assetDepositPoints(vault_id, token)
    expected_share = simple_erc20_vault.getUserLootBoxShare(bob, token)
    assert asset_points.precision == 10**9
    assert user_points.lastBalance == expected_share // asset_points.precision
    assert asset_points.lastBalance == user_points.lastBalance
    assert user_points.balancePoints == 0
    assert asset_points.balancePoints == 0
    assert ledger.lastTouch(bob) == last_touch_before == 0
    assert ledger.userDebt(bob) == debt_before
    assert debt_before.amount == 0
    assert [log.amount for log in filter_logs(teller, "TellerDeposit")] == [
        nested_amount,
        amount,
    ]


def test_post_clear_nested_deposit_rolls_back_with_downstream_failure(
    ripe_hq,
    governance,
    credit_engine,
    simple_erc20_vault,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    ledger,
    vault_book,
):
    token, callback_price_desk, amount, nested_amount, vault_id = (
        _setup_post_clear_callback(
            REVERTING_PRICE_CALLBACK_SOURCE,
            "assessment_reverting_price_callback",
            ripe_hq,
            governance,
            credit_engine,
            simple_erc20_vault,
            bob,
            setGeneralConfig,
            setAssetConfig,
            teller,
            vault_book,
        )
    )
    before = (
        token.balanceValue(credit_engine),
        token.balanceValue(callback_price_desk),
        token.balanceValue(simple_erc20_vault),
        simple_erc20_vault.getTotalAmountForUser(bob, token),
        ledger.getNumUserVaults(bob),
        ledger.userDepositPoints(bob, vault_id, token),
        ledger.assetDepositPoints(vault_id, token),
        ledger.lastTouch(bob),
        ledger.userDebt(bob),
        callback_price_desk.callback_enabled(),
    )
    with pytest.raises(BoaError) as downstream:
        teller.depositFromTrusted(
            bob,
            vault_id,
            token,
            amount,
            0,
            sender=credit_engine.address,
        )
    assert not _boa_error_has_dev_reason(
        downstream.value, "nested callback failed"
    )

    assert before == (
        token.balanceValue(credit_engine),
        token.balanceValue(callback_price_desk),
        token.balanceValue(simple_erc20_vault),
        simple_erc20_vault.getTotalAmountForUser(bob, token),
        ledger.getNumUserVaults(bob),
        ledger.userDepositPoints(bob, vault_id, token),
        ledger.assetDepositPoints(vault_id, token),
        ledger.lastTouch(bob),
        ledger.userDebt(bob),
        callback_price_desk.callback_enabled(),
    )
    assert nested_amount == 1
    assert filter_logs(teller, "TellerDeposit") == []


def _setup_governance_post_clear_callback(
    source,
    name,
    ripe_hq,
    governance,
    simple_erc20_vault,
    bob,
    setGeneralConfig,
    setAssetConfig,
    mission_control,
    switchboard_alpha,
    teller,
    vault_book,
):
    setGeneralConfig()
    token = _m1_token()
    gov_id, simple_id = _configure_gov_and_simple_asset(
        token,
        mission_control,
        switchboard_alpha,
        setAssetConfig,
        vault_book,
        simple_erc20_vault,
    )
    callback_price_desk = boa.loads(
        source,
        name=name,
        override_address=boa.env.generate_address(),
    )
    _m1_replace_hq_address(ripe_hq, governance, 7, callback_price_desk)

    amount = 100 * EIGHTEEN_DECIMALS
    nested_amount = 1
    token.mint(bob, amount)
    token.approve(teller, amount, sender=bob)
    token.mint(callback_price_desk, nested_amount)
    callback_price_desk.approve_teller(token, teller, nested_amount)
    nested = teller.depositFromTrusted.prepare_calldata(
        bob, simple_id, token, nested_amount, 0
    )
    callback_price_desk.configure(teller, nested)
    return (
        token,
        callback_price_desk,
        amount,
        nested_amount,
        gov_id,
        simple_id,
    )


def test_governance_post_clear_nested_deposit_preserves_complete_accounting(
    ripe_hq,
    governance,
    simple_erc20_vault,
    ripe_gov_vault,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    mission_control,
    switchboard_alpha,
    teller,
    ledger,
    vault_book,
):
    token, callback_price_desk, amount, nested_amount, gov_id, simple_id = (
        _setup_governance_post_clear_callback(
            GOVERNANCE_PRICE_CALLBACK_SOURCE,
            "assessment_governance_success_price_callback",
            ripe_hq,
            governance,
            simple_erc20_vault,
            bob,
            setGeneralConfig,
            setAssetConfig,
            mission_control,
            switchboard_alpha,
            teller,
            vault_book,
        )
    )
    setRipeRewardsConfig()
    debt_before = ledger.userDebt(bob)

    assert teller.depositIntoGovVault(
        token, amount, 500, bob, sender=bob
    ) == amount

    assert not callback_price_desk.callback_enabled()
    assert token.balanceValue(ripe_gov_vault) == amount
    assert ripe_gov_vault.getTotalAmountForUser(bob, token) == amount
    assert token.balanceValue(simple_erc20_vault) == nested_amount
    assert simple_erc20_vault.getTotalAmountForUser(bob, token) == nested_amount
    assert ledger.getNumUserVaults(bob) == 2

    gov_user_points = ledger.userDepositPoints(bob, gov_id, token)
    gov_asset_points = ledger.assetDepositPoints(gov_id, token)
    gov_share = ripe_gov_vault.getUserLootBoxShare(bob, token)
    assert gov_asset_points.precision == 10**9
    assert gov_user_points.lastBalance == gov_share
    assert gov_asset_points.lastBalance == gov_share
    assert gov_user_points.balancePoints == 0
    assert gov_asset_points.balancePoints == 0

    nested_user_points = ledger.userDepositPoints(bob, simple_id, token)
    nested_asset_points = ledger.assetDepositPoints(simple_id, token)
    nested_share = simple_erc20_vault.getUserLootBoxShare(bob, token)
    assert nested_asset_points.precision == 10**9
    assert nested_user_points.lastBalance == (
        nested_share // nested_asset_points.precision
    )
    assert nested_asset_points.lastBalance == nested_user_points.lastBalance
    assert nested_user_points.balancePoints == 0
    assert nested_asset_points.balancePoints == 0

    assert ledger.lastTouch(bob) == boa.env.evm.patch.block_number
    assert ledger.userDebt(bob) == debt_before
    assert debt_before.amount == 0
    logs = filter_logs(teller, "TellerDeposit")
    assert [(log.vaultId, log.amount) for log in logs] == [
        (simple_id, nested_amount),
        (gov_id, amount),
    ]


def test_governance_post_clear_nested_deposit_rolls_back_after_housekeeping(
    ripe_hq,
    governance,
    simple_erc20_vault,
    ripe_gov_vault,
    bob,
    setGeneralConfig,
    setAssetConfig,
    mission_control,
    switchboard_alpha,
    teller,
    ledger,
    vault_book,
):
    token, callback_price_desk, amount, nested_amount, gov_id, simple_id = (
        _setup_governance_post_clear_callback(
            GOVERNANCE_REVERTING_PRICE_CALLBACK_SOURCE,
            "assessment_governance_reverting_price_callback",
            ripe_hq,
            governance,
            simple_erc20_vault,
            bob,
            setGeneralConfig,
            setAssetConfig,
            mission_control,
            switchboard_alpha,
            teller,
            vault_book,
        )
    )
    before = (
        token.balanceValue(bob),
        token.balanceValue(callback_price_desk),
        token.balanceValue(ripe_gov_vault),
        token.balanceValue(simple_erc20_vault),
        ripe_gov_vault.getTotalAmountForUser(bob, token),
        simple_erc20_vault.getTotalAmountForUser(bob, token),
        ledger.getNumUserVaults(bob),
        ledger.userDepositPoints(bob, gov_id, token),
        ledger.assetDepositPoints(gov_id, token),
        ledger.userDepositPoints(bob, simple_id, token),
        ledger.assetDepositPoints(simple_id, token),
        ledger.lastTouch(bob),
        ledger.userDebt(bob),
        callback_price_desk.callback_enabled(),
    )
    with pytest.raises(BoaError) as downstream:
        teller.depositIntoGovVault(token, amount, 500, bob, sender=bob)
    assert not _boa_error_has_dev_reason(
        downstream.value, "nested callback failed"
    )

    assert before == (
        token.balanceValue(bob),
        token.balanceValue(callback_price_desk),
        token.balanceValue(ripe_gov_vault),
        token.balanceValue(simple_erc20_vault),
        ripe_gov_vault.getTotalAmountForUser(bob, token),
        simple_erc20_vault.getTotalAmountForUser(bob, token),
        ledger.getNumUserVaults(bob),
        ledger.userDepositPoints(bob, gov_id, token),
        ledger.assetDepositPoints(gov_id, token),
        ledger.userDepositPoints(bob, simple_id, token),
        ledger.assetDepositPoints(simple_id, token),
        ledger.lastTouch(bob),
        ledger.userDebt(bob),
        callback_price_desk.callback_enabled(),
    )
    assert nested_amount == 1
    assert filter_logs(teller, "TellerDeposit") == []
