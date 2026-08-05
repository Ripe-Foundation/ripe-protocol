"""Focused Track 8 M2 behavior for the safe shared BasicVault behavior through SimpleErc20."""

import boa
import pytest

from conf_utils import filter_logs
from constants import EIGHTEEN_DECIMALS, MAX_UINT256


ADVERSARIAL_TOKEN_SOURCE = """
# @version 0.4.3

balances: HashMap[address, uint256]
allowances: HashMap[address, HashMap[address, uint256]]

transfer_mode: public(uint256)
transfer_return_mode: public(uint256)
balance_mode: public(uint256)
post_balance_mode: public(uint256)
change_balance_mode_on_transfer: public(bool)
balance_target: public(address)
callback_target: public(address)
callback_data: public(Bytes[1024])
callback_enabled: public(bool)

@external
def mint(_to: address, _amount: uint256):
    self.balances[_to] += _amount

@external
def configure_transfer(_mode: uint256):
    self.transfer_mode = _mode

@external
def configure_transfer_return(_mode: uint256):
    self.transfer_return_mode = _mode

@external
def configure_balance(
    _target: address,
    _mode: uint256,
    _post_mode: uint256,
    _change_on_transfer: bool,
):
    self.balance_target = _target
    self.balance_mode = _mode
    self.post_balance_mode = _post_mode
    self.change_balance_mode_on_transfer = _change_on_transfer

@external
def configure_callback(_target: address, _data: Bytes[1024], _enabled: bool):
    self.callback_target = _target
    self.callback_data = _data
    self.callback_enabled = _enabled

@view
@external
def balanceValue(_holder: address) -> uint256:
    return self.balances[_holder]

@view
@external
@raw_return
def balanceOf(_holder: address) -> Bytes[65]:
    if _holder == self.balance_target:
        if self.balance_mode == 1:
            raise
        if self.balance_mode == 2:
            return b""
        if self.balance_mode == 3:
            return slice(convert(self.balances[_holder], bytes32), 31, 1)
        if self.balance_mode == 4:
            return slice(convert(self.balances[_holder], bytes32), 0, 31)
        if self.balance_mode == 5:
            return concat(convert(self.balances[_holder], bytes32), b"x")
        if self.balance_mode == 6:
            return concat(convert(32, bytes32), convert(self.balances[_holder], bytes32))
    return slice(convert(self.balances[_holder], bytes32), 0, 32)

@external
def approve(_spender: address, _amount: uint256) -> bool:
    self.allowances[msg.sender][_spender] = _amount
    return True

@internal
def _move(_from: address, _to: address, _amount: uint256) -> bool:
    if self.transfer_mode == 6:
        return False
    if self.transfer_mode == 7:
        raise

    self.balances[_from] -= _amount

    if self.callback_enabled:
        raw_call(self.callback_target, self.callback_data)

    if self.transfer_mode == 0 or self.transfer_mode == 8:
        self.balances[_to] += _amount
    elif self.transfer_mode == 2:
        self.balances[_to] += _amount - 1
    elif self.transfer_mode == 3:
        self.balances[_to] += _amount * 99 // 100
    elif self.transfer_mode == 4:
        self.balances[_to] += _amount + 1
    elif self.transfer_mode == 5:
        if self.balances[_to] != 0:
            self.balances[_to] -= 1
    elif self.transfer_mode == 9:
        self.balances[_from] -= 1
        self.balances[_to] += _amount

    if self.change_balance_mode_on_transfer:
        self.balance_mode = self.post_balance_mode
    return True

@external
@raw_return
def transfer(_to: address, _amount: uint256) -> Bytes[65]:
    success: bool = self._move(msg.sender, _to, _amount)
    if self.transfer_return_mode == 1:
        return b""
    if self.transfer_return_mode == 2:
        return slice(convert(0, bytes32), 0, 32)
    if self.transfer_return_mode == 3:
        return slice(convert(2, bytes32), 0, 32)
    if self.transfer_return_mode == 4:
        return slice(convert(1, bytes32), 31, 1)
    if self.transfer_return_mode == 5:
        return concat(convert(1, bytes32), b"x")
    if self.transfer_return_mode == 6:
        return concat(convert(1, bytes32), convert(0, bytes32))
    if success:
        return slice(convert(1, bytes32), 0, 32)
    return slice(convert(0, bytes32), 0, 32)

@external
def transferFrom(_from: address, _to: address, _amount: uint256) -> bool:
    self.allowances[_from][msg.sender] -= _amount
    return self._move(_from, _to, _amount)
"""

AUTHORIZED_REENTRANCY_ROUTER_SOURCE = """
# @version 0.4.3

interface NominalVault:
    def transferBalanceWithinVault(
        _asset: address,
        _fromUser: address,
        _toUser: address,
        _transferAmount: uint256,
    ) -> (uint256, bool): nonpayable

vault: address
asset: address
from_user: address
to_user: address
amount: uint256
entered: public(bool)
completed: public(bool)

@external
def configure(
    _vault: address,
    _asset: address,
    _from_user: address,
    _to_user: address,
    _amount: uint256,
):
    self.vault = _vault
    self.asset = _asset
    self.from_user = _from_user
    self.to_user = _to_user
    self.amount = _amount

@external
def route() -> (uint256, bool):
    self.entered = True
    amount: uint256 = 0
    depleted: bool = False
    amount, depleted = extcall NominalVault(self.vault).transferBalanceWithinVault(
        self.asset,
        self.from_user,
        self.to_user,
        self.amount,
    )
    self.completed = True
    return amount, depleted
"""

@pytest.fixture(scope="session")
def safe_simple_erc20_vault(ripe_hq_deploy):
    return boa.load(
        "contracts/vaults/SimpleErc20.vy",
        ripe_hq_deploy,
        name="safe_simple_erc20_vault",
    )


@pytest.fixture
def vault_token(deploy3r):
    return boa.load(
        "contracts/mock/MockStockTokenControls.vy",
        deploy3r,
        18,
        name="safe_nominal_token",
    )


@pytest.fixture
def adversarial_token():
    return boa.loads(
        ADVERSARIAL_TOKEN_SOURCE,
        name="safe_nominal_adversarial_token",
        override_address=boa.env.generate_address(),
    )


def _credit(vault, token, user, amount, teller, admin=None):
    if admin is None:
        token.mint(vault, amount)
    else:
        token.mint(vault, amount, sender=admin)
    return vault.depositTokensInVault(
        user,
        token,
        amount,
        sender=teller.address,
    )


def _state(vault, token, from_user, to_user):
    balance = token.balanceValue if hasattr(token, "balanceValue") else token.balanceOf
    return (
        balance(vault),
        balance(to_user),
        vault.userBalances(from_user, token),
        vault.userBalances(to_user, token),
        vault.totalBalances(token),
        len(filter_logs(vault, "SimpleErc20VaultWithdrawal")),
        len(filter_logs(vault, "SimpleErc20VaultTransfer")),
    )


def _register_safe_nominal_vault(vault_book, governance, vault):
    assert vault_book.startAddNewAddressToRegistry(
        vault,
        "Safe Simple ERC20 Vault",
        sender=governance.address,
    )
    boa.env.time_travel(blocks=vault_book.registryChangeTimeLock())
    vault_id = vault_book.confirmNewAddressToRegistry(
        vault,
        sender=governance.address,
    )
    assert vault_book.getAddr(vault_id) == vault.address
    return vault_id


# Reserved addresses avoid perturbing Boa's generated-address sequence and the
# stale diagnostic type metadata that can survive its automatic test anchors.
SAFE_NOMINAL_CROSS_VAULT_PEER_ADDRESS = (
    "0x00000000000000000000000000000000C0DE0003"
)


@pytest.mark.parametrize("decimals", (6, 18), ids=("six-decimals", "eighteen-decimals"))
def test_exact_deposit_preserves_units_layout_and_event(
    decimals,
    ripe_hq_deploy,
    deploy3r,
    teller,
    bob,
):
    vault = boa.load("contracts/vaults/SimpleErc20.vy", ripe_hq_deploy)
    token = boa.load("contracts/mock/MockStockTokenControls.vy", deploy3r, decimals)
    amount = 137 * 10**decimals

    assert _credit(vault, token, bob, amount, teller, deploy3r) == amount
    events = filter_logs(vault, "SimpleErc20VaultDeposit")
    assert token.balanceOf(vault) == amount
    assert vault.userBalances(bob, token) == amount
    assert vault.totalBalances(token) == amount
    assert vault.getTotalAmountForUser(bob, token) == amount
    assert vault.getTotalAmountForVault(token) == amount

    assert len(events) == 1
    assert events[0].user == bob
    assert events[0].asset == token.address
    assert events[0].amount == amount


def test_preexisting_surplus_remains_uncredited_and_live(
    safe_simple_erc20_vault,
    vault_token,
    deploy3r,
    teller,
    bob,
    alice,
):
    donation = 17
    first = 100
    second = 41
    vault_token.mint(safe_simple_erc20_vault, donation, sender=deploy3r)

    assert _credit(safe_simple_erc20_vault, vault_token, bob, first, teller, deploy3r) == first
    assert _credit(safe_simple_erc20_vault, vault_token, alice, second, teller, deploy3r) == second
    assert vault_token.balanceOf(safe_simple_erc20_vault) == donation + first + second
    assert safe_simple_erc20_vault.totalBalances(vault_token) == first + second
    assert safe_simple_erc20_vault.getTotalAmountForUser(bob, vault_token) == first
    assert safe_simple_erc20_vault.getTotalAmountForUser(alice, vault_token) == second


def test_deficit_blocks_deposit_without_allocating_new_nominal(
    safe_simple_erc20_vault,
    vault_token,
    deploy3r,
    teller,
    bob,
    alice,
):
    amount = 100
    _credit(safe_simple_erc20_vault, vault_token, bob, amount, teller, deploy3r)
    vault_token.adminBurn(safe_simple_erc20_vault, 1, sender=deploy3r)
    vault_token.mint(safe_simple_erc20_vault, 50, sender=deploy3r)

    with boa.reverts():
        safe_simple_erc20_vault.depositTokensInVault(
            alice,
            vault_token,
            50,
            sender=teller.address,
        )

    assert safe_simple_erc20_vault.userBalances(alice, vault_token) == 0
    assert safe_simple_erc20_vault.totalBalances(vault_token) == amount
    assert vault_token.balanceOf(safe_simple_erc20_vault) == amount + 49


@pytest.mark.parametrize(
    "balance_mode",
    (1, 2, 3, 4),
    ids=("revert", "empty", "one-byte", "short-31"),
)
def test_invalid_typed_balance_read_reverts_views_and_mutations(
    balance_mode,
    safe_simple_erc20_vault,
    adversarial_token,
    teller,
    bob,
    alice,
    auction_house,
):
    amount = 100
    _credit(safe_simple_erc20_vault, adversarial_token, bob, amount, teller)
    adversarial_token.configure_balance(safe_simple_erc20_vault, balance_mode, 0, False)

    with boa.reverts():
        safe_simple_erc20_vault.getTotalAmountForUser(bob, adversarial_token)
    with boa.reverts():
        safe_simple_erc20_vault.getUserAssetAndAmountAtIndex(bob, 1)

    with boa.reverts():
        safe_simple_erc20_vault.depositTokensInVault(
            alice,
            adversarial_token,
            1,
            sender=teller.address,
        )
    with boa.reverts():
        safe_simple_erc20_vault.withdrawTokensFromVault(
            bob,
            adversarial_token,
            1,
            alice,
            sender=teller.address,
        )
    with boa.reverts():
        safe_simple_erc20_vault.transferBalanceWithinVault(
            adversarial_token,
            bob,
            alice,
            1,
            sender=auction_house.address,
        )

    assert safe_simple_erc20_vault.userBalances(bob, adversarial_token) == amount
    assert safe_simple_erc20_vault.totalBalances(adversarial_token) == amount


def test_typed_balance_read_accepts_trailing_returndata(
    safe_simple_erc20_vault,
    adversarial_token,
    teller,
    bob,
):
    amount = 100
    _credit(safe_simple_erc20_vault, adversarial_token, bob, amount, teller)
    adversarial_token.configure_balance(safe_simple_erc20_vault, 5, 0, False)

    assert safe_simple_erc20_vault.getTotalAmountForUser(bob, adversarial_token) == amount
    assert safe_simple_erc20_vault.getUserAssetAndAmountAtIndex(bob, 1) == (
        adversarial_token.address,
        amount,
    )


def test_deficit_zeroes_usable_views_but_surplus_preserves_only_nominal(
    safe_simple_erc20_vault,
    vault_token,
    deploy3r,
    teller,
    bob,
):
    amount = 100
    _credit(safe_simple_erc20_vault, vault_token, bob, amount, teller, deploy3r)

    vault_token.adminBurn(safe_simple_erc20_vault, 1, sender=deploy3r)
    assert safe_simple_erc20_vault.getTotalAmountForUser(bob, vault_token) == 0
    assert safe_simple_erc20_vault.getUserAssetAndAmountAtIndex(bob, 1) == (
        vault_token.address,
        0,
    )

    vault_token.mint(safe_simple_erc20_vault, 8, sender=deploy3r)
    assert safe_simple_erc20_vault.getTotalAmountForUser(bob, vault_token) == amount
    assert safe_simple_erc20_vault.getUserAssetAndAmountAtIndex(bob, 1) == (
        vault_token.address,
        amount,
    )
    assert safe_simple_erc20_vault.getTotalAmountForVault(vault_token) == amount


def test_deficit_preserves_position_and_reward_getter_asymmetry(
    safe_simple_erc20_vault,
    vault_token,
    deploy3r,
    teller,
    bob,
):
    amount = 100
    _credit(safe_simple_erc20_vault, vault_token, bob, amount, teller, deploy3r)
    vault_token.adminBurn(safe_simple_erc20_vault, 1, sender=deploy3r)

    assert safe_simple_erc20_vault.getTotalAmountForUser(bob, vault_token) == 0
    assert safe_simple_erc20_vault.getUserAssetAndAmountAtIndex(bob, 1) == (
        vault_token.address,
        0,
    )
    assert safe_simple_erc20_vault.getTotalAmountForVault(vault_token) == amount
    assert safe_simple_erc20_vault.getUserLootBoxShare(bob, vault_token) == amount
    assert safe_simple_erc20_vault.getUserAssetAtIndexAndHasBalance(bob, 1) == (
        vault_token.address,
        True,
    )
    assert safe_simple_erc20_vault.doesUserHaveBalance(bob, vault_token)


def test_true_empty_and_zero_nominal_index_returns_empty_zero(
    safe_simple_erc20_vault,
    vault_token,
    deploy3r,
    teller,
    bob,
):
    assert safe_simple_erc20_vault.getUserAssetAndAmountAtIndex(bob, 1) == (
        "0x0000000000000000000000000000000000000000",
        0,
    )

    _credit(safe_simple_erc20_vault, vault_token, bob, 25, teller, deploy3r)
    safe_simple_erc20_vault.withdrawTokensFromVault(
        bob,
        vault_token,
        25,
        bob,
        sender=teller.address,
    )
    assert safe_simple_erc20_vault.getUserAssetAndAmountAtIndex(bob, 1) == (
        "0x0000000000000000000000000000000000000000",
        0,
    )


@pytest.mark.parametrize(
    ("requested", "expected", "depleted"),
    (
        pytest.param(40, 40, False, id="partial"),
        pytest.param(100, 100, True, id="full"),
        pytest.param(140, 100, True, id="over-request"),
    ),
)
def test_internal_movement_is_exact_partial_or_full_and_custody_neutral(
    requested,
    expected,
    depleted,
    safe_simple_erc20_vault,
    vault_token,
    deploy3r,
    teller,
    auction_house,
    bob,
    alice,
):
    _credit(safe_simple_erc20_vault, vault_token, bob, 100, teller, deploy3r)
    custody_before = vault_token.balanceOf(safe_simple_erc20_vault)
    total_before = safe_simple_erc20_vault.totalBalances(vault_token)

    moved, seller_depleted = safe_simple_erc20_vault.transferBalanceWithinVault(
        vault_token,
        bob,
        alice,
        requested,
        sender=auction_house.address,
    )
    event = filter_logs(safe_simple_erc20_vault, "SimpleErc20VaultTransfer")[-1]

    assert moved == expected
    assert seller_depleted is depleted
    assert safe_simple_erc20_vault.userBalances(bob, vault_token) == 100 - expected
    assert safe_simple_erc20_vault.userBalances(alice, vault_token) == expected
    assert safe_simple_erc20_vault.totalBalances(vault_token) == total_before
    assert vault_token.balanceOf(safe_simple_erc20_vault) == custody_before
    assert event.transferAmount == expected
    assert event.isFromUserDepleted is depleted


def test_internal_movement_ignores_token_transfer_controls(
    safe_simple_erc20_vault,
    vault_token,
    deploy3r,
    teller,
    auction_house,
    bob,
    alice,
):
    _credit(safe_simple_erc20_vault, vault_token, bob, 100, teller, deploy3r)
    vault_token.setPaused(True, sender=deploy3r)
    vault_token.setSenderBlocked(safe_simple_erc20_vault, True, sender=deploy3r)
    vault_token.setRecipientBlocked(alice, True, sender=deploy3r)
    vault_token.setOperatorBlocked(safe_simple_erc20_vault, True, sender=deploy3r)
    vault_token.setUpgradeBehavior(1, sender=deploy3r)

    assert safe_simple_erc20_vault.transferBalanceWithinVault(
        vault_token,
        bob,
        alice,
        60,
        sender=auction_house.address,
    ) == (60, False)


def test_internal_failure_on_deficit_or_self_transfer_is_atomic(
    safe_simple_erc20_vault,
    vault_token,
    deploy3r,
    teller,
    auction_house,
    bob,
    alice,
):
    _credit(safe_simple_erc20_vault, vault_token, bob, 100, teller, deploy3r)
    vault_token.adminBurn(safe_simple_erc20_vault, 1, sender=deploy3r)
    before = (
        safe_simple_erc20_vault.userBalances(bob, vault_token),
        safe_simple_erc20_vault.userBalances(alice, vault_token),
        safe_simple_erc20_vault.totalBalances(vault_token),
    )
    with boa.reverts():
        safe_simple_erc20_vault.transferBalanceWithinVault(
            vault_token,
            bob,
            alice,
            50,
            sender=auction_house.address,
        )
    assert before == (
        safe_simple_erc20_vault.userBalances(bob, vault_token),
        safe_simple_erc20_vault.userBalances(alice, vault_token),
        safe_simple_erc20_vault.totalBalances(vault_token),
    )

    vault_token.mint(safe_simple_erc20_vault, 1, sender=deploy3r)
    with boa.reverts():
        safe_simple_erc20_vault.transferBalanceWithinVault(
            vault_token,
            bob,
            bob,
            50,
            sender=auction_house.address,
        )
    assert before == (
        safe_simple_erc20_vault.userBalances(bob, vault_token),
        safe_simple_erc20_vault.userBalances(alice, vault_token),
        safe_simple_erc20_vault.totalBalances(vault_token),
    )


def test_external_partial_and_full_withdrawals_match_outflow_delivery_and_report(
    safe_simple_erc20_vault,
    vault_token,
    deploy3r,
    teller,
    bob,
    alice,
):
    _credit(safe_simple_erc20_vault, vault_token, bob, 100, teller, deploy3r)

    first, depleted = safe_simple_erc20_vault.withdrawTokensFromVault(
        bob,
        vault_token,
        35,
        alice,
        sender=teller.address,
    )
    assert (first, depleted) == (35, False)
    assert vault_token.balanceOf(alice) == 35
    assert vault_token.balanceOf(safe_simple_erc20_vault) == 65
    assert safe_simple_erc20_vault.totalBalances(vault_token) == 65

    second, depleted = safe_simple_erc20_vault.withdrawTokensFromVault(
        bob,
        vault_token,
        100,
        alice,
        sender=teller.address,
    )
    assert (second, depleted) == (65, True)
    assert vault_token.balanceOf(alice) == first + second
    assert vault_token.balanceOf(safe_simple_erc20_vault) == 0
    assert safe_simple_erc20_vault.totalBalances(vault_token) == 0


def test_external_withdrawal_preserves_surplus_without_assigning_it(
    safe_simple_erc20_vault,
    vault_token,
    deploy3r,
    teller,
    bob,
    alice,
):
    vault_token.mint(safe_simple_erc20_vault, 13, sender=deploy3r)
    _credit(safe_simple_erc20_vault, vault_token, bob, 100, teller, deploy3r)

    assert safe_simple_erc20_vault.withdrawTokensFromVault(
        bob,
        vault_token,
        100,
        alice,
        sender=teller.address,
    ) == (100, True)
    assert vault_token.balanceOf(alice) == 100
    assert vault_token.balanceOf(safe_simple_erc20_vault) == 13
    assert safe_simple_erc20_vault.totalBalances(vault_token) == 0


def test_over_request_is_bounded_by_nominal_and_never_spends_surplus(
    safe_simple_erc20_vault,
    vault_token,
    deploy3r,
    teller,
    bob,
    alice,
):
    surplus = 13
    nominal = 100
    vault_token.mint(safe_simple_erc20_vault, surplus, sender=deploy3r)
    _credit(
        safe_simple_erc20_vault,
        vault_token,
        bob,
        nominal,
        teller,
        deploy3r,
    )

    assert safe_simple_erc20_vault.withdrawTokensFromVault(
        bob,
        vault_token,
        MAX_UINT256,
        alice,
        sender=teller.address,
    ) == (nominal, True)
    assert vault_token.balanceOf(alice) == nominal
    assert vault_token.balanceOf(safe_simple_erc20_vault) == surplus
    assert safe_simple_erc20_vault.totalBalances(vault_token) == 0


def test_safe_nominal_deficit_is_isolated_from_second_vault(
    safe_simple_erc20_vault,
    vault_token,
    deploy3r,
    teller,
    ripe_hq_deploy,
    bob,
    alice,
):
    second_vault = boa.load(
        "contracts/vaults/SimpleErc20.vy",
        ripe_hq_deploy,
        name="safe_nominal_cross_vault_peer",
        override_address=SAFE_NOMINAL_CROSS_VAULT_PEER_ADDRESS,
    )
    _credit(
        safe_simple_erc20_vault,
        vault_token,
        bob,
        100,
        teller,
        deploy3r,
    )
    _credit(second_vault, vault_token, bob, 100, teller, deploy3r)
    vault_token.adminBurn(
        safe_simple_erc20_vault,
        1,
        sender=deploy3r,
    )

    with boa.reverts("insufficient vault backing"):
        safe_simple_erc20_vault.withdrawTokensFromVault(
            bob,
            vault_token,
            40,
            alice,
            sender=teller.address,
        )

    assert second_vault.withdrawTokensFromVault(
        bob,
        vault_token,
        40,
        alice,
        sender=teller.address,
    ) == (40, False)
    assert safe_simple_erc20_vault.userBalances(bob, vault_token) == 100
    assert vault_token.balanceOf(safe_simple_erc20_vault) == 99
    assert second_vault.userBalances(bob, vault_token) == 60
    assert vault_token.balanceOf(second_vault) == 60
    assert vault_token.balanceOf(alice) == 40


def test_safe_nominal_failed_user_withdrawal_preserves_peer_state_and_retry(
    safe_simple_erc20_vault,
    vault_token,
    deploy3r,
    teller,
    bob,
    alice,
    charlie,
):
    _credit(
        safe_simple_erc20_vault,
        vault_token,
        bob,
        100,
        teller,
        deploy3r,
    )
    _credit(
        safe_simple_erc20_vault,
        vault_token,
        alice,
        60,
        teller,
        deploy3r,
    )
    vault_token.adminBurn(
        safe_simple_erc20_vault,
        1,
        sender=deploy3r,
    )

    with boa.reverts("insufficient vault backing"):
        safe_simple_erc20_vault.withdrawTokensFromVault(
            bob,
            vault_token,
            40,
            charlie,
            sender=teller.address,
        )

    assert safe_simple_erc20_vault.userBalances(bob, vault_token) == 100
    assert safe_simple_erc20_vault.userBalances(alice, vault_token) == 60
    assert safe_simple_erc20_vault.totalBalances(vault_token) == 160
    assert vault_token.balanceOf(charlie) == 0

    vault_token.mint(safe_simple_erc20_vault, 1, sender=deploy3r)
    assert safe_simple_erc20_vault.withdrawTokensFromVault(
        alice,
        vault_token,
        40,
        charlie,
        sender=teller.address,
    ) == (40, False)
    assert safe_simple_erc20_vault.userBalances(bob, vault_token) == 100
    assert safe_simple_erc20_vault.userBalances(alice, vault_token) == 20
    assert safe_simple_erc20_vault.totalBalances(vault_token) == 120
    assert vault_token.balanceOf(charlie) == 40


@pytest.mark.parametrize(
    ("operation", "reason"),
    (
        pytest.param("deposit", "only Teller allowed", id="deposit"),
        pytest.param("withdraw", "not allowed", id="withdraw"),
        pytest.param("transfer", "not allowed", id="internal-transfer"),
    ),
)
def test_authorization_reverts_before_unknown_balance_observation(
    operation,
    reason,
    safe_simple_erc20_vault,
    adversarial_token,
    alice,
    bob,
):
    adversarial_token.configure_balance(
        safe_simple_erc20_vault,
        1,
        0,
        False,
    )

    with boa.reverts(reason):
        if operation == "deposit":
            safe_simple_erc20_vault.depositTokensInVault(
                bob,
                adversarial_token,
                1,
                sender=alice,
            )
        elif operation == "withdraw":
            safe_simple_erc20_vault.withdrawTokensFromVault(
                bob,
                adversarial_token,
                1,
                alice,
                sender=alice,
            )
        else:
            safe_simple_erc20_vault.transferBalanceWithinVault(
                adversarial_token,
                bob,
                alice,
                1,
                sender=alice,
            )


@pytest.mark.parametrize(
    "return_mode",
    (
        pytest.param(1, id="empty"),
        pytest.param(0, id="exact-true"),
        pytest.param(5, id="oversized-33-true-prefix"),
        pytest.param(6, id="oversized-64-true-prefix"),
    ),
)
def test_typed_transfer_compatible_returndata_succeeds(
    return_mode,
    safe_simple_erc20_vault,
    adversarial_token,
    teller,
    bob,
    alice,
):
    _credit(safe_simple_erc20_vault, adversarial_token, bob, 100, teller)
    adversarial_token.configure_transfer_return(return_mode)

    assert safe_simple_erc20_vault.withdrawTokensFromVault(
        bob,
        adversarial_token,
        40,
        alice,
        sender=teller.address,
    ) == (40, False)
    assert _state(
        safe_simple_erc20_vault,
        adversarial_token,
        bob,
        alice,
    )[:5] == (60, 40, 60, 0, 60)


@pytest.mark.parametrize(
    ("return_mode", "transfer_mode"),
    (
        pytest.param(2, 0, id="exact-false"),
        pytest.param(3, 0, id="malformed-boolean"),
        pytest.param(4, 0, id="short-nonempty"),
        pytest.param(0, 7, id="token-revert"),
    ),
)
def test_rejected_transfer_returndata_rolls_back_every_observable_effect(
    return_mode,
    transfer_mode,
    safe_simple_erc20_vault,
    adversarial_token,
    teller,
    bob,
    alice,
):
    _credit(safe_simple_erc20_vault, adversarial_token, bob, 100, teller)
    adversarial_token.configure_transfer_return(return_mode)
    adversarial_token.configure_transfer(transfer_mode)
    before = _state(safe_simple_erc20_vault, adversarial_token, bob, alice)

    with boa.reverts():
        safe_simple_erc20_vault.withdrawTokensFromVault(
            bob,
            adversarial_token,
            40,
            alice,
            sender=teller.address,
        )

    assert _state(safe_simple_erc20_vault, adversarial_token, bob, alice) == before


@pytest.mark.parametrize(
    "transfer_mode",
    (1, 2, 3, 4, 5, 6, 7),
    ids=(
        "zero-delivery",
        "short-one",
        "recipient-fee",
        "reflection-excess",
        "recipient-burn",
        "false-return",
        "revert",
    ),
)
def test_nonexact_external_delivery_reverts_all_vault_and_token_state(
    transfer_mode,
    safe_simple_erc20_vault,
    adversarial_token,
    teller,
    bob,
    alice,
):
    _credit(safe_simple_erc20_vault, adversarial_token, bob, 100, teller)
    if transfer_mode == 5:
        adversarial_token.mint(alice, 5)
    adversarial_token.configure_transfer(transfer_mode)
    before = _state(safe_simple_erc20_vault, adversarial_token, bob, alice)

    with boa.reverts():
        safe_simple_erc20_vault.withdrawTokensFromVault(
            bob,
            adversarial_token,
            40,
            alice,
            sender=teller.address,
        )

    assert _state(safe_simple_erc20_vault, adversarial_token, bob, alice) == before


@pytest.mark.parametrize("target", ("vault", "recipient"))
@pytest.mark.parametrize("post_mode", (1, 2, 3, 4, 6))
def test_post_transfer_unknown_balance_reverts_atomically(
    target,
    post_mode,
    safe_simple_erc20_vault,
    adversarial_token,
    teller,
    bob,
    alice,
):
    _credit(safe_simple_erc20_vault, adversarial_token, bob, 100, teller)
    balance_target = safe_simple_erc20_vault if target == "vault" else alice
    adversarial_token.configure_balance(balance_target, 0, post_mode, True)
    before = _state(safe_simple_erc20_vault, adversarial_token, bob, alice)

    with boa.reverts():
        safe_simple_erc20_vault.withdrawTokensFromVault(
            bob,
            adversarial_token,
            40,
            alice,
            sender=teller.address,
        )

    assert _state(safe_simple_erc20_vault, adversarial_token, bob, alice) == before


def test_shared_mutex_rejects_authorized_callback_and_rolls_back_outer_withdrawal(
    safe_simple_erc20_vault,
    adversarial_token,
    teller,
    ripe_hq_deploy,
    governance,
    bob,
    alice,
):
    _credit(safe_simple_erc20_vault, adversarial_token, bob, 100, teller)
    router = boa.loads(
        AUTHORIZED_REENTRANCY_ROUTER_SOURCE,
        name="safe_nominal_authorized_reentrancy_router",
    )
    router.configure(
        safe_simple_erc20_vault,
        adversarial_token,
        bob,
        alice,
        1,
    )
    assert ripe_hq_deploy.startAddressUpdateToRegistry(
        9,
        router,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=ripe_hq_deploy.registryChangeTimeLock())
    assert ripe_hq_deploy.confirmAddressUpdateToRegistry(
        9,
        sender=governance.address,
    )

    with boa.env.anchor():
        assert router.route() == (1, False)
        assert router.entered()
        assert router.completed()
        assert safe_simple_erc20_vault.userBalances(bob, adversarial_token) == 99
        assert safe_simple_erc20_vault.userBalances(alice, adversarial_token) == 1

    callback = router.route.prepare_calldata()
    adversarial_token.configure_callback(router, callback, True)
    before = _state(safe_simple_erc20_vault, adversarial_token, bob, alice)

    with boa.reverts():
        safe_simple_erc20_vault.withdrawTokensFromVault(
            bob,
            adversarial_token,
            40,
            alice,
            sender=teller.address,
        )

    assert _state(safe_simple_erc20_vault, adversarial_token, bob, alice) == before
    assert not router.entered()
    assert not router.completed()



def test_real_teller_batch_routes_partial_exact_and_over_request_through_safe_nominal_vault(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createAuctionParams,
    createDebtTerms,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    green_token,
    whale,
    bob,
    alice,
    sally,
    teller,
    mock_price_source,
    ledger,
    safe_simple_erc20_vault,
    vault_book,
    governance,
):
    vault_id = _register_safe_nominal_vault(
        vault_book,
        governance,
        safe_simple_erc20_vault,
    )
    setGeneralConfig()
    setGeneralDebtConfig(
        _ltvPaybackBuffer=0,
        _genAuctionParams=createAuctionParams(
            _startDiscount=0,
            _maxDiscount=0,
        ),
    )
    debt_terms = createDebtTerms(
        _liqThreshold=80_00,
        _liqFee=10_00,
        _ltv=50_00,
        _borrowRate=0,
    )
    setAssetConfig(
        alpha_token,
        _vaultIds=[vault_id],
        _debtTerms=debt_terms,
        _shouldAuctionInstantly=True,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)

    deposit_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(
        bob,
        deposit_amount,
        alpha_token,
        alpha_token_whale,
        safe_simple_erc20_vault,
    )
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    mock_price_source.setPrice(
        alpha_token,
        25 * EIGHTEEN_DECIMALS // 100,
    )
    teller.liquidateUser(bob, False, sender=sally)

    green_amount = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)
    purchases = [
        (bob, vault_id, alpha_token, 10 * EIGHTEEN_DECIMALS),
        (bob, vault_id, alpha_token, 10 * EIGHTEEN_DECIMALS),
        (bob, vault_id, alpha_token, MAX_UINT256),
    ]

    spent = teller.buyManyFungibleAuctions(
        purchases,
        green_amount,
        False,
        True,
        False,
        sender=alice,
    )

    assert spent == 50 * EIGHTEEN_DECIMALS
    assert safe_simple_erc20_vault.userBalances(bob, alpha_token) == 0
    assert safe_simple_erc20_vault.userBalances(alice, alpha_token) == deposit_amount
    assert safe_simple_erc20_vault.totalBalances(alpha_token) == deposit_amount
    assert alpha_token.balanceOf(safe_simple_erc20_vault) == deposit_amount
    assert alpha_token.balanceOf(alice) == 0
    assert ledger.isParticipatingInVault(alice, vault_id)

    purchase_events = filter_logs(teller, "FungAuctionPurchased")
    transfer_events = filter_logs(
        teller,
        "SimpleErc20VaultTransfer",
    )
    expected_amounts = [
        40 * EIGHTEEN_DECIMALS,
        40 * EIGHTEEN_DECIMALS,
        120 * EIGHTEEN_DECIMALS,
    ]
    assert [event.collateralAmountSent for event in purchase_events] == expected_amounts
    assert [event.isPositionDepleted for event in purchase_events] == [
        False,
        False,
        True,
    ]
    assert [event.transferAmount for event in transfer_events] == expected_amounts
    assert [event.isFromUserDepleted for event in transfer_events] == [
        False,
        False,
        True,
    ]


def test_real_teller_batch_later_deficit_preserves_earlier_healthy_row(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createAuctionParams,
    createDebtTerms,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    whale,
    bob,
    alice,
    sally,
    teller,
    auction_house,
    credit_engine,
    mock_price_source,
    ledger,
    safe_simple_erc20_vault,
    vault_book,
    governance,
):
    vault_id = _register_safe_nominal_vault(
        vault_book,
        governance,
        safe_simple_erc20_vault,
    )
    setGeneralConfig()
    setGeneralDebtConfig(
        _ltvPaybackBuffer=0,
        _genAuctionParams=createAuctionParams(
            _startDiscount=0,
            _maxDiscount=0,
        ),
    )
    debt_terms = createDebtTerms(
        _liqThreshold=80_00,
        _liqFee=10_00,
        _ltv=50_00,
        _borrowRate=0,
    )
    for token in (alpha_token, bravo_token):
        setAssetConfig(
            token,
            _vaultIds=[vault_id],
            _debtTerms=debt_terms,
            _shouldAuctionInstantly=True,
        )
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)

    performDeposit(
        bob,
        100 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
        safe_simple_erc20_vault,
    )
    performDeposit(
        bob,
        150 * EIGHTEEN_DECIMALS,
        bravo_token,
        bravo_token_whale,
        safe_simple_erc20_vault,
    )
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    for token in (alpha_token, bravo_token):
        mock_price_source.setPrice(
            token,
            25 * EIGHTEEN_DECIMALS // 100,
        )
    teller.liquidateUser(bob, False, sender=sally)

    bravo_token.burn(1, sender=safe_simple_erc20_vault.address)
    green_amount = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)
    purchases = [
        (bob, vault_id, alpha_token, 10 * EIGHTEEN_DECIMALS),
        (bob, vault_id, bravo_token, 10 * EIGHTEEN_DECIMALS),
    ]
    debt_before = credit_engine.getUserDebtAmount(bob)
    green_before = green_token.balanceOf(alice)

    spent = teller.buyManyFungibleAuctions(
        purchases,
        green_amount,
        False,
        True,
        False,
        sender=alice,
    )

    expected_spent = 10 * EIGHTEEN_DECIMALS
    expected_alpha = 40 * EIGHTEEN_DECIMALS
    assert spent == expected_spent
    assert green_token.balanceOf(alice) == green_before - expected_spent
    assert credit_engine.getUserDebtAmount(bob) == debt_before - expected_spent
    assert safe_simple_erc20_vault.userBalances(bob, alpha_token) == (
        100 * EIGHTEEN_DECIMALS - expected_alpha
    )
    assert safe_simple_erc20_vault.userBalances(alice, alpha_token) == expected_alpha
    assert safe_simple_erc20_vault.userBalances(bob, bravo_token) == (
        150 * EIGHTEEN_DECIMALS
    )
    assert safe_simple_erc20_vault.userBalances(alice, bravo_token) == 0
    assert alpha_token.balanceOf(safe_simple_erc20_vault) == 100 * EIGHTEEN_DECIMALS
    assert bravo_token.balanceOf(safe_simple_erc20_vault) == (
        150 * EIGHTEEN_DECIMALS - 1
    )

    purchases = filter_logs(teller, "FungAuctionPurchased")
    transfers = filter_logs(teller, "SimpleErc20VaultTransfer")
    assert len(purchases) == len(transfers) == 1
    assert purchases[0].liqAsset == alpha_token.address
    assert purchases[0].greenSpent == expected_spent
    assert purchases[0].collateralAmountSent == expected_alpha
    assert transfers[0].asset == alpha_token.address
    assert transfers[0].transferAmount == expected_alpha


@pytest.mark.parametrize(
    "route",
    ("ordinary-teller", "credit-engine"),
)
@pytest.mark.parametrize("endpoint_fixture", ("endaoment_funds", "endaoment_psm"))
def test_registry_endpoints_are_not_hard_coded_as_prohibited_recipients(
    route,
    endpoint_fixture,
    request,
    safe_simple_erc20_vault,
    vault_token,
    deploy3r,
    teller,
    credit_engine,
    bob,
):
    endpoint = request.getfixturevalue(endpoint_fixture)
    _credit(safe_simple_erc20_vault, vault_token, bob, 100, teller, deploy3r)
    sender = teller.address if route == "ordinary-teller" else credit_engine.address
    endpoint_before = vault_token.balanceOf(endpoint)
    assert safe_simple_erc20_vault.withdrawTokensFromVault(
        bob,
        vault_token,
        40,
        endpoint,
        sender=sender,
    ) == (40, False)
    assert vault_token.balanceOf(endpoint) == endpoint_before + 40
    assert vault_token.balanceOf(safe_simple_erc20_vault) == 60
    assert safe_simple_erc20_vault.userBalances(bob, vault_token) == 60
    assert safe_simple_erc20_vault.totalBalances(vault_token) == 60


def test_roles_pause_and_normal_recipient_behavior_remain_live(
    safe_simple_erc20_vault,
    vault_token,
    deploy3r,
    teller,
    auction_house,
    credit_engine,
    switchboard_alpha,
    bob,
    alice,
    sally,
):
    vault_token.mint(safe_simple_erc20_vault, 100, sender=deploy3r)
    with boa.reverts():
        safe_simple_erc20_vault.depositTokensInVault(
            bob,
            vault_token,
            100,
            sender=sally,
        )
    assert safe_simple_erc20_vault.depositTokensInVault(
        bob,
        vault_token,
        100,
        sender=teller.address,
    ) == 100

    with boa.reverts():
        safe_simple_erc20_vault.transferBalanceWithinVault(
            vault_token,
            bob,
            alice,
            10,
            sender=teller.address,
        )
    assert safe_simple_erc20_vault.transferBalanceWithinVault(
        vault_token,
        bob,
        alice,
        10,
        sender=credit_engine.address,
    ) == (10, False)

    safe_simple_erc20_vault.pause(True, sender=switchboard_alpha.address)
    with boa.reverts():
        safe_simple_erc20_vault.withdrawTokensFromVault(
            alice,
            vault_token,
            10,
            alice,
            sender=auction_house.address,
        )
    safe_simple_erc20_vault.pause(False, sender=switchboard_alpha.address)
    assert safe_simple_erc20_vault.withdrawTokensFromVault(
        alice,
        vault_token,
        10,
        alice,
        sender=auction_house.address,
    ) == (10, True)


def test_g2_registered_zero_liability_asset_cannot_be_recovered(
    safe_simple_erc20_vault,
    vault_token,
    deploy3r,
    teller,
    switchboard_alpha,
    bob,
    alice,
):
    _credit(
        safe_simple_erc20_vault,
        vault_token,
        bob,
        100,
        teller,
        deploy3r,
    )
    assert safe_simple_erc20_vault.withdrawTokensFromVault(
        bob,
        vault_token,
        100,
        alice,
        sender=teller.address,
    ) == (100, True)
    assert safe_simple_erc20_vault.totalBalances(vault_token) == 0
    assert safe_simple_erc20_vault.indexOfAsset(vault_token) != 0

    vault_token.mint(safe_simple_erc20_vault, 7, sender=deploy3r)
    with boa.reverts():
        safe_simple_erc20_vault.recoverFunds(
            alice,
            vault_token,
            sender=switchboard_alpha.address,
        )
    assert vault_token.balanceOf(safe_simple_erc20_vault) == 7


def test_registered_surplus_becomes_recoverable_only_after_explicit_cleanup(
    safe_simple_erc20_vault,
    vault_token,
    deploy3r,
    teller,
    switchboard_alpha,
    bob,
    alice,
):
    nominal = 100
    surplus = 7
    _credit(
        safe_simple_erc20_vault,
        vault_token,
        bob,
        nominal,
        teller,
        deploy3r,
    )
    vault_token.mint(safe_simple_erc20_vault, surplus, sender=deploy3r)
    assert safe_simple_erc20_vault.withdrawTokensFromVault(
        bob,
        vault_token,
        nominal,
        alice,
        sender=teller.address,
    ) == (nominal, True)

    assert safe_simple_erc20_vault.totalBalances(vault_token) == 0
    assert safe_simple_erc20_vault.isSupportedVaultAsset(vault_token)
    with boa.reverts("invalid recovery"):
        safe_simple_erc20_vault.recoverFunds(
            alice,
            vault_token,
            sender=switchboard_alpha.address,
        )

    assert safe_simple_erc20_vault.deregisterVaultAsset(
        vault_token,
        sender=switchboard_alpha.address,
    )
    assert not safe_simple_erc20_vault.isSupportedVaultAsset(vault_token)
    safe_simple_erc20_vault.recoverFunds(
        alice,
        vault_token,
        sender=switchboard_alpha.address,
    )
    assert vault_token.balanceOf(safe_simple_erc20_vault) == 0
    assert vault_token.balanceOf(alice) == nominal + surplus
    event = filter_logs(safe_simple_erc20_vault, "VaultFundsRecovered")[-1]
    assert event.asset == vault_token.address
    assert event.recipient == alice
    assert event.balance == surplus


def test_g2_nonzero_liability_asset_cannot_be_recovered(
    safe_simple_erc20_vault,
    vault_token,
    deploy3r,
    teller,
    switchboard_alpha,
    bob,
    alice,
):
    _credit(
        safe_simple_erc20_vault,
        vault_token,
        bob,
        100,
        teller,
        deploy3r,
    )
    with boa.reverts():
        safe_simple_erc20_vault.recoverFunds(
            alice,
            vault_token,
            sender=switchboard_alpha.address,
        )
    assert vault_token.balanceOf(safe_simple_erc20_vault) == 100
    assert safe_simple_erc20_vault.totalBalances(vault_token) == 100


@pytest.mark.parametrize(
    "return_mode",
    (
        pytest.param(0, id="exact-true"),
        pytest.param(1, id="empty-default-true"),
        pytest.param(5, id="oversized-33-true-prefix"),
        pytest.param(6, id="oversized-64-true-prefix"),
    ),
)
def test_g2_unregistered_zero_liability_recovery_accepts_compatible_returns(
    return_mode,
    safe_simple_erc20_vault,
    adversarial_token,
    switchboard_alpha,
    alice,
):
    adversarial_token.mint(safe_simple_erc20_vault, 25)
    adversarial_token.configure_transfer_return(return_mode)

    safe_simple_erc20_vault.recoverFunds(
        alice,
        adversarial_token,
        sender=switchboard_alpha.address,
    )

    assert adversarial_token.balanceValue(safe_simple_erc20_vault) == 0
    assert adversarial_token.balanceValue(alice) == 25
    event = filter_logs(safe_simple_erc20_vault, "VaultFundsRecovered")[-1]
    assert event.asset == adversarial_token.address
    assert event.recipient == alice
    assert event.balance == 25


@pytest.mark.parametrize(
    ("return_mode", "transfer_mode"),
    (
        pytest.param(2, 0, id="exact-false"),
        pytest.param(3, 0, id="malformed-boolean"),
        pytest.param(4, 0, id="short-nonempty"),
        pytest.param(0, 7, id="token-revert"),
    ),
)
def test_g2_rejected_recovery_returns_are_atomic(
    return_mode,
    transfer_mode,
    safe_simple_erc20_vault,
    adversarial_token,
    switchboard_alpha,
    alice,
):
    adversarial_token.mint(safe_simple_erc20_vault, 25)
    adversarial_token.configure_transfer_return(return_mode)
    adversarial_token.configure_transfer(transfer_mode)

    with boa.reverts():
        safe_simple_erc20_vault.recoverFunds(
            alice,
            adversarial_token,
            sender=switchboard_alpha.address,
        )

    assert adversarial_token.balanceValue(safe_simple_erc20_vault) == 25
    assert adversarial_token.balanceValue(alice) == 0
    assert filter_logs(safe_simple_erc20_vault, "VaultFundsRecovered") == []


def test_g2_recovery_pins_inherited_recipient_mismatch_boundary(
    safe_simple_erc20_vault,
    adversarial_token,
    switchboard_alpha,
    alice,
):
    adversarial_token.mint(safe_simple_erc20_vault, 25)
    adversarial_token.configure_transfer(2)

    safe_simple_erc20_vault.recoverFunds(
        alice,
        adversarial_token,
        sender=switchboard_alpha.address,
    )

    # Inherited VaultData recovery checks the typed Boolean return, but unlike
    # Safe nominal withdrawal it does not prove an exact recipient delta.
    assert adversarial_token.balanceValue(safe_simple_erc20_vault) == 0
    assert adversarial_token.balanceValue(alice) == 24
    event = filter_logs(safe_simple_erc20_vault, "VaultFundsRecovered")[-1]
    assert event.balance == 25


def test_g2_recover_many_rolls_back_prior_unregistered_asset_on_later_rejection(
    safe_simple_erc20_vault,
    vault_token,
    adversarial_token,
    deploy3r,
    teller,
    switchboard_alpha,
    bob,
    alice,
):
    adversarial_token.mint(safe_simple_erc20_vault, 25)
    _credit(
        safe_simple_erc20_vault,
        vault_token,
        bob,
        100,
        teller,
        deploy3r,
    )

    with boa.reverts():
        safe_simple_erc20_vault.recoverFundsMany(
            alice,
            [adversarial_token, vault_token],
            sender=switchboard_alpha.address,
        )

    assert adversarial_token.balanceValue(safe_simple_erc20_vault) == 25
    assert adversarial_token.balanceValue(alice) == 0
    assert vault_token.balanceOf(safe_simple_erc20_vault) == 100
    assert safe_simple_erc20_vault.totalBalances(vault_token) == 100
    assert filter_logs(safe_simple_erc20_vault, "VaultFundsRecovered") == []
