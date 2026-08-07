import boa
import pytest
from eth_abi import encode
from eth_utils import keccak

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


ROUTE_TOKEN_SOURCE = """# @version 0.4.3

from ethereum.ercs import IERC20

balances: HashMap[address, uint256]
allowances: HashMap[address, HashMap[address, uint256]]
underlying: public(address)

@external
def configure_underlying(_underlying: address):
    self.underlying = _underlying

@external
def mint(_to: address, _amount: uint256):
    self.balances[_to] += _amount

@view
@external
def balanceOf(_owner: address) -> uint256:
    return self.balances[_owner]

@view
@external
def allowance(_owner: address, _spender: address) -> uint256:
    return self.allowances[_owner][_spender]

@external
def approve(_spender: address, _amount: uint256) -> bool:
    self.allowances[msg.sender][_spender] = _amount
    return True

@internal
def _transfer(_from: address, _to: address, _amount: uint256):
    assert self.balances[_from] >= _amount
    self.balances[_from] -= _amount
    self.balances[_to] += _amount

@external
def transfer(_to: address, _amount: uint256) -> bool:
    self._transfer(msg.sender, _to, _amount)
    return True

@external
def transferFrom(_from: address, _to: address, _amount: uint256) -> bool:
    if msg.sender != _from:
        assert self.allowances[_from][msg.sender] >= _amount
        self.allowances[_from][msg.sender] -= _amount
    self._transfer(_from, _to, _amount)
    return True

@external
def deposit(_assets: uint256, _receiver: address) -> uint256:
    assert self.underlying != empty(address)
    assert extcall IERC20(self.underlying).transferFrom(msg.sender, self, _assets)
    self.balances[_receiver] += _assets
    return _assets

@external
def redeem(_shares: uint256, _receiver: address, _owner: address) -> uint256:
    assert self.balances[_owner] >= _shares
    self.balances[_owner] -= _shares
    assert extcall IERC20(self.underlying).transfer(_receiver, _shares)
    return _shares
"""


RAW_CALL_PROBE_SOURCE = """# @version 0.4.3

@external
def call_succeeds(_target: address, _data: Bytes[1024]) -> bool:
    success: bool = False
    response: Bytes[4096] = b""
    success, response = raw_call(
        _target,
        _data,
        max_outsize=4096,
        revert_on_failure=False,
    )
    return success
"""


ROUTE_SINK_SOURCE = """# @version 0.4.3

import contracts.modules.Addys as addys

struct CollateralRedemption:
    user: address
    vaultId: uint256
    asset: address
    maxGreenAmount: uint256

struct FungAuctionPurchase:
    liqUser: address
    vaultId: uint256
    asset: address
    maxGreenAmount: uint256

struct StabPoolClaim:
    stabAsset: address
    claimAsset: address
    maxUsdValue: uint256

struct StabPoolRedemption:
    claimAsset: address
    maxGreenAmount: uint256

debtUpdateCount: public(uint256)
lastDebtUser: public(address)
lastHq: public(address)

@external
def reset():
    self.debtUpdateCount = 0
    self.lastDebtUser = empty(address)
    self.lastHq = empty(address)

@external
def updateDebtForUser(_user: address, _a: addys.Addys = empty(addys.Addys)) -> bool:
    self.debtUpdateCount += 1
    self.lastDebtUser = _user
    self.lastHq = _a.hq
    return True

@view
@external
def getMaxWithdrawableForAsset(_user: address, _vaultId: uint256, _asset: address, _vaultAddr: address, _a: addys.Addys = empty(addys.Addys)) -> uint256:
    return max_value(uint256)

@external
def borrowForUser(_user: address, _greenAmount: uint256, _wantsSavingsGreen: bool, _shouldEnterStabPool: bool, _caller: address, _a: addys.Addys = empty(addys.Addys)) -> uint256:
    return _greenAmount

@external
def repayForUser(_user: address, _greenAmount: uint256, _shouldRefundSavingsGreen: bool, _caller: address, _a: addys.Addys = empty(addys.Addys)) -> bool:
    return True

@external
def depositTokensInVault(_user: address, _asset: address, _amount: uint256, _a: addys.Addys = empty(addys.Addys)) -> uint256:
    return _amount

@external
def depositTokensWithLockDuration(_user: address, _asset: address, _amount: uint256, _lockDuration: uint256, _a: addys.Addys = empty(addys.Addys)) -> uint256:
    return _amount

@external
def withdrawTokensFromVault(_user: address, _asset: address, _amount: uint256, _recipient: address, _a: addys.Addys = empty(addys.Addys)) -> (uint256, bool):
    return _amount, True

@view
@external
def getVaultDataOnDeposit(_user: address, _asset: address) -> (bool, uint256, uint256, uint256):
    return False, 0, 0, 0

@view
@external
def getTotalAmountForUser(_user: address, _asset: address) -> uint256:
    return max_value(uint256)

@view
@external
def isPaused() -> bool:
    return False

@external
def adjustLock(_user: address, _asset: address, _newLockDuration: uint256, _a: addys.Addys = empty(addys.Addys)):
    pass

@external
def releaseLock(_user: address, _asset: address, _a: addys.Addys = empty(addys.Addys)):
    pass

@external
def updateDepositPoints(_user: address, _vaultId: uint256, _vaultAddr: address, _asset: address, _a: addys.Addys = empty(addys.Addys)):
    pass

@external
def claimLootForUser(_user: address, _caller: address, _shouldStake: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256:
    return 1

@external
def claimLootForManyUsers(_users: DynArray[address, 25], _caller: address, _shouldStake: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256:
    return 1

@external
def liquidateUser(_liqUser: address, _keeper: address, _wantsSavingsGreen: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256:
    return 1

@external
def liquidateManyUsers(_liqUsers: DynArray[address, 50], _keeper: address, _wantsSavingsGreen: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256:
    return 1

@external
def buyManyFungibleAuctions(_purchases: DynArray[FungAuctionPurchase, 20], _greenAmount: uint256, _recipient: address, _caller: address, _shouldTransferBalance: bool, _shouldRefundSavingsGreen: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256:
    return min(_greenAmount, 1)

@external
def redeemCollateralFromMany(_redemptions: DynArray[CollateralRedemption, 20], _greenAmount: uint256, _recipient: address, _caller: address, _shouldTransferBalance: bool, _shouldRefundSavingsGreen: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256:
    return min(_greenAmount, 1)

@external
def claimManyFromStabilityPool(_claimer: address, _claims: DynArray[StabPoolClaim, 15], _caller: address, _shouldAutoDeposit: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256:
    return 1

@external
def redeemManyFromStabilityPool(_redemptions: DynArray[StabPoolRedemption, 15], _greenAmount: uint256, _recipient: address, _caller: address, _shouldAutoDeposit: bool, _shouldRefundSavingsGreen: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256:
    return min(_greenAmount, 1)

@external
def purchaseRipeBond(_recipient: address, _paymentAsset: address, _paymentAmount: uint256, _lockDuration: uint256, _caller: address, _a: addys.Addys = empty(addys.Addys)) -> uint256:
    return _paymentAmount
"""


def _route_sink(name):
    return boa.loads(
        ROUTE_SINK_SOURCE,
        name=name,
    )


def _replace_hq_address(ripe_hq, governance, registry_id, replacement):
    assert ripe_hq.startAddressUpdateToRegistry(
        registry_id,
        replacement,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=ripe_hq.registryChangeTimeLock())
    assert ripe_hq.confirmAddressUpdateToRegistry(
        registry_id,
        sender=governance.address,
    )
    assert ripe_hq.getAddr(registry_id) == replacement.address


@pytest.fixture
def teller_route_matrix_env(
    ripe_hq,
    governance,
    teller,
    ledger,
    mission_control,
    switchboard_alpha,
    registerVault,
    setGeneralConfig,
    setAssetConfig,
    setUserConfig,
    setUserDelegation,
    mock_undy_v2,
    bob,
    alice,
    charlie,
):
    # Keep registry rewrites and test-only user permissions local even if this
    # module is collected without the repository's autouse Boa anchor plugin.
    with boa.env.anchor():
        setGeneralConfig()
        asset = boa.loads(ROUTE_TOKEN_SOURCE, name="route_matrix_asset")
        green = boa.loads(ROUTE_TOKEN_SOURCE, name="route_matrix_green")
        savings = boa.loads(ROUTE_TOKEN_SOURCE, name="route_matrix_savings")
        savings.configure_underlying(green)

        vault = _route_sink("route_matrix_vault")
        credit_engine = _route_sink("route_matrix_credit_engine")
        auction_house = _route_sink("route_matrix_auction_house")
        bond_room = _route_sink("route_matrix_bond_room")
        lootbox = _route_sink("route_matrix_lootbox")
        credit_redeem = _route_sink("route_matrix_credit_redeem")
        vault_id = registerVault(vault, "Teller route matrix vault")

        mission_control.setCoreRipeGovVaultId(
            vault_id,
            sender=switchboard_alpha.address,
        )
        mission_control.setPreferredStabVaultId(
            vault_id,
            sender=switchboard_alpha.address,
        )
        mission_control.setShouldCheckLastTouch(
            True,
            sender=switchboard_alpha.address,
        )
        # Bob remains an ordinary account for last-touch enforcement. The mock
        # registry recognizes Charlie as an Underscore protocol caller so the
        # gov-vault/lock routes can exercise _user != msg.sender as well.
        mission_control.setUnderscoreRegistry(
            mock_undy_v2.address,
            sender=switchboard_alpha.address,
        )
        mock_undy_v2.setAllAddressesAreVaults(False)
        mock_undy_v2.setIsUserWallet(False)
        setUserConfig(
            bob,
            _canAnyoneDeposit=True,
            _canAnyoneRepayDebt=True,
            _canAnyoneBondForUser=True,
        )
        setUserDelegation(
            bob,
            charlie,
            _canWithdraw=True,
            _canBorrow=True,
            _canClaimFromStabPool=True,
            _canClaimLoot=True,
        )
        setAssetConfig(asset, _vaultIds=[vault_id])
        setAssetConfig(savings, _vaultIds=[vault_id])

        replacements = (
            (1, green),
            (2, savings),
            (9, auction_house),
            (12, bond_room),
            (13, credit_engine),
            (16, lootbox),
            (19, credit_redeem),
        )
        for registry_id, replacement in replacements:
            _replace_hq_address(
                ripe_hq,
                governance,
                registry_id,
                replacement,
            )

        yield {
            "asset": asset,
            "green": green,
            "savings": savings,
            "vault": vault,
            "vault_id": vault_id,
            "credit_engine": credit_engine,
            "teller": teller,
            "ledger": ledger,
            "bob": bob,
            "alice": alice,
            "charlie": charlie,
            "ripe_hq": ripe_hq,
        }


ROUTE_CASES = (
    pytest.param("deposit", False, "user", True, id="deposit"),
    pytest.param("depositMany", False, "user", True, id="depositMany"),
    pytest.param(
        "convertToSavingsGreenAndDepositIntoStabPool",
        False,
        "user",
        True,
        id="convertToSavingsGreenAndDepositIntoStabPool",
    ),
    pytest.param("depositIntoGovVault", False, "user", True, id="depositIntoGovVault"),
    pytest.param("claimLoot", False, "user", True, id="claimLoot"),
    pytest.param("adjustLock", False, "user", True, id="adjustLock"),
    pytest.param("releaseLock", False, "user", True, id="releaseLock"),
    pytest.param("withdraw", True, "user", True, id="withdraw"),
    pytest.param("withdrawMany", True, "user", True, id="withdrawMany"),
    pytest.param("rebalance", True, "user", True, id="rebalance"),
    pytest.param(
        "claimManyFromStabilityPool",
        True,
        "user",
        True,
        id="claimManyFromStabilityPool",
    ),
    pytest.param("borrow", True, "user", False, id="borrow"),
    pytest.param("repay", False, "user", False, id="repay"),
    pytest.param(
        "redeemCollateralFromMany",
        False,
        "recipient",
        True,
        id="redeemCollateralFromMany",
    ),
    pytest.param(
        "buyManyFungibleAuctions",
        False,
        "recipient",
        True,
        id="buyManyFungibleAuctions",
    ),
    pytest.param(
        "redeemManyFromStabilityPool",
        False,
        "recipient",
        True,
        id="redeemManyFromStabilityPool",
    ),
    pytest.param("purchaseRipeBond", False, "recipient", True, id="purchaseRipeBond"),
    pytest.param("liquidateUser", False, "caller", True, id="liquidateUser"),
    pytest.param(
        "liquidateManyUsers",
        False,
        "caller",
        True,
        id="liquidateManyUsers",
    ),
    pytest.param(
        "claimLootForManyUsers",
        False,
        "caller",
        True,
        id="claimLootForManyUsers",
    ),
)


def _fund_and_approve(token, owner, teller, amount=10):
    token.mint(owner, amount)
    token.approve(teller, amount, sender=owner)


def _route_subject(env, subject_kind):
    if subject_kind == "recipient":
        return env["alice"]
    if subject_kind == "caller":
        return env["charlie"]
    return env["bob"]


def _invoke_teller_route(route, env):
    teller = env["teller"]
    asset = env["asset"]
    green = env["green"]
    vault = env["vault"]
    vault_id = env["vault_id"]
    user = env["bob"]
    caller = env["charlie"]
    recipient = env["alice"]
    amount = 10

    if route == "deposit":
        _fund_and_approve(asset, caller, teller, amount)
        return teller.deposit(asset, amount, user, vault, sender=caller)
    if route == "depositMany":
        _fund_and_approve(asset, caller, teller, amount)
        return teller.depositMany(
            user,
            [(asset.address, amount, vault.address, 0)],
            sender=caller,
        )
    if route == "convertToSavingsGreenAndDepositIntoStabPool":
        _fund_and_approve(green, caller, teller, amount)
        return teller.convertToSavingsGreenAndDepositIntoStabPool(
            user,
            amount,
            sender=caller,
        )
    if route == "depositIntoGovVault":
        _fund_and_approve(asset, caller, teller, amount)
        return teller.depositIntoGovVault(asset, amount, 1, user, sender=caller)
    if route == "claimLoot":
        return teller.claimLoot(user, False, sender=caller)
    if route == "adjustLock":
        return teller.adjustLock(asset, 1, user, sender=caller)
    if route == "releaseLock":
        return teller.releaseLock(asset, user, sender=caller)
    if route == "withdraw":
        return teller.withdraw(asset, 1, user, vault, sender=caller)
    if route == "withdrawMany":
        return teller.withdrawMany(
            user,
            [(asset.address, 1, vault.address, 0)],
            sender=caller,
        )
    if route == "rebalance":
        _fund_and_approve(asset, caller, teller, amount)
        return teller.rebalance(
            asset,
            vault_id,
            asset,
            vault_id,
            amount,
            1,
            user,
            sender=caller,
        )
    if route == "claimManyFromStabilityPool":
        return teller.claimManyFromStabilityPool(
            vault_id,
            [],
            user,
            False,
            sender=caller,
        )
    if route == "borrow":
        return teller.borrow(1, user, False, False, sender=caller)
    if route == "repay":
        _fund_and_approve(green, caller, teller, amount)
        return teller.repay(1, user, False, True, sender=caller)
    if route == "redeemCollateralFromMany":
        _fund_and_approve(green, caller, teller, amount)
        return teller.redeemCollateralFromMany(
            [],
            amount,
            False,
            False,
            True,
            recipient,
            sender=caller,
        )
    if route == "buyManyFungibleAuctions":
        _fund_and_approve(green, caller, teller, amount)
        return teller.buyManyFungibleAuctions(
            [],
            amount,
            False,
            False,
            True,
            recipient,
            sender=caller,
        )
    if route == "redeemManyFromStabilityPool":
        _fund_and_approve(green, caller, teller, amount)
        return teller.redeemManyFromStabilityPool(
            vault_id,
            [],
            amount,
            recipient,
            False,
            False,
            True,
            sender=caller,
        )
    if route == "purchaseRipeBond":
        _fund_and_approve(asset, caller, teller, amount)
        return teller.purchaseRipeBond(asset, amount, 0, recipient, sender=caller)
    if route == "liquidateUser":
        return teller.liquidateUser(recipient, False, sender=caller)
    if route == "liquidateManyUsers":
        return teller.liquidateManyUsers([recipient], False, sender=caller)
    if route == "claimLootForManyUsers":
        return teller.claimLootForManyUsers([recipient], False, sender=caller)
    raise AssertionError(f"unhandled Teller route: {route}")


@pytest.mark.parametrize(
    ("route", "is_higher_risk", "subject_kind", "should_update_debt"),
    ROUTE_CASES,
)
def test_teller_route_housekeeping_risk_and_subject_matrix(
    route,
    is_higher_risk,
    subject_kind,
    should_update_debt,
    teller_route_matrix_env,
):
    env = teller_route_matrix_env
    ledger = env["ledger"]
    subject = _route_subject(env, subject_kind)
    decoys = {env["bob"], env["alice"], env["charlie"]} - {subject}

    _invoke_teller_route(route, env)
    assert ledger.lastTouch(subject) == boa.env.evm.patch.block_number
    for decoy in decoys:
        assert ledger.lastTouch(decoy) == 0

    if is_higher_risk:
        with boa.reverts("one action per block"):
            _invoke_teller_route(route, env)
    else:
        _invoke_teller_route(route, env)
        assert ledger.lastTouch(subject) == boa.env.evm.patch.block_number


@pytest.mark.parametrize(
    ("route", "is_higher_risk", "subject_kind", "should_update_debt"),
    ROUTE_CASES,
)
def test_teller_route_housekeeping_debt_update_matrix(
    route,
    is_higher_risk,
    subject_kind,
    should_update_debt,
    teller_route_matrix_env,
):
    env = teller_route_matrix_env
    recorder = env["credit_engine"]
    subject = _route_subject(env, subject_kind)
    recorder.reset()
    _invoke_teller_route(route, env)
    assert recorder.debtUpdateCount() == int(should_update_debt)
    if should_update_debt:
        assert recorder.lastDebtUser() == subject
        assert recorder.lastHq() == env["ripe_hq"].address


@pytest.mark.parametrize(
    ("route", "signature", "types"),
    (
        pytest.param(
            "redeemCollateralFromMany",
            (
                "redeemCollateralFromMany((address,uint256,address,uint256)[],"
                "uint256,bool,bool,bool,address)"
            ),
            (
                "(address,uint256,address,uint256)[]",
                "uint256",
                "bool",
                "bool",
                "bool",
                "address",
            ),
            id="redeemCollateralFromMany",
        ),
        pytest.param(
            "buyManyFungibleAuctions",
            (
                "buyManyFungibleAuctions((address,uint256,address,uint256)[],"
                "uint256,bool,bool,bool,address)"
            ),
            (
                "(address,uint256,address,uint256)[]",
                "uint256",
                "bool",
                "bool",
                "bool",
                "address",
            ),
            id="buyManyFungibleAuctions",
        ),
        pytest.param(
            "claimManyFromStabilityPool",
            "claimManyFromStabilityPool(uint256,(address,address,uint256)[],address,bool)",
            ("uint256", "(address,address,uint256)[]", "address", "bool"),
            id="claimManyFromStabilityPool",
        ),
        pytest.param(
            "redeemManyFromStabilityPool",
            (
                "redeemManyFromStabilityPool(uint256,(address,uint256)[],"
                "uint256,address,bool,bool,bool)"
            ),
            (
                "uint256",
                "(address,uint256)[]",
                "uint256",
                "address",
                "bool",
                "bool",
                "bool",
            ),
            id="redeemManyFromStabilityPool",
        ),
    ),
)
def test_surviving_batch_routes_are_callable_runtime_controls(
    route,
    signature,
    types,
    teller_route_matrix_env,
    teller,
):
    """Bind the same raw selector derivation to live surviving batch routes."""

    env = teller_route_matrix_env
    teller = env["teller"]
    probe = boa.loads(
        RAW_CALL_PROBE_SOURCE,
        name=f"surviving_{route}_selector_probe",
    )
    if route in ("redeemCollateralFromMany", "buyManyFungibleAuctions"):
        values = ([], 10, False, False, True, str(env["alice"]))
    elif route == "claimManyFromStabilityPool":
        values = (env["vault_id"], [], str(env["bob"]), False)
    else:
        values = (
            env["vault_id"],
            [],
            10,
            str(env["alice"]),
            False,
            False,
            True,
        )

    if route != "claimManyFromStabilityPool":
        _fund_and_approve(env["green"], probe.address, teller, 10)
    calldata = keccak(text=signature)[:4] + encode(types, values)
    assert calldata == getattr(teller, route).prepare_calldata(*values)
    assert probe.call_succeeds(teller, calldata), signature


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
