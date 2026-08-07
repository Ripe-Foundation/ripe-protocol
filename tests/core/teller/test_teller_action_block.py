import boa
import pytest

from constants import ZERO_ADDRESS


ADDYS_FIELDS = (
    "hq",
    "greenToken",
    "savingsGreen",
    "ripeToken",
    "ledger",
    "missionControl",
    "switchboard",
    "priceDesk",
    "vaultBook",
    "auctionHouse",
    "auctionHouseNft",
    "boardroom",
    "bondRoom",
    "creditEngine",
    "endaoment",
    "humanResources",
    "lootbox",
    "teller",
)


def _credit_engine_recorder():
    return boa.loads(
        """# @version 0.4.3
count: public(uint256)
lastUser: public(address)
lastHq: public(address)

struct Addys:
    hq: address
    greenToken: address
    savingsGreen: address
    ripeToken: address
    ledger: address
    missionControl: address
    switchboard: address
    priceDesk: address
    vaultBook: address
    auctionHouse: address
    auctionHouseNft: address
    boardroom: address
    bondRoom: address
    creditEngine: address
    endaoment: address
    humanResources: address
    lootbox: address
    teller: address

@external
def updateDebtForUser(_user: address, _a: Addys) -> bool:
    self.count += 1
    self.lastUser = _user
    self.lastHq = _a.hq
    return True
""",
        name="teller_housekeeping_credit_engine_recorder",
    )


@pytest.mark.parametrize(
    ("is_higher_risk", "subject_fixture"),
    (
        pytest.param(False, "alice", id="low-risk-user-subject"),
        pytest.param(True, "bob", id="high-risk-user-subject"),
    ),
)
def test_teller_route_housekeeping_risk_and_subject_matrix(
    request,
    is_higher_risk,
    subject_fixture,
    teller,
    ledger,
    mission_control,
    switchboard_alpha,
    deleverage,
    alice,
    bob,
):
    mission_control.setShouldCheckLastTouch(True, sender=switchboard_alpha.address)
    subject = request.getfixturevalue(subject_fixture)
    decoy = bob if subject == alice else alice

    teller.performHousekeeping(
        is_higher_risk,
        subject,
        False,
        sender=deleverage.address,
    )
    assert ledger.lastTouch(subject) == boa.env.evm.patch.block_number
    assert ledger.lastTouch(decoy) == 0

    if is_higher_risk:
        with boa.reverts("one action per block"):
            teller.performHousekeeping(
                True,
                subject,
                False,
                sender=deleverage.address,
            )
    else:
        teller.performHousekeeping(
            False,
            subject,
            False,
            sender=deleverage.address,
        )
        assert ledger.lastTouch(subject) == boa.env.evm.patch.block_number


@pytest.mark.parametrize("should_update_debt", [False, True])
def test_teller_route_housekeeping_debt_update_matrix(
    should_update_debt,
    teller,
    deleverage,
    alice,
):
    recorder = _credit_engine_recorder()
    supplied = _addys_bundle(teller, creditEngine=recorder.address)
    teller.performHousekeeping(
        False,
        alice,
        should_update_debt,
        supplied,
        sender=deleverage.address,
    )
    assert recorder.count() == int(should_update_debt)
    if should_update_debt:
        assert recorder.lastUser() == alice
        assert recorder.lastHq() == supplied[0]


def _addys_bundle(teller, **replacements):
    current = teller.getAddys()
    return tuple(
        replacements.get(field, getattr(current, field))
        for field in ADDYS_FIELDS
    )


@pytest.mark.parametrize(
    "caller_fixture",
    [
        "deleverage",
        "credit_engine",
        "simple_erc20_vault",
        "switchboard_alpha",
    ],
)
def test_external_housekeeping_preserves_broad_valid_ripe_caller_boundary(
    request,
    caller_fixture,
    teller,
    ledger,
    alice,
):
    caller = request.getfixturevalue(caller_fixture)
    teller.performHousekeeping(False, alice, False, sender=caller.address)
    assert ledger.lastTouch(alice) == boa.env.evm.patch.block_number


def test_external_housekeeping_rejects_invalid_caller(
    teller,
    ledger,
    alice,
    bob,
):
    with boa.reverts("only ripe addr allowed"):
        teller.performHousekeeping(False, alice, False, sender=bob)
    assert ledger.lastTouch(alice) == 0


def test_external_housekeeping_valid_caller_can_select_victim_and_risk_flag(
    teller,
    ledger,
    mission_control,
    switchboard_alpha,
    deleverage,
    alice,
    bob,
):
    mission_control.setShouldCheckLastTouch(
        True,
        sender=switchboard_alpha.address,
    )

    # The preserved boundary lets the valid caller arm Alice as low risk.
    teller.performHousekeeping(
        False,
        alice,
        False,
        sender=deleverage.address,
    )
    with boa.reverts("one action per block"):
        teller.performHousekeeping(
            True,
            alice,
            False,
            sender=deleverage.address,
        )

    # The caller can independently select another victim in the same block.
    teller.performHousekeeping(
        True,
        bob,
        False,
        sender=deleverage.address,
    )
    assert ledger.lastTouch(alice) == ledger.lastTouch(bob)


@pytest.mark.parametrize("is_vault", [False, True])
def test_external_housekeeping_preserves_underscore_exemption_but_writes_touch(
    teller,
    ledger,
    mission_control,
    switchboard_alpha,
    mock_undy_v2,
    deleverage,
    alice,
    is_vault,
):
    mission_control.setShouldCheckLastTouch(
        True,
        sender=switchboard_alpha.address,
    )
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_undy_v2.setAllAddressesAreVaults(is_vault)
    mock_undy_v2.setIsUserWallet(not is_vault)

    teller.performHousekeeping(
        True,
        alice,
        False,
        sender=deleverage.address,
    )
    teller.performHousekeeping(
        True,
        alice,
        False,
        sender=deleverage.address,
    )
    assert ledger.lastTouch(alice) == boa.env.evm.patch.block_number


def test_external_housekeeping_preserves_caller_supplied_addys_propagation(
    teller,
    ledger,
    ripe_hq_deploy,
    deleverage,
    alice,
):
    alternate_ledger = boa.load(
        "contracts/data/Ledger.vy",
        ripe_hq_deploy,
        ZERO_ADDRESS,
        ZERO_ADDRESS,
        name="caller_selected_action_block_ledger",
    )
    supplied = _addys_bundle(teller, ledger=alternate_ledger.address)

    teller.performHousekeeping(
        False,
        alice,
        False,
        supplied,
        sender=deleverage.address,
    )

    assert alternate_ledger.lastTouch(alice) == boa.env.evm.patch.block_number
    assert ledger.lastTouch(alice) == 0


def test_external_housekeeping_rolls_back_touch_when_supplied_addys_fail_later(
    teller,
    ledger,
    deleverage,
    alice,
):
    supplied = _addys_bundle(teller, priceDesk=ZERO_ADDRESS)

    with boa.reverts():
        teller.performHousekeeping(
            False,
            alice,
            False,
            supplied,
            sender=deleverage.address,
        )
    assert ledger.lastTouch(alice) == 0


def test_external_housekeeping_preserves_zero_address_victim(
    teller,
    ledger,
    deleverage,
):
    teller.performHousekeeping(
        False,
        ZERO_ADDRESS,
        False,
        sender=deleverage.address,
    )
    assert ledger.lastTouch(ZERO_ADDRESS) == boa.env.evm.patch.block_number


TRUSTED_DEPOSIT_ENCLOSING_FAILURE_SOURCE = """
# @version 0.4.3

interface Teller:
    def depositFromTrusted(
        _user: address,
        _vaultId: uint256,
        _asset: address,
        _amount: uint256,
        _lockDuration: uint256,
    ) -> uint256: nonpayable
    def performHousekeeping(
        _isHigherRisk: bool,
        _user: address,
        _shouldUpdateDebt: bool,
    ): nonpayable

@external
def depositHousekeepAndFail(
    _teller: address,
    _user: address,
    _vaultId: uint256,
    _asset: address,
    _amount: uint256,
):
    _: uint256 = extcall Teller(_teller).depositFromTrusted(
        _user,
        _vaultId,
        _asset,
        _amount,
        0,
    )
    extcall Teller(_teller).performHousekeeping(False, _user, False)
    raise "enclosing failure"
"""


def test_l1_trusted_deposit_does_not_arm_then_explicit_touch_and_enclosing_revert(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    credit_engine,
    bob,
    alice,
    setGeneralConfig,
    setAssetConfig,
    vault_book,
    teller,
    ledger,
):
    setGeneralConfig()
    setAssetConfig(alpha_token)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    amount = 25 * 10**18
    alpha_token.transfer(
        credit_engine,
        amount * 2,
        sender=alpha_token_whale,
    )
    alpha_token.approve(
        teller,
        amount * 2,
        sender=credit_engine.address,
    )

    assert (
        teller.depositFromTrusted(
            bob,
            vault_id,
            alpha_token,
            amount,
            0,
            sender=credit_engine.address,
        )
        == amount
    )
    assert ledger.lastTouch(bob) == 0

    teller.performHousekeeping(
        False,
        bob,
        False,
        sender=credit_engine.address,
    )
    assert ledger.lastTouch(bob) == boa.env.evm.patch.block_number

    assert boa.env.lookup_contract(credit_engine.address) is credit_engine
    try:
        with boa.env.anchor():
            producer = boa.loads(
                TRUSTED_DEPOSIT_ENCLOSING_FAILURE_SOURCE,
                name="l1_trusted_deposit_enclosing_failure",
                override_address=credit_engine.address,
            )
            with boa.reverts("enclosing failure"):
                producer.depositHousekeepAndFail(
                    teller,
                    alice,
                    vault_id,
                    alpha_token,
                    amount,
                )

            assert ledger.lastTouch(alice) == 0
            assert (
                simple_erc20_vault.getTotalAmountForUser(alice, alpha_token)
                == 0
            )
            assert alpha_token.balanceOf(credit_engine) == amount
            assert alpha_token.balanceOf(simple_erc20_vault) == amount
    finally:
        boa.env.register_contract(credit_engine.address, credit_engine)
    assert boa.env.lookup_contract(credit_engine.address) is credit_engine


def test_initial_robinhood_underscore_omission_cannot_create_exemption(
    teller,
    ledger,
    mission_control,
    switchboard_alpha,
    deleverage,
    alice,
):
    assert mission_control.underscoreRegistry() == ZERO_ADDRESS
    mission_control.setShouldCheckLastTouch(
        True,
        sender=switchboard_alpha.address,
    )

    teller.performHousekeeping(
        True,
        alice,
        False,
        sender=deleverage.address,
    )
    with boa.reverts():
        teller.performHousekeeping(
            True,
            alice,
            False,
            sender=deleverage.address,
        )
    assert ledger.lastTouch(alice) == boa.env.evm.patch.block_number


def test_selected_real_curve_component_is_inert_without_reference_pool_config(
    teller,
    ledger,
    price_desk,
    curve_prices,
    governance,
    deleverage,
    alice,
):
    """ID 2 makes Teller call real CurvePrices, but the empty ref config is inert."""
    with boa.env.anchor():
        if price_desk.getAddr(2) != curve_prices.address:
            assert price_desk.startAddressUpdateToRegistry(
                2, curve_prices, sender=governance.address
            )
            boa.env.time_travel(blocks=price_desk.registryChangeTimeLock() + 1)
            assert price_desk.confirmAddressUpdateToRegistry(
                2, sender=governance.address
            )

        config = curve_prices.greenRefPoolConfig()
        assert config.pool == ZERO_ADDRESS
        assert config.lpToken == ZERO_ADDRESS
        before = curve_prices.getCurrentGreenPoolStatus()
        assert before.weightedRatio == 0
        assert before.numBlocksInDanger == 0

        teller.performHousekeeping(
            False,
            alice,
            False,
            sender=deleverage.address,
        )

        after = curve_prices.getCurrentGreenPoolStatus()
        assert after == before
        assert ledger.lastTouch(alice) == boa.env.evm.patch.block_number
