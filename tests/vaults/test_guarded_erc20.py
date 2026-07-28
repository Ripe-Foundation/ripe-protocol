"""Focused Track 8 M2 behavior for the generic guarded ERC-20 vault."""

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

interface GuardedVault:
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
    amount, depleted = extcall GuardedVault(self.vault).transferBalanceWithinVault(
        self.asset,
        self.from_user,
        self.to_user,
        self.amount,
    )
    self.completed = True
    return amount, depleted
"""

INTERNAL_POST_READ_TOKEN_SOURCE = """
# @version 0.4.3

interface VaultData:
    def userBalances(_user: address, _asset: address) -> uint256: view

balances: HashMap[address, uint256]
vault: address
watched_user: address
expected_balance: uint256
reject_changed_balance: bool

@external
def mint(_to: address, _amount: uint256):
    self.balances[_to] += _amount

@external
def configure_post_read(
    _vault: address,
    _watched_user: address,
    _expected_balance: uint256,
):
    self.vault = _vault
    self.watched_user = _watched_user
    self.expected_balance = _expected_balance
    self.reject_changed_balance = True

@view
@external
def balanceValue(_holder: address) -> uint256:
    return self.balances[_holder]

@view
@external
@raw_return
def balanceOf(_holder: address) -> Bytes[33]:
    if (
        self.reject_changed_balance
        and _holder == self.vault
        and staticcall VaultData(self.vault).userBalances(self.watched_user, self) != self.expected_balance
    ):
        return concat(convert(self.balances[_holder], bytes32), b"x")
    return slice(convert(self.balances[_holder], bytes32), 0, 32)

@external
def transfer(_to: address, _amount: uint256) -> bool:
    self.balances[msg.sender] -= _amount
    self.balances[_to] += _amount
    return True
"""


@pytest.fixture(scope="session")
def guarded_erc20_vault(ripe_hq_deploy):
    return boa.load(
        "contracts/vaults/GuardedErc20.vy",
        ripe_hq_deploy,
        name="guarded_erc20_vault",
    )


@pytest.fixture
def guarded_token(deploy3r):
    return boa.load(
        "contracts/mock/MockStockTokenControls.vy",
        deploy3r,
        18,
        name="guarded_stock_token",
    )


@pytest.fixture
def adversarial_token():
    return boa.loads(
        ADVERSARIAL_TOKEN_SOURCE,
        name="guarded_adversarial_token",
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
        len(filter_logs(vault, "GuardedErc20VaultWithdrawal")),
        len(filter_logs(vault, "GuardedErc20VaultTransfer")),
    )


def _register_guarded_vault(vault_book, governance, vault):
    assert vault_book.startAddNewAddressToRegistry(
        vault,
        "Guarded ERC20 Vault",
        sender=governance.address,
    )
    boa.env.time_travel(blocks=vault_book.registryChangeTimeLock())
    vault_id = vault_book.confirmNewAddressToRegistry(
        vault,
        sender=governance.address,
    )
    assert vault_book.getAddr(vault_id) == vault.address
    return vault_id


def _batch_state(
    vault,
    alpha_token,
    bravo_token,
    green_token,
    ledger,
    teller,
    auction_house,
    credit_engine,
    seller,
    buyer,
):
    debt = ledger.userDebt(seller)
    return (
        alpha_token.balanceOf(vault),
        bravo_token.balanceOf(vault),
        alpha_token.balanceOf(buyer),
        bravo_token.balanceOf(buyer),
        vault.userBalances(seller, alpha_token),
        vault.userBalances(seller, bravo_token),
        vault.userBalances(buyer, alpha_token),
        vault.userBalances(buyer, bravo_token),
        vault.totalBalances(alpha_token),
        vault.totalBalances(bravo_token),
        green_token.balanceOf(buyer),
        green_token.balanceOf(auction_house),
        green_token.balanceOf(credit_engine),
        debt.amount,
        debt.inLiquidation,
    )


@pytest.mark.parametrize("decimals", (6, 18), ids=("six-decimals", "eighteen-decimals"))
def test_exact_deposit_preserves_units_layout_and_event(
    decimals,
    ripe_hq_deploy,
    deploy3r,
    teller,
    bob,
):
    vault = boa.load("contracts/vaults/GuardedErc20.vy", ripe_hq_deploy)
    token = boa.load("contracts/mock/MockStockTokenControls.vy", deploy3r, decimals)
    amount = 137 * 10**decimals

    assert _credit(vault, token, bob, amount, teller, deploy3r) == amount
    events = filter_logs(vault, "GuardedErc20VaultDeposit")
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
    guarded_erc20_vault,
    guarded_token,
    deploy3r,
    teller,
    bob,
    alice,
):
    donation = 17
    first = 100
    second = 41
    guarded_token.mint(guarded_erc20_vault, donation, sender=deploy3r)

    assert _credit(guarded_erc20_vault, guarded_token, bob, first, teller, deploy3r) == first
    assert _credit(guarded_erc20_vault, guarded_token, alice, second, teller, deploy3r) == second
    assert guarded_token.balanceOf(guarded_erc20_vault) == donation + first + second
    assert guarded_erc20_vault.totalBalances(guarded_token) == first + second
    assert guarded_erc20_vault.getTotalAmountForUser(bob, guarded_token) == first
    assert guarded_erc20_vault.getTotalAmountForUser(alice, guarded_token) == second


def test_deficit_blocks_deposit_without_allocating_new_nominal(
    guarded_erc20_vault,
    guarded_token,
    deploy3r,
    teller,
    bob,
    alice,
):
    amount = 100
    _credit(guarded_erc20_vault, guarded_token, bob, amount, teller, deploy3r)
    guarded_token.adminBurn(guarded_erc20_vault, 1, sender=deploy3r)
    guarded_token.mint(guarded_erc20_vault, 50, sender=deploy3r)

    with boa.reverts():
        guarded_erc20_vault.depositTokensInVault(
            alice,
            guarded_token,
            50,
            sender=teller.address,
        )

    assert guarded_erc20_vault.userBalances(alice, guarded_token) == 0
    assert guarded_erc20_vault.totalBalances(guarded_token) == amount
    assert guarded_token.balanceOf(guarded_erc20_vault) == amount + 49


@pytest.mark.parametrize(
    "balance_mode",
    (1, 2, 3, 4, 5, 6),
    ids=("revert", "empty", "one-byte", "short-31", "long-33", "long-64"),
)
def test_unknown_backing_blocks_mutation_and_zeroes_usable_views(
    balance_mode,
    guarded_erc20_vault,
    adversarial_token,
    teller,
    bob,
    alice,
    auction_house,
):
    amount = 100
    _credit(guarded_erc20_vault, adversarial_token, bob, amount, teller)
    adversarial_token.configure_balance(guarded_erc20_vault, balance_mode, 0, False)

    assert guarded_erc20_vault.getTotalAmountForUser(bob, adversarial_token) == 0
    assert guarded_erc20_vault.getUserAssetAndAmountAtIndex(bob, 1) == (
        adversarial_token.address,
        0,
    )

    with boa.reverts():
        guarded_erc20_vault.depositTokensInVault(
            alice,
            adversarial_token,
            1,
            sender=teller.address,
        )
    with boa.reverts():
        guarded_erc20_vault.withdrawTokensFromVault(
            bob,
            adversarial_token,
            1,
            alice,
            sender=teller.address,
        )
    with boa.reverts():
        guarded_erc20_vault.transferBalanceWithinVault(
            adversarial_token,
            bob,
            alice,
            1,
            sender=auction_house.address,
        )

    assert guarded_erc20_vault.userBalances(bob, adversarial_token) == amount
    assert guarded_erc20_vault.totalBalances(adversarial_token) == amount


def test_deficit_zeroes_usable_views_but_surplus_preserves_only_nominal(
    guarded_erc20_vault,
    guarded_token,
    deploy3r,
    teller,
    bob,
):
    amount = 100
    _credit(guarded_erc20_vault, guarded_token, bob, amount, teller, deploy3r)

    guarded_token.adminBurn(guarded_erc20_vault, 1, sender=deploy3r)
    assert guarded_erc20_vault.getTotalAmountForUser(bob, guarded_token) == 0
    assert guarded_erc20_vault.getUserAssetAndAmountAtIndex(bob, 1) == (
        guarded_token.address,
        0,
    )

    guarded_token.mint(guarded_erc20_vault, 8, sender=deploy3r)
    assert guarded_erc20_vault.getTotalAmountForUser(bob, guarded_token) == amount
    assert guarded_erc20_vault.getUserAssetAndAmountAtIndex(bob, 1) == (
        guarded_token.address,
        amount,
    )
    assert guarded_erc20_vault.getTotalAmountForVault(guarded_token) == amount


def test_true_empty_and_zero_nominal_index_returns_empty_zero(
    guarded_erc20_vault,
    guarded_token,
    deploy3r,
    teller,
    bob,
):
    assert guarded_erc20_vault.getUserAssetAndAmountAtIndex(bob, 1) == (
        "0x0000000000000000000000000000000000000000",
        0,
    )

    _credit(guarded_erc20_vault, guarded_token, bob, 25, teller, deploy3r)
    guarded_erc20_vault.withdrawTokensFromVault(
        bob,
        guarded_token,
        25,
        bob,
        sender=teller.address,
    )
    assert guarded_erc20_vault.getUserAssetAndAmountAtIndex(bob, 1) == (
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
    guarded_erc20_vault,
    guarded_token,
    deploy3r,
    teller,
    auction_house,
    bob,
    alice,
):
    _credit(guarded_erc20_vault, guarded_token, bob, 100, teller, deploy3r)
    custody_before = guarded_token.balanceOf(guarded_erc20_vault)
    total_before = guarded_erc20_vault.totalBalances(guarded_token)

    moved, seller_depleted = guarded_erc20_vault.transferBalanceWithinVault(
        guarded_token,
        bob,
        alice,
        requested,
        sender=auction_house.address,
    )
    event = filter_logs(guarded_erc20_vault, "GuardedErc20VaultTransfer")[-1]

    assert moved == expected
    assert seller_depleted is depleted
    assert guarded_erc20_vault.userBalances(bob, guarded_token) == 100 - expected
    assert guarded_erc20_vault.userBalances(alice, guarded_token) == expected
    assert guarded_erc20_vault.totalBalances(guarded_token) == total_before
    assert guarded_token.balanceOf(guarded_erc20_vault) == custody_before
    assert event.transferAmount == expected
    assert event.isFromUserDepleted is depleted


def test_internal_movement_ignores_token_transfer_controls(
    guarded_erc20_vault,
    guarded_token,
    deploy3r,
    teller,
    auction_house,
    bob,
    alice,
):
    _credit(guarded_erc20_vault, guarded_token, bob, 100, teller, deploy3r)
    guarded_token.setPaused(True, sender=deploy3r)
    guarded_token.setSenderBlocked(guarded_erc20_vault, True, sender=deploy3r)
    guarded_token.setRecipientBlocked(alice, True, sender=deploy3r)
    guarded_token.setOperatorBlocked(guarded_erc20_vault, True, sender=deploy3r)
    guarded_token.setUpgradeBehavior(1, sender=deploy3r)

    assert guarded_erc20_vault.transferBalanceWithinVault(
        guarded_token,
        bob,
        alice,
        60,
        sender=auction_house.address,
    ) == (60, False)


def test_internal_failure_on_deficit_or_self_transfer_is_atomic(
    guarded_erc20_vault,
    guarded_token,
    deploy3r,
    teller,
    auction_house,
    bob,
    alice,
):
    _credit(guarded_erc20_vault, guarded_token, bob, 100, teller, deploy3r)
    guarded_token.adminBurn(guarded_erc20_vault, 1, sender=deploy3r)
    before = (
        guarded_erc20_vault.userBalances(bob, guarded_token),
        guarded_erc20_vault.userBalances(alice, guarded_token),
        guarded_erc20_vault.totalBalances(guarded_token),
    )
    with boa.reverts():
        guarded_erc20_vault.transferBalanceWithinVault(
            guarded_token,
            bob,
            alice,
            50,
            sender=auction_house.address,
        )
    assert before == (
        guarded_erc20_vault.userBalances(bob, guarded_token),
        guarded_erc20_vault.userBalances(alice, guarded_token),
        guarded_erc20_vault.totalBalances(guarded_token),
    )

    guarded_token.mint(guarded_erc20_vault, 1, sender=deploy3r)
    with boa.reverts():
        guarded_erc20_vault.transferBalanceWithinVault(
            guarded_token,
            bob,
            bob,
            50,
            sender=auction_house.address,
        )
    assert before == (
        guarded_erc20_vault.userBalances(bob, guarded_token),
        guarded_erc20_vault.userBalances(alice, guarded_token),
        guarded_erc20_vault.totalBalances(guarded_token),
    )


def test_internal_unknown_post_read_reverts_all_nominal_changes(
    guarded_erc20_vault,
    teller,
    auction_house,
    bob,
    alice,
):
    token = boa.loads(
        INTERNAL_POST_READ_TOKEN_SOURCE,
        name="guarded_internal_post_read_token",
        override_address=boa.env.generate_address(),
    )
    _credit(guarded_erc20_vault, token, bob, 100, teller)
    token.configure_post_read(guarded_erc20_vault, bob, 100)
    before = (
        token.balanceValue(guarded_erc20_vault),
        guarded_erc20_vault.userBalances(bob, token),
        guarded_erc20_vault.userBalances(alice, token),
        guarded_erc20_vault.totalBalances(token),
    )

    with boa.reverts():
        guarded_erc20_vault.transferBalanceWithinVault(
            token,
            bob,
            alice,
            40,
            sender=auction_house.address,
        )

    assert before == (
        token.balanceValue(guarded_erc20_vault),
        guarded_erc20_vault.userBalances(bob, token),
        guarded_erc20_vault.userBalances(alice, token),
        guarded_erc20_vault.totalBalances(token),
    )


def test_external_partial_and_full_withdrawals_match_outflow_delivery_and_report(
    guarded_erc20_vault,
    guarded_token,
    deploy3r,
    teller,
    bob,
    alice,
):
    _credit(guarded_erc20_vault, guarded_token, bob, 100, teller, deploy3r)

    first, depleted = guarded_erc20_vault.withdrawTokensFromVault(
        bob,
        guarded_token,
        35,
        alice,
        sender=teller.address,
    )
    assert (first, depleted) == (35, False)
    assert guarded_token.balanceOf(alice) == 35
    assert guarded_token.balanceOf(guarded_erc20_vault) == 65
    assert guarded_erc20_vault.totalBalances(guarded_token) == 65

    second, depleted = guarded_erc20_vault.withdrawTokensFromVault(
        bob,
        guarded_token,
        100,
        alice,
        sender=teller.address,
    )
    assert (second, depleted) == (65, True)
    assert guarded_token.balanceOf(alice) == first + second
    assert guarded_token.balanceOf(guarded_erc20_vault) == 0
    assert guarded_erc20_vault.totalBalances(guarded_token) == 0


def test_external_withdrawal_preserves_surplus_without_assigning_it(
    guarded_erc20_vault,
    guarded_token,
    deploy3r,
    teller,
    bob,
    alice,
):
    guarded_token.mint(guarded_erc20_vault, 13, sender=deploy3r)
    _credit(guarded_erc20_vault, guarded_token, bob, 100, teller, deploy3r)

    assert guarded_erc20_vault.withdrawTokensFromVault(
        bob,
        guarded_token,
        100,
        alice,
        sender=teller.address,
    ) == (100, True)
    assert guarded_token.balanceOf(alice) == 100
    assert guarded_token.balanceOf(guarded_erc20_vault) == 13
    assert guarded_erc20_vault.totalBalances(guarded_token) == 0


@pytest.mark.parametrize(
    "return_mode",
    (
        pytest.param(1, id="empty"),
        pytest.param(0, id="exact-true"),
    ),
)
def test_compatible_transfer_returndata_succeeds(
    return_mode,
    guarded_erc20_vault,
    adversarial_token,
    teller,
    bob,
    alice,
):
    _credit(guarded_erc20_vault, adversarial_token, bob, 100, teller)
    adversarial_token.configure_transfer_return(return_mode)

    assert guarded_erc20_vault.withdrawTokensFromVault(
        bob,
        adversarial_token,
        40,
        alice,
        sender=teller.address,
    ) == (40, False)
    assert _state(
        guarded_erc20_vault,
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
        pytest.param(5, 0, id="oversized-33"),
        pytest.param(6, 0, id="oversized-large"),
        pytest.param(0, 7, id="token-revert"),
    ),
)
def test_rejected_transfer_returndata_rolls_back_every_observable_effect(
    return_mode,
    transfer_mode,
    guarded_erc20_vault,
    adversarial_token,
    teller,
    bob,
    alice,
):
    _credit(guarded_erc20_vault, adversarial_token, bob, 100, teller)
    adversarial_token.configure_transfer_return(return_mode)
    adversarial_token.configure_transfer(transfer_mode)
    before = _state(guarded_erc20_vault, adversarial_token, bob, alice)

    with boa.reverts():
        guarded_erc20_vault.withdrawTokensFromVault(
            bob,
            adversarial_token,
            40,
            alice,
            sender=teller.address,
        )

    assert _state(guarded_erc20_vault, adversarial_token, bob, alice) == before


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
    guarded_erc20_vault,
    adversarial_token,
    teller,
    bob,
    alice,
):
    _credit(guarded_erc20_vault, adversarial_token, bob, 100, teller)
    if transfer_mode == 5:
        adversarial_token.mint(alice, 5)
    adversarial_token.configure_transfer(transfer_mode)
    before = _state(guarded_erc20_vault, adversarial_token, bob, alice)

    with boa.reverts():
        guarded_erc20_vault.withdrawTokensFromVault(
            bob,
            adversarial_token,
            40,
            alice,
            sender=teller.address,
        )

    assert _state(guarded_erc20_vault, adversarial_token, bob, alice) == before


@pytest.mark.parametrize("target", ("vault", "recipient"))
@pytest.mark.parametrize("post_mode", (1, 2, 4, 5, 6))
def test_post_transfer_unknown_balance_reverts_atomically(
    target,
    post_mode,
    guarded_erc20_vault,
    adversarial_token,
    teller,
    bob,
    alice,
):
    _credit(guarded_erc20_vault, adversarial_token, bob, 100, teller)
    balance_target = guarded_erc20_vault if target == "vault" else alice
    adversarial_token.configure_balance(balance_target, 0, post_mode, True)
    before = _state(guarded_erc20_vault, adversarial_token, bob, alice)

    with boa.reverts():
        guarded_erc20_vault.withdrawTokensFromVault(
            bob,
            adversarial_token,
            40,
            alice,
            sender=teller.address,
        )

    assert _state(guarded_erc20_vault, adversarial_token, bob, alice) == before


def test_shared_mutex_rejects_authorized_callback_and_rolls_back_outer_withdrawal(
    guarded_erc20_vault,
    adversarial_token,
    teller,
    ripe_hq_deploy,
    governance,
    bob,
    alice,
):
    _credit(guarded_erc20_vault, adversarial_token, bob, 100, teller)
    router = boa.loads(
        AUTHORIZED_REENTRANCY_ROUTER_SOURCE,
        name="guarded_authorized_reentrancy_router",
    )
    router.configure(
        guarded_erc20_vault,
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
        assert guarded_erc20_vault.userBalances(bob, adversarial_token) == 99
        assert guarded_erc20_vault.userBalances(alice, adversarial_token) == 1

    callback = router.route.prepare_calldata()
    adversarial_token.configure_callback(router, callback, True)
    before = _state(guarded_erc20_vault, adversarial_token, bob, alice)

    with boa.reverts():
        guarded_erc20_vault.withdrawTokensFromVault(
            bob,
            adversarial_token,
            40,
            alice,
            sender=teller.address,
        )

    assert _state(guarded_erc20_vault, adversarial_token, bob, alice) == before
    assert not router.entered()
    assert not router.completed()


def test_real_teller_batch_routes_partial_exact_and_over_request_through_guarded(
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
    guarded_erc20_vault,
    vault_book,
    governance,
):
    vault_id = _register_guarded_vault(
        vault_book,
        governance,
        guarded_erc20_vault,
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
        guarded_erc20_vault,
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
    assert guarded_erc20_vault.userBalances(bob, alpha_token) == 0
    assert guarded_erc20_vault.userBalances(alice, alpha_token) == deposit_amount
    assert guarded_erc20_vault.totalBalances(alpha_token) == deposit_amount
    assert alpha_token.balanceOf(guarded_erc20_vault) == deposit_amount
    assert alpha_token.balanceOf(alice) == 0
    assert ledger.isParticipatingInVault(alice, vault_id)

    purchase_events = filter_logs(teller, "FungAuctionPurchased")
    transfer_events = filter_logs(
        teller,
        "GuardedErc20VaultTransfer",
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


def test_real_teller_batch_later_guarded_failure_rolls_back_every_earlier_row(
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
    guarded_erc20_vault,
    vault_book,
    governance,
):
    vault_id = _register_guarded_vault(
        vault_book,
        governance,
        guarded_erc20_vault,
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
        guarded_erc20_vault,
    )
    performDeposit(
        bob,
        150 * EIGHTEEN_DECIMALS,
        bravo_token,
        bravo_token_whale,
        guarded_erc20_vault,
    )
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    for token in (alpha_token, bravo_token):
        mock_price_source.setPrice(
            token,
            25 * EIGHTEEN_DECIMALS // 100,
        )
    teller.liquidateUser(bob, False, sender=sally)

    bravo_token.burn(1, sender=guarded_erc20_vault.address)
    green_amount = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)
    purchases = [
        (bob, vault_id, alpha_token, 10 * EIGHTEEN_DECIMALS),
        (bob, vault_id, bravo_token, 10 * EIGHTEEN_DECIMALS),
    ]
    before = _batch_state(
        guarded_erc20_vault,
        alpha_token,
        bravo_token,
        green_token,
        ledger,
        teller,
        auction_house,
        credit_engine,
        bob,
        alice,
    )

    with boa.reverts():
        teller.buyManyFungibleAuctions(
            purchases,
            green_amount,
            False,
            True,
            False,
            sender=alice,
        )

    assert _batch_state(
        guarded_erc20_vault,
        alpha_token,
        bravo_token,
        green_token,
        ledger,
        teller,
        auction_house,
        credit_engine,
        bob,
        alice,
    ) == before
    assert filter_logs(teller, "FungAuctionPurchased") == []
    assert filter_logs(teller, "GuardedErc20VaultTransfer") == []
    assert filter_logs(teller, "RepayDebt") == []


@pytest.mark.parametrize(
    "route",
    ("ordinary-teller", "auction-wrapper", "credit-engine"),
)
@pytest.mark.parametrize("endpoint_fixture", ("endaoment_funds", "endaoment_psm"))
def test_current_endaoment_endpoints_are_rejected_before_delivery(
    route,
    endpoint_fixture,
    request,
    guarded_erc20_vault,
    guarded_token,
    deploy3r,
    teller,
    auction_house,
    credit_engine,
    deleverage,
    bob,
):
    endpoint = request.getfixturevalue(endpoint_fixture)
    _credit(guarded_erc20_vault, guarded_token, bob, 100, teller, deploy3r)
    before = (
        guarded_token.balanceOf(guarded_erc20_vault),
        guarded_token.balanceOf(endpoint),
        guarded_erc20_vault.userBalances(bob, guarded_token),
        guarded_erc20_vault.totalBalances(guarded_token),
    )

    with boa.reverts():
        if route == "ordinary-teller":
            guarded_erc20_vault.withdrawTokensFromVault(
                bob,
                guarded_token,
                40,
                endpoint,
                sender=teller.address,
            )
        elif route == "auction-wrapper":
            auction_house.withdrawTokensFromVault(
                bob,
                guarded_token,
                40,
                endpoint,
                guarded_erc20_vault,
                auction_house.getAddys(),
                sender=deleverage.address,
            )
        else:
            guarded_erc20_vault.withdrawTokensFromVault(
                bob,
                guarded_token,
                40,
                endpoint,
                sender=credit_engine.address,
            )

    assert before == (
        guarded_token.balanceOf(guarded_erc20_vault),
        guarded_token.balanceOf(endpoint),
        guarded_erc20_vault.userBalances(bob, guarded_token),
        guarded_erc20_vault.totalBalances(guarded_token),
    )


def test_roles_pause_and_normal_recipient_behavior_remain_live(
    guarded_erc20_vault,
    guarded_token,
    deploy3r,
    teller,
    auction_house,
    credit_engine,
    switchboard_alpha,
    bob,
    alice,
    sally,
):
    guarded_token.mint(guarded_erc20_vault, 100, sender=deploy3r)
    with boa.reverts():
        guarded_erc20_vault.depositTokensInVault(
            bob,
            guarded_token,
            100,
            sender=sally,
        )
    assert guarded_erc20_vault.depositTokensInVault(
        bob,
        guarded_token,
        100,
        sender=teller.address,
    ) == 100

    with boa.reverts():
        guarded_erc20_vault.transferBalanceWithinVault(
            guarded_token,
            bob,
            alice,
            10,
            sender=teller.address,
        )
    assert guarded_erc20_vault.transferBalanceWithinVault(
        guarded_token,
        bob,
        alice,
        10,
        sender=credit_engine.address,
    ) == (10, False)

    guarded_erc20_vault.pause(True, sender=switchboard_alpha.address)
    with boa.reverts():
        guarded_erc20_vault.withdrawTokensFromVault(
            alice,
            guarded_token,
            10,
            alice,
            sender=auction_house.address,
        )
    guarded_erc20_vault.pause(False, sender=switchboard_alpha.address)
    assert guarded_erc20_vault.withdrawTokensFromVault(
        alice,
        guarded_token,
        10,
        alice,
        sender=auction_house.address,
    ) == (10, True)
