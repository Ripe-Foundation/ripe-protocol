import boa
import pytest

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS


M3_BACKING_OBSERVER_SOURCE = """
# @version 0.4.3

backing_value: immutable(uint256)

@deploy
def __init__(_backing_value: uint256):
    backing_value = _backing_value

@view
@external
def backing() -> uint256:
    return backing_value
"""


M3_CONTAINMENT_VAULT_SOURCE = """
# @version 0.4.3

asset: immutable(address)
nominal_amount: immutable(uint256)
backing_observer: immutable(address)
true_zero: immutable(bool)

@deploy
def __init__(
    _asset: address,
    _nominal_amount: uint256,
    _backing_observer: address,
    _true_zero: bool,
):
    asset = _asset
    nominal_amount = _nominal_amount
    backing_observer = _backing_observer
    true_zero = _true_zero

@view
@external
def numUserAssets(_user: address) -> uint256:
    return 2

@view
@external
def getUserAssetAndAmountAtIndex(
    _user: address,
    _index: uint256,
) -> (address, uint256):
    if _index != 1 or true_zero:
        return empty(address), 0

    success: bool = False
    response: Bytes[65] = b""
    success, response = raw_call(
        backing_observer,
        method_id("backing()", output_type=Bytes[4]),
        max_outsize=65,
        is_static_call=True,
        revert_on_failure=False,
    )
    if not success or len(response) != 32:
        return asset, 0

    observed_backing: uint256 = abi_decode(response, uint256)
    if observed_backing < nominal_amount:
        return asset, 0
    return asset, nominal_amount
"""


M3_GUARDED_PRICE_DESK_SOURCE = """
# @version 0.4.3

unsafe_asset: immutable(address)
value_numerator: immutable(uint256)
value_denominator: immutable(uint256)

@deploy
def __init__(
    _unsafe_asset: address,
    _value_numerator: uint256,
    _value_denominator: uint256,
):
    unsafe_asset = _unsafe_asset
    value_numerator = _value_numerator
    value_denominator = _value_denominator

@view
@external
def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool) -> uint256:
    assert _asset != unsafe_asset, "unsafe price lookup"
    return _amount * value_numerator // value_denominator

@view
@external
def getAddr(_regId: uint256) -> address:
    return empty(address)
"""


def _m3_backing_observer(failure_kind, backing_value):
    observer = boa.env.generate_address()
    if failure_kind == "observed":
        implementation = boa.loads(
            M3_BACKING_OBSERVER_SOURCE,
            backing_value,
            name="m3_backing_observer",
            override_address=boa.env.generate_address(),
        )
        boa.env.set_code(observer, boa.env.get_code(implementation.address))
    elif failure_kind == "failed":
        boa.env.set_code(observer, bytes.fromhex("60006000fd"))
    elif failure_kind == "malformed":
        # Return one byte instead of the one ABI word required by `backing()`.
        boa.env.set_code(
            observer,
            bytes.fromhex("600160005360016000f3"),
        )
    elif failure_kind != "missing":
        raise AssertionError(f"unknown backing observation: {failure_kind}")
    return observer


def _m3_containment_vault(
    asset,
    nominal_amount,
    failure_kind="observed",
    backing_value=0,
    true_zero=False,
):
    observer = _m3_backing_observer(failure_kind, backing_value)
    vault = boa.loads(
        M3_CONTAINMENT_VAULT_SOURCE,
        asset.address,
        nominal_amount,
        observer,
        true_zero,
        name="m3_containment_vault",
        override_address=boa.env.generate_address(),
    )
    return vault, observer


def _m3_register_vault(vault_book, governance, vault):
    assert vault_book.startAddNewAddressToRegistry(
        vault,
        "M3 disposable containment vault",
        sender=governance.address,
    )
    boa.env.time_travel(blocks=vault_book.registryChangeTimeLock())
    return vault_book.confirmNewAddressToRegistry(
        vault,
        sender=governance.address,
    )


def _m3_add_position(
    user,
    asset,
    vault,
    debt_terms,
    vault_book,
    governance,
    setAssetConfig,
    ledger,
    teller,
):
    vault_id = _m3_register_vault(vault_book, governance, vault)
    setAssetConfig(
        asset,
        _vaultIds=[vault_id],
        _debtTerms=debt_terms,
    )
    ledger.addVaultToUser(user, vault_id, sender=teller.address)
    return vault_id


def _m3_install_guarded_price_desk(
    price_desk,
    unsafe_asset,
    numerator=1,
    denominator=1,
):
    guarded = boa.loads(
        M3_GUARDED_PRICE_DESK_SOURCE,
        unsafe_asset.address,
        numerator,
        denominator,
        name="m3_guarded_price_desk",
        override_address=boa.env.generate_address(),
    )
    boa.env.set_code(price_desk.address, boa.env.get_code(guarded.address))


@pytest.mark.parametrize(
    "failure_kind",
    (
        pytest.param("observed", id="one-unit-deficit"),
        pytest.param("missing", id="missing-observer"),
        pytest.param("failed", id="failed-observer"),
        pytest.param("malformed", id="malformed-observer"),
    ),
)
def test_unsafe_backing_failures_keep_terms_with_zero_capacity(
    failure_kind,
    alpha_token,
    bob,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    vault_book,
    governance,
    ledger,
    teller,
    credit_engine,
    price_desk,
):
    setGeneralConfig()
    setGeneralDebtConfig()
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=60_00,
        _liqThreshold=70_00,
        _liqFee=10_00,
        _borrowRate=5_00,
        _daowry=1_00,
    )
    vault, _ = _m3_containment_vault(
        alpha_token,
        nominal_amount=1,
        failure_kind=failure_kind,
        backing_value=0,
    )
    _m3_add_position(
        bob,
        alpha_token,
        vault,
        debt_terms,
        vault_book,
        governance,
        setAssetConfig,
        ledger,
        teller,
    )
    _m3_install_guarded_price_desk(price_desk, alpha_token)

    assert vault.getUserAssetAndAmountAtIndex(bob, 1) == (
        alpha_token.address,
        0,
    )
    preview = credit_engine.getUserBorrowTerms(bob, True)
    assert preview.collateralVal == 0
    assert preview.totalMaxDebt == 0
    assert preview.debtTerms.ltv == 50_00
    assert preview.debtTerms.redemptionThreshold == 60_00
    assert preview.debtTerms.liqThreshold == 70_00
    assert preview.debtTerms.liqFee == 10_00
    assert preview.debtTerms.borrowRate == 5_00
    assert preview.debtTerms.daowry == 1_00
    assert credit_engine.getCollateralValue(bob) == 0
    assert credit_engine.getMaxBorrowAmount(bob) == 0

    debt_amount = 1 * EIGHTEEN_DECIMALS
    user_debt = (
        debt_amount,
        debt_amount,
        debt_terms,
        boa.env.evm.patch.timestamp,
        False,
    )
    ledger.setUserDebt(
        bob,
        user_debt,
        0,
        (0, 0),
        sender=credit_engine.address,
    )

    state_debt, state_terms, _ = credit_engine.getLatestUserDebtAndTerms(
        bob,
        False,
    )
    assert state_debt.amount == debt_amount
    assert state_terms == preview
    assert not credit_engine.hasGoodDebtHealth(bob)
    assert credit_engine.canLiquidateUser(bob)
    assert credit_engine.canRedeemUserCollateral(bob)
    assert credit_engine.getLiquidationThreshold(bob) == (
        debt_amount * 100_00 // 70_00
    )
    assert credit_engine.getRedemptionThreshold(bob) == (
        debt_amount * 100_00 // 60_00
    )


def test_true_zero_nominal_position_remains_absent(
    alpha_token,
    bob,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    vault_book,
    governance,
    ledger,
    teller,
    credit_engine,
):
    setGeneralConfig()
    setGeneralDebtConfig()
    debt_terms = createDebtTerms()
    vault, _ = _m3_containment_vault(
        alpha_token,
        nominal_amount=0,
        failure_kind="missing",
        true_zero=True,
    )
    _m3_add_position(
        bob,
        alpha_token,
        vault,
        debt_terms,
        vault_book,
        governance,
        setAssetConfig,
        ledger,
        teller,
    )

    assert vault.getUserAssetAndAmountAtIndex(bob, 1) == (
        ZERO_ADDRESS,
        0,
    )
    preview = credit_engine.getUserBorrowTerms(bob, True)
    assert preview.collateralVal == 0
    assert preview.totalMaxDebt == 0
    assert preview.debtTerms.ltv == 0
    assert preview.debtTerms.redemptionThreshold == 0
    assert preview.debtTerms.liqThreshold == 0
    assert preview.debtTerms.liqFee == 0
    assert preview.debtTerms.borrowRate == 0
    assert preview.debtTerms.daowry == 0


def test_safe_backing_surplus_values_only_nominal_user_amount(
    alpha_token,
    bob,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    vault_book,
    governance,
    ledger,
    teller,
    credit_engine,
    mock_price_source,
):
    setGeneralConfig()
    setGeneralDebtConfig()
    debt_terms = createDebtTerms(_ltv=50_00)
    nominal_amount = 1 * EIGHTEEN_DECIMALS
    vault, _ = _m3_containment_vault(
        alpha_token,
        nominal_amount=nominal_amount,
        failure_kind="observed",
        backing_value=3 * nominal_amount,
    )
    _m3_add_position(
        bob,
        alpha_token,
        vault,
        debt_terms,
        vault_book,
        governance,
        setAssetConfig,
        ledger,
        teller,
    )
    mock_price_source.setPrice(alpha_token, 2 * EIGHTEEN_DECIMALS)

    assert vault.getUserAssetAndAmountAtIndex(bob, 1) == (
        alpha_token.address,
        nominal_amount,
    )
    preview = credit_engine.getUserBorrowTerms(bob, True)
    assert preview.collateralVal == 2 * nominal_amount
    assert preview.totalMaxDebt == nominal_amount


def test_mixed_safe_collateral_remains_exact_and_liquidatable(
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bob,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    vault_book,
    governance,
    ledger,
    teller,
    credit_engine,
    price_desk,
):
    setGeneralConfig()
    setGeneralDebtConfig()
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=60_00,
        _liqThreshold=70_00,
        _liqFee=10_00,
        _borrowRate=5_00,
        _daowry=0,
    )
    setAssetConfig(alpha_token, _vaultIds=[3], _debtTerms=debt_terms)
    safe_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(
        bob,
        safe_amount,
        alpha_token,
        alpha_token_whale,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)

    unsafe_vault, _ = _m3_containment_vault(
        bravo_token,
        nominal_amount=1,
        failure_kind="observed",
        backing_value=0,
    )
    _m3_add_position(
        bob,
        bravo_token,
        unsafe_vault,
        debt_terms,
        vault_book,
        governance,
        setAssetConfig,
        ledger,
        teller,
    )

    initial_debt = 50 * EIGHTEEN_DECIMALS
    assert teller.borrow(
        initial_debt,
        bob,
        False,
        sender=bob,
    ) == initial_debt

    # The safe asset is repriced to one half. The guarded desk proves the
    # unsafe zero-amount asset is not consulted.
    _m3_install_guarded_price_desk(
        price_desk,
        bravo_token,
        numerator=1,
        denominator=2,
    )
    preview = credit_engine.getUserBorrowTerms(bob, True)
    assert preview.collateralVal == safe_amount // 2
    assert preview.totalMaxDebt == safe_amount // 4
    assert preview.debtTerms.ltv == 50_00
    assert preview.debtTerms.liqThreshold == 70_00
    assert not credit_engine.hasGoodDebtHealth(bob)
    assert credit_engine.canLiquidateUser(bob)

    assert not credit_engine.updateDebtForUser(
        bob,
        sender=credit_engine.address,
    )
    stored_debt = ledger.userDebt(bob)
    assert stored_debt.amount == initial_debt
    assert stored_debt.debtTerms.ltv == preview.debtTerms.ltv
    assert stored_debt.debtTerms.liqThreshold == preview.debtTerms.liqThreshold


def test_existing_stab_and_basic_vault_empty_zero_remain_absent(
    alpha_token,
    bob,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    ledger,
    teller,
    credit_engine,
    stability_pool,
    simple_erc20_vault,
):
    setGeneralConfig()
    setGeneralDebtConfig()
    setAssetConfig(alpha_token, _vaultIds=[1, 3], _debtTerms=createDebtTerms())
    ledger.addVaultToUser(bob, 1, sender=teller.address)
    ledger.addVaultToUser(bob, 3, sender=teller.address)

    assert stability_pool.getUserAssetAndAmountAtIndex(bob, 1) == (
        ZERO_ADDRESS,
        0,
    )
    assert simple_erc20_vault.getUserAssetAndAmountAtIndex(bob, 1) == (
        ZERO_ADDRESS,
        0,
    )
    # These legacy vaults expose no iterable entries when empty. The generic
    # true-zero containment case above exercises CreditEngine exclusion.
    assert stability_pool.numUserAssets(bob) == 0
    assert simple_erc20_vault.numUserAssets(bob) == 0


def test_backing_observation_mutation_fails_closed(
    alpha_token,
    bob,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    vault_book,
    governance,
    ledger,
    teller,
    credit_engine,
    mock_price_source,
):
    setGeneralConfig()
    setGeneralDebtConfig()
    debt_terms = createDebtTerms()
    nominal_amount = 1 * EIGHTEEN_DECIMALS
    vault, observer = _m3_containment_vault(
        alpha_token,
        nominal_amount=nominal_amount,
        failure_kind="observed",
        backing_value=nominal_amount,
    )
    _m3_add_position(
        bob,
        alpha_token,
        vault,
        debt_terms,
        vault_book,
        governance,
        setAssetConfig,
        ledger,
        teller,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)

    safe_preview = credit_engine.getUserBorrowTerms(bob, True)
    assert safe_preview.collateralVal == nominal_amount
    assert safe_preview.totalMaxDebt == nominal_amount // 2

    boa.env.set_code(observer, bytes.fromhex("60006000fd"))
    assert vault.getUserAssetAndAmountAtIndex(bob, 1) == (
        alpha_token.address,
        0,
    )
    unsafe_preview = credit_engine.getUserBorrowTerms(bob, True)
    assert unsafe_preview.collateralVal == 0
    assert unsafe_preview.totalMaxDebt == 0
    assert unsafe_preview.debtTerms.liqThreshold == debt_terms[2]


def test_zero_amount_containment_path_has_bounded_gas(
    alpha_token,
    bob,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    vault_book,
    governance,
    ledger,
    teller,
    credit_engine,
    mock_price_source,
):
    setGeneralConfig()
    setGeneralDebtConfig()
    debt_terms = createDebtTerms()
    nominal_amount = 1 * EIGHTEEN_DECIMALS
    vault, observer = _m3_containment_vault(
        alpha_token,
        nominal_amount=nominal_amount,
        failure_kind="observed",
        backing_value=nominal_amount,
    )
    _m3_add_position(
        bob,
        alpha_token,
        vault,
        debt_terms,
        vault_book,
        governance,
        setAssetConfig,
        ledger,
        teller,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)

    gas_before_safe = boa.env.get_gas_used()
    safe_preview = credit_engine.getUserBorrowTerms(bob, True)
    safe_gas = boa.env.get_gas_used() - gas_before_safe
    assert safe_preview.collateralVal == nominal_amount

    boa.env.set_code(observer, bytes.fromhex("60006000fd"))
    gas_before_unsafe = boa.env.get_gas_used()
    unsafe_preview = credit_engine.getUserBorrowTerms(bob, True)
    unsafe_gas = boa.env.get_gas_used() - gas_before_unsafe
    assert unsafe_preview.collateralVal == 0

    assert 0 < unsafe_gas < 1_000_000
    assert unsafe_gas < safe_gas
