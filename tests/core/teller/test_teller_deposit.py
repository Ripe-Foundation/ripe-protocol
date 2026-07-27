import subprocess
import sys

import boa
import pytest

from constants import EIGHTEEN_DECIMALS, MAX_UINT256
from conf_utils import filter_logs


M1_ADVERSARIAL_TOKEN_SOURCE = """
# @version 0.4.3

from ethereum.ercs import IERC20

balances: HashMap[address, uint256]
allowances: HashMap[address, HashMap[address, uint256]]
total_supply: uint256
underlying: public(address)

transfer_mode: public(uint256)
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
    self.total_supply += _amount

@external
def configure_transfer(_mode: uint256):
    self.transfer_mode = _mode

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

@external
def configure_underlying(_underlying: address):
    self.underlying = _underlying

@external
def set_self_allowance(_spender: address, _amount: uint256):
    self.allowances[self][_spender] = _amount

@view
@external
def balanceValue(_holder: address) -> uint256:
    return self.balances[_holder]

@view
@external
def allowance(_owner: address, _spender: address) -> uint256:
    return self.allowances[_owner][_spender]

@view
@external
def decimals() -> uint256:
    return 18

@view
@external
def asset() -> address:
    return self.underlying

@view
@external
def convertToAssets(_shares: uint256) -> uint256:
    return _shares

@view
@external
def convertToShares(_assets: uint256) -> uint256:
    return _assets

@view
@external
def previewDeposit(_assets: uint256) -> uint256:
    return _assets

@view
@external
def getLastUnderlying(_shares: uint256) -> uint256:
    return _shares

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
        if self.balance_mode == 7:
            return slice(convert(max_value(uint256), bytes32), 0, 32)
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

    assert self.balances[_from] >= _amount
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
        self.total_supply += 1
    elif self.transfer_mode == 5:
        if self.balances[_to] != 0:
            self.balances[_to] -= 1
            self.total_supply -= 1

    if self.change_balance_mode_on_transfer:
        self.balance_mode = self.post_balance_mode
    return True

@external
def transfer(_to: address, _amount: uint256) -> bool:
    return self._move(msg.sender, _to, _amount)

@external
def transferFrom(_from: address, _to: address, _amount: uint256) -> bool:
    allowed: uint256 = self.allowances[_from][msg.sender]
    assert allowed >= _amount
    if allowed != max_value(uint256):
        self.allowances[_from][msg.sender] = allowed - _amount
    return self._move(_from, _to, _amount)

@external
def deposit(_assets: uint256, _receiver: address) -> uint256:
    assert self.underlying != empty(address)
    assert extcall IERC20(self.underlying).transferFrom(
        msg.sender,
        self,
        _assets,
        default_return_value=True,
    )
    self.balances[_receiver] += _assets
    self.total_supply += _assets
    return _assets
"""


M1_ADVERSARIAL_VAULT_SOURCE = """
# @version 0.4.3

import contracts.modules.Addys as addys
from interfaces import Vault

mode: public(uint256)
callback_target: public(address)
callback_data: public(Bytes[1024])

@external
def configure(_mode: uint256, _target: address, _data: Bytes[1024]):
    self.mode = _mode
    self.callback_target = _target
    self.callback_data = _data

@view
@external
def getVaultDataOnDeposit(_user: address, _asset: address) -> Vault.VaultDataOnDeposit:
    return Vault.VaultDataOnDeposit(
        hasPosition=False,
        numAssets=0,
        userBalance=0,
        totalBalance=0,
    )

@internal
def _deposit(_amount: uint256) -> uint256:
    if self.mode == 4:
        raise
    if self.mode == 5:
        raw_call(self.callback_target, self.callback_data)
    if self.mode == 1:
        return 0
    if self.mode == 2:
        return _amount - 1
    if self.mode == 3:
        return _amount + 1
    return _amount

@external
def depositTokensInVault(
    _user: address,
    _asset: address,
    _amount: uint256,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    return self._deposit(_amount)

@external
def depositTokensWithLockDuration(
    _user: address,
    _asset: address,
    _amount: uint256,
    _lockDuration: uint256,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    return self._deposit(_amount)
"""


def _m1_token():
    return boa.loads(
        M1_ADVERSARIAL_TOKEN_SOURCE,
        name="m1_adversarial_token",
        override_address=boa.env.generate_address(),
    )


def _m1_register_vault(vault_book, governance, vault):
    assert vault_book.startAddNewAddressToRegistry(
        vault,
        "M1 disposable vault",
        sender=governance.address,
    )
    boa.env.time_travel(blocks=vault_book.registryChangeTimeLock())
    return vault_book.confirmNewAddressToRegistry(vault, sender=governance.address)


def _m1_assert_no_deposit_effects(teller, ledger, vault, token, user, amount):
    assert token.balanceValue(user) == amount
    assert token.balanceValue(vault) == 0
    assert ledger.getNumUserVaults(user) == 0
    assert filter_logs(teller, "TellerDeposit") == []


def _m1_clear_titanoboa_transient_storage():
    # Titanoboa 0.2.7 does not clear EIP-1153 state at its simulated
    # top-level transaction boundary. Production EVMs do.
    boa.env.evm.vm.state.clear_transient_storage()


def _m1_configure_gov_asset(
    token,
    mission_control,
    switchboard_alpha,
    setAssetConfig,
):
    mission_control.setRipeGovVaultConfig(
        token,
        100_00,
        False,
        (100, 1000, 200_00, True, 10_00),
        sender=switchboard_alpha.address,
    )
    setAssetConfig(token, _vaultIds=[2])


def _m1_replace_hq_address(ripe_hq, governance, registry_id, replacement):
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


def test_teller_basic_deposit(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, deposit_amount, sender=alpha_token_whale)
    alpha_token.approve(teller.address, deposit_amount, sender=bob)

    # deposit
    amount = teller.deposit(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)

    log = filter_logs(teller, "TellerDeposit")[0]
    assert log.user == bob
    assert log.depositor == bob
    assert log.asset == alpha_token.address
    assert log.amount == deposit_amount == amount
    assert log.vaultAddr == simple_erc20_vault.address
    assert log.vaultId != 0

    # check balance
    assert alpha_token.balanceOf(bob) == 0
    assert alpha_token.balanceOf(simple_erc20_vault) == deposit_amount


def test_deposit_low_risk_repeats_and_arms_current_action_block(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    ledger,
    mission_control,
    switchboard_alpha,
):
    setGeneralConfig()
    setAssetConfig(alpha_token)
    mission_control.setShouldCheckLastTouch(
        True,
        sender=switchboard_alpha.address,
    )

    deposit_amount = 25 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, deposit_amount * 2, sender=alpha_token_whale)
    alpha_token.approve(teller.address, deposit_amount * 2, sender=bob)

    teller.deposit(
        alpha_token,
        deposit_amount,
        bob,
        simple_erc20_vault,
        sender=bob,
    )
    teller.deposit(
        alpha_token,
        deposit_amount,
        bob,
        simple_erc20_vault,
        sender=bob,
    )

    assert ledger.lastTouch(bob) == boa.env.evm.patch.block_number
    assert (
        simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
        == deposit_amount * 2
    )


def test_teller_deposit_protocol_disabled(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
):
    # Setup with protocol deposits disabled
    setGeneralConfig(_canDeposit=False)
    setAssetConfig(alpha_token)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, deposit_amount, sender=alpha_token_whale)
    alpha_token.approve(teller.address, deposit_amount, sender=bob)

    # Attempt deposit should fail
    with boa.reverts("protocol deposits disabled"):
        teller.deposit(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)


def test_teller_deposit_asset_disabled(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
):
    # Setup with asset deposits disabled
    setGeneralConfig()
    setAssetConfig(alpha_token, _canDeposit=False)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, deposit_amount, sender=alpha_token_whale)
    alpha_token.approve(teller.address, deposit_amount, sender=bob)

    # Attempt deposit should fail
    with boa.reverts("asset deposits disabled"):
        teller.deposit(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)


def test_teller_deposit_user_not_allowed(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    mock_whitelist,
    teller,
):
    # Setup with user not allowed
    setGeneralConfig()
    setAssetConfig(alpha_token, _whitelist=mock_whitelist)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, deposit_amount, sender=alpha_token_whale)
    alpha_token.approve(teller.address, deposit_amount, sender=bob)

    # Attempt deposit should fail
    with boa.reverts("user not on whitelist"):
        teller.deposit(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)

    # add to whitelist
    mock_whitelist.setAllowed(bob, alpha_token, True, sender=bob)

    # attempt deposit again
    teller.deposit(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)


def test_teller_deposit_others_not_allowed(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    setGeneralConfig,
    setAssetConfig,
    setUserConfig,
    teller,
):
    # Setup with others not allowed to deposit
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setUserConfig(bob, _canAnyoneDeposit=False)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(sally, deposit_amount, sender=alpha_token_whale)
    alpha_token.approve(teller.address, deposit_amount, sender=sally)

    # Attempt deposit by sally for bob should fail
    with boa.reverts("cannot deposit for user"):
        teller.deposit(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=sally)


def test_teller_deposit_max_vaults(
    simple_erc20_vault,
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
):
    # Setup with max vaults = 1
    setGeneralConfig(_perUserMaxVaults=1)
    setAssetConfig(alpha_token, _vaultIds=[3, 4])

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, deposit_amount, sender=alpha_token_whale)
    alpha_token.approve(teller.address, deposit_amount, sender=bob)

    # First deposit should succeed
    teller.deposit(alpha_token, deposit_amount // 2, bob, simple_erc20_vault, sender=bob)

    # Second deposit to a different vault should fail
    with boa.reverts("reached max vaults"):
        teller.deposit(alpha_token, deposit_amount // 2, bob, rebase_erc20_vault, sender=bob)


def test_teller_deposit_max_assets(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
):
    # Setup with max assets per vault = 1
    setGeneralConfig(_perUserMaxAssetsPerVault=1)
    setAssetConfig(alpha_token)
    setAssetConfig(bravo_token)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Setup alpha token
    alpha_token.transfer(bob, deposit_amount, sender=alpha_token_whale)
    alpha_token.approve(teller.address, deposit_amount, sender=bob)
    
    # Setup bravo token
    bravo_token.transfer(bob, deposit_amount, sender=bravo_token_whale)
    bravo_token.approve(teller.address, deposit_amount, sender=bob)

    # First deposit should succeed
    teller.deposit(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)

    # Second deposit of different asset should fail
    with boa.reverts("reached max assets per vault"):
        teller.deposit(bravo_token, deposit_amount, bob, simple_erc20_vault, sender=bob)


def test_teller_deposit_user_limit(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
):
    # Setup with per user deposit limit
    user_limit = 100 * EIGHTEEN_DECIMALS
    setGeneralConfig()
    setAssetConfig(alpha_token, _perUserDepositLimit=user_limit)

    # Transfer more than limit
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, deposit_amount, sender=alpha_token_whale)
    alpha_token.approve(teller.address, deposit_amount, sender=bob)

    # First deposit up to limit should succeed
    teller.deposit(alpha_token, user_limit, bob, simple_erc20_vault, sender=bob)

    # Second deposit should fail
    with boa.reverts("cannot deposit, reached user limit"):
        teller.deposit(alpha_token, user_limit, bob, simple_erc20_vault, sender=bob)


def test_teller_deposit_global_limit(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    setGeneralConfig,
    setAssetConfig,
    teller,
):
    # Setup with global deposit limit
    global_limit = 100 * EIGHTEEN_DECIMALS
    setGeneralConfig()
    setAssetConfig(alpha_token, _globalDepositLimit=global_limit)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Setup for bob
    alpha_token.transfer(bob, deposit_amount, sender=alpha_token_whale)
    alpha_token.approve(teller.address, deposit_amount, sender=bob)
    
    # Setup for sally
    alpha_token.transfer(sally, deposit_amount, sender=alpha_token_whale)
    alpha_token.approve(teller.address, deposit_amount, sender=sally)

    # First deposit should succeed
    teller.deposit(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)

    # Second deposit should fail
    with boa.reverts("cannot deposit, reached global limit"):
        teller.deposit(alpha_token, deposit_amount, sally, simple_erc20_vault, sender=sally)


def test_teller_deposit_insufficient_funds(
    simple_erc20_vault,
    alpha_token,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
):
    # Setup basic config
    setGeneralConfig()
    setAssetConfig(alpha_token)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Don't transfer any tokens to bob, so he has 0 balance
    alpha_token.approve(teller.address, deposit_amount, sender=bob)

    # Attempt deposit should fail
    with boa.reverts("cannot deposit 0"):
        teller.deposit(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)

    # Verify bob still has 0 balance
    assert alpha_token.balanceOf(bob) == 0
    assert alpha_token.balanceOf(simple_erc20_vault) == 0


def test_teller_deposit_first_vault_adds_to_ledger(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    ledger,
    vault_book,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, deposit_amount, sender=alpha_token_whale)
    alpha_token.approve(teller.address, deposit_amount, sender=bob)

    # verify bob is not in any vaults initially
    assert ledger.numUserVaults(bob) == 0

    # deposit
    teller.deposit(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)

    # verify bob is now in the vault
    vault_id = vault_book.getRegId(simple_erc20_vault)
    assert ledger.getNumUserVaults(bob) == 1
    assert ledger.numUserVaults(bob) == 2
    assert ledger.userVaults(bob, 1) == vault_id
    assert ledger.indexOfVault(bob, vault_id) == 1


def test_teller_deposit_existing_vault_no_duplicate_ledger_entry(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    ledger,
    vault_book,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, deposit_amount * 2, sender=alpha_token_whale)  # transfer enough for two deposits
    alpha_token.approve(teller.address, deposit_amount * 2, sender=bob)

    # first deposit
    teller.deposit(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # verify initial state
    assert ledger.getNumUserVaults(bob) == 1
    assert ledger.userVaults(bob, 1) == vault_id
    initial_vault_index = ledger.indexOfVault(bob, vault_id)

    # second deposit to same vault
    teller.deposit(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)

    # verify no duplicate entry was created
    assert ledger.getNumUserVaults(bob) == 1
    assert ledger.userVaults(bob, 1) == vault_id
    assert ledger.indexOfVault(bob, vault_id) == initial_vault_index


def test_teller_deposit_teller_paused(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    switchboard_alpha,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, deposit_amount, sender=alpha_token_whale)
    alpha_token.approve(teller.address, deposit_amount, sender=bob)

    # pause the teller
    teller.pause(True, sender=switchboard_alpha.address)
    assert teller.isPaused()

    # attempt deposit should fail
    with boa.reverts("contract paused"):
        teller.deposit(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)

    # unpause the teller
    teller.pause(False, sender=switchboard_alpha.address)
    assert not teller.isPaused()

    # deposit should now succeed
    teller.deposit(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)

    # verify deposit was successful
    assert alpha_token.balanceOf(bob) == 0
    assert alpha_token.balanceOf(simple_erc20_vault) == deposit_amount


def test_teller_deposit_many(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    vault_book,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(bravo_token)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Setup alpha token
    alpha_token.transfer(bob, deposit_amount, sender=alpha_token_whale)
    alpha_token.approve(teller.address, deposit_amount, sender=bob)
    
    # Setup bravo token
    bravo_token.transfer(bob, deposit_amount, sender=bravo_token_whale)
    bravo_token.approve(teller.address, deposit_amount, sender=bob)

    # Create deposit actions
    vault_id = vault_book.getRegId(simple_erc20_vault)
    deposits = [
        (alpha_token.address, deposit_amount, simple_erc20_vault.address, vault_id),
        (bravo_token.address, deposit_amount, simple_erc20_vault.address, vault_id)
    ]

    # Execute multiple deposits
    num_deposits = teller.depositMany(bob, deposits, sender=bob)

    # Get deposit logs
    logs = filter_logs(teller, "TellerDeposit")
    assert len(logs) == 2

    # Verify number of deposits
    assert num_deposits == 2

    # Verify alpha token deposit
    alpha_log = logs[0]
    assert alpha_log.user == bob
    assert alpha_log.depositor == bob
    assert alpha_log.asset == alpha_token.address
    assert alpha_log.amount == deposit_amount
    assert alpha_log.vaultAddr == simple_erc20_vault.address
    assert alpha_log.vaultId == vault_id

    # Verify bravo token deposit
    bravo_log = logs[1]
    assert bravo_log.user == bob
    assert bravo_log.depositor == bob
    assert bravo_log.asset == bravo_token.address
    assert bravo_log.amount == deposit_amount
    assert bravo_log.vaultAddr == simple_erc20_vault.address
    assert bravo_log.vaultId == vault_id

    # Verify balances
    assert alpha_token.balanceOf(bob) == 0
    assert bravo_token.balanceOf(bob) == 0
    assert alpha_token.balanceOf(simple_erc20_vault) == deposit_amount
    assert bravo_token.balanceOf(simple_erc20_vault) == deposit_amount


def test_teller_deposit_nonexistent_vault(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, deposit_amount, sender=alpha_token_whale)
    alpha_token.approve(teller.address, deposit_amount, sender=bob)

    # Attempt deposit to non-existent vault should fail
    bad_vault_id = 9999
    with boa.reverts("invalid vault id"):
        teller.deposit(alpha_token, deposit_amount, bob, simple_erc20_vault, bad_vault_id, sender=bob)


def test_teller_deposit_vault_mismatch(
    simple_erc20_vault,
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    vault_book,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, deposit_amount, sender=alpha_token_whale)
    alpha_token.approve(teller.address, deposit_amount, sender=bob)

    # Get vault IDs
    simple_vault_id = vault_book.getRegId(simple_erc20_vault)

    # Attempt deposit with mismatched vault ID and address should fail
    with boa.reverts("vault id and vault addr mismatch"):
        teller.deposit(alpha_token, deposit_amount, bob, rebase_erc20_vault, simple_vault_id, sender=bob)


def test_teller_deposit_trusted_contract_bypasses_user_limit(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    credit_engine,
):
    # Setup with per user deposit limit
    user_limit = 50 * EIGHTEEN_DECIMALS
    setGeneralConfig()
    setAssetConfig(alpha_token, _perUserDepositLimit=user_limit)

    # First, make a deposit up to the user limit
    alpha_token.transfer(bob, user_limit, sender=alpha_token_whale)
    alpha_token.approve(teller.address, user_limit, sender=bob)
    teller.deposit(alpha_token, user_limit, bob, simple_erc20_vault, sender=bob)
    
    # Now try to deposit more - should fail for regular user since limit is reached
    additional_amount = 25 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, additional_amount, sender=alpha_token_whale)
    alpha_token.approve(teller.address, additional_amount, sender=bob)
    with boa.reverts("cannot deposit, reached user limit"):
        teller.deposit(alpha_token, additional_amount, bob, simple_erc20_vault, sender=bob)

    # Transfer tokens to trusted contract (credit_engine) and approve
    alpha_token.transfer(credit_engine.address, additional_amount, sender=alpha_token_whale)
    alpha_token.approve(teller.address, additional_amount, sender=credit_engine.address)
    
    # Trusted contract deposit should succeed despite user limit being reached
    amount = teller.deposit(alpha_token, additional_amount, bob, simple_erc20_vault, sender=credit_engine.address)

    # Verify the log shows the trusted contract as depositor
    logs = filter_logs(teller, "TellerDeposit")
    trusted_contract_log = logs[0]
    assert trusted_contract_log.user == bob
    assert trusted_contract_log.depositor == credit_engine.address
    assert trusted_contract_log.amount == additional_amount

    # Verify the deposit was successful
    assert amount == additional_amount
    assert alpha_token.balanceOf(simple_erc20_vault) == user_limit + additional_amount


def test_teller_deposit_trusted_contract_bypasses_global_limit(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    setGeneralConfig,
    setAssetConfig,
    teller,
    auction_house,
):
    # Setup with global deposit limit
    global_limit = 75 * EIGHTEEN_DECIMALS
    setGeneralConfig()
    setAssetConfig(alpha_token, _globalDepositLimit=global_limit)
    
    # Setup for bob - first deposit up to global limit
    alpha_token.transfer(bob, global_limit, sender=alpha_token_whale)
    alpha_token.approve(teller.address, global_limit, sender=bob)
    teller.deposit(alpha_token, global_limit, bob, simple_erc20_vault, sender=bob)
    
    # Setup for sally - regular user deposit should fail due to global limit being reached
    additional_amount = 25 * EIGHTEEN_DECIMALS
    alpha_token.transfer(sally, additional_amount, sender=alpha_token_whale)
    alpha_token.approve(teller.address, additional_amount, sender=sally)
    with boa.reverts("cannot deposit, reached global limit"):
        teller.deposit(alpha_token, additional_amount, sally, simple_erc20_vault, sender=sally)

    # Transfer tokens to trusted contract (auction_house) and approve
    alpha_token.transfer(auction_house.address, additional_amount, sender=alpha_token_whale)
    alpha_token.approve(teller.address, additional_amount, sender=auction_house.address)
    
    # Trusted contract deposit should succeed despite global limit being reached
    amount = teller.deposit(alpha_token, additional_amount, sally, simple_erc20_vault, sender=auction_house.address)
    
    # Verify the log shows the trusted contract as depositor
    logs = filter_logs(teller, "TellerDeposit")
    trusted_contract_log = logs[0]
    assert trusted_contract_log.user == sally
    assert trusted_contract_log.depositor == auction_house.address
    assert trusted_contract_log.amount == additional_amount

    # Verify the deposit was successful
    assert amount == additional_amount
    assert alpha_token.balanceOf(simple_erc20_vault) == global_limit + additional_amount


def test_teller_get_savings_green_and_enter_stab_pool_basic(
    stability_pool,
    green_token,
    savings_green,
    whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    ledger,
):
    # Basic setup
    setGeneralConfig()
    setAssetConfig(savings_green, [1])  # Configure savings_green for stability pool (vault ID 1)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, deposit_amount, sender=whale)
    green_token.approve(teller.address, deposit_amount, sender=bob)

    # Record initial balances
    initial_bob_green = green_token.balanceOf(bob)
    savings_green.balanceOf(bob)
    initial_stability_pool_sgreen = savings_green.balanceOf(stability_pool)

    # Execute convertToSavingsGreenAndDepositIntoStabPool
    sgreen_amount = teller.convertToSavingsGreenAndDepositIntoStabPool(bob, deposit_amount, sender=bob)

    # Verify TellerDeposit event was emitted
    logs = filter_logs(teller, "TellerDeposit")
    assert len(logs) == 1
    log = logs[0]
    assert log.user == bob
    assert log.depositor == bob
    assert log.asset == savings_green.address
    assert log.amount == sgreen_amount
    assert log.vaultAddr == stability_pool.address
    assert log.vaultId == 1  # STABILITY_POOL_ID

    # Check that the function returned a reasonable amount
    assert sgreen_amount > 0

    # Verify GREEN was transferred from bob
    assert green_token.balanceOf(bob) == initial_bob_green - deposit_amount

    # Verify sGREEN was deposited into stability pool on behalf of bob
    assert savings_green.balanceOf(stability_pool) == initial_stability_pool_sgreen + sgreen_amount

    # Verify bob is now participating in the stability pool vault
    assert ledger.getNumUserVaults(bob) == 1
    assert green_token.allowance(teller, savings_green) == 0


def test_teller_get_savings_green_and_enter_stab_pool_insufficient_funds(
    stability_pool,
    green_token,
    savings_green,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
):
    # Basic setup
    setGeneralConfig()
    setAssetConfig(savings_green, [1])

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Don't transfer any GREEN to bob, so he has 0 balance
    green_token.approve(teller.address, deposit_amount, sender=bob)

    # Attempt to deposit should fail
    with boa.reverts("cannot deposit 0 green"):
        teller.convertToSavingsGreenAndDepositIntoStabPool(bob, deposit_amount, sender=bob)

    # Verify no balances changed
    assert green_token.balanceOf(bob) == 0
    assert savings_green.balanceOf(stability_pool) == 0


def test_teller_get_savings_green_and_enter_stab_pool_contract_paused(
    stability_pool,
    green_token,
    savings_green,
    whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    switchboard_alpha,
):
    # Basic setup
    setGeneralConfig()
    setAssetConfig(savings_green, [1])

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, deposit_amount, sender=whale)
    green_token.approve(teller.address, deposit_amount, sender=bob)

    # Pause the teller
    teller.pause(True, sender=switchboard_alpha.address)
    assert teller.isPaused()

    # Attempt to deposit should fail
    with boa.reverts("contract paused"):
        teller.convertToSavingsGreenAndDepositIntoStabPool(bob, deposit_amount, sender=bob)

    # Unpause the teller
    teller.pause(False, sender=switchboard_alpha.address)
    assert not teller.isPaused()

    # Function should now succeed
    sgreen_amount = teller.convertToSavingsGreenAndDepositIntoStabPool(bob, deposit_amount, sender=bob)
    assert sgreen_amount > 0

    # Verify the deposit was successful
    assert green_token.balanceOf(bob) == 0
    assert savings_green.balanceOf(stability_pool) == sgreen_amount


def test_teller_deposit_min_balance_below_minimum(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
):
    """Test that deposits fail when they would result in a balance below minDepositBalance"""
    # Setup with minDepositBalance = 50 tokens
    min_balance = 50 * EIGHTEEN_DECIMALS
    setGeneralConfig()
    setAssetConfig(alpha_token, _minDepositBalance=min_balance)

    # Try to deposit less than minimum balance - should fail
    deposit_amount = 25 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, deposit_amount, sender=alpha_token_whale)
    alpha_token.approve(teller.address, deposit_amount, sender=bob)

    # Attempt deposit should fail
    with boa.reverts("too small a balance"):
        teller.deposit(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)

    # Verify no tokens were transferred
    assert alpha_token.balanceOf(bob) == deposit_amount
    assert alpha_token.balanceOf(simple_erc20_vault) == 0


def test_teller_deposit_min_balance_exactly_minimum(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
):
    """Test that deposits succeed when they result in exactly the minDepositBalance"""
    # Setup with minDepositBalance = 50 tokens
    min_balance = 50 * EIGHTEEN_DECIMALS
    setGeneralConfig()
    setAssetConfig(alpha_token, _minDepositBalance=min_balance)

    # Deposit exactly the minimum balance - should succeed
    deposit_amount = min_balance
    alpha_token.transfer(bob, deposit_amount, sender=alpha_token_whale)
    alpha_token.approve(teller.address, deposit_amount, sender=bob)

    # Deposit should succeed
    amount = teller.deposit(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)
    assert amount == deposit_amount

    # Verify tokens were transferred
    assert alpha_token.balanceOf(bob) == 0
    assert alpha_token.balanceOf(simple_erc20_vault) == deposit_amount


def test_teller_deposit_min_balance_above_minimum(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
):
    """Test that deposits succeed when they result in a balance above minDepositBalance"""
    # Setup with minDepositBalance = 50 tokens
    min_balance = 50 * EIGHTEEN_DECIMALS
    setGeneralConfig()
    setAssetConfig(alpha_token, _minDepositBalance=min_balance)

    # Deposit more than minimum balance - should succeed
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, deposit_amount, sender=alpha_token_whale)
    alpha_token.approve(teller.address, deposit_amount, sender=bob)

    # Deposit should succeed
    amount = teller.deposit(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)
    assert amount == deposit_amount

    # Verify tokens were transferred
    assert alpha_token.balanceOf(bob) == 0
    assert alpha_token.balanceOf(simple_erc20_vault) == deposit_amount


def test_teller_deposit_min_balance_with_existing_balance(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
):
    """Test that minDepositBalance considers existing user balance"""
    # Setup with minDepositBalance = 150 tokens
    min_balance = 150 * EIGHTEEN_DECIMALS
    setGeneralConfig()
    setAssetConfig(alpha_token, _minDepositBalance=min_balance)

    # First deposit 100 tokens (meets minimum) - should succeed
    first_deposit = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, first_deposit, sender=alpha_token_whale)
    alpha_token.approve(teller.address, first_deposit, sender=bob)
    
    # This should fail because 100 < 150 minimum
    with boa.reverts("too small a balance"):
        teller.deposit(alpha_token, first_deposit, bob, simple_erc20_vault, sender=bob)

    # Deposit 150 tokens (exactly meets minimum) - should succeed
    first_deposit = 150 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, first_deposit, sender=alpha_token_whale)
    alpha_token.approve(teller.address, first_deposit, sender=bob)
    teller.deposit(alpha_token, first_deposit, bob, simple_erc20_vault, sender=bob)

    # Second deposit of 30 tokens would bring total to 180 (above min 150) - should succeed
    second_deposit = 30 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, second_deposit, sender=alpha_token_whale)
    alpha_token.approve(teller.address, second_deposit, sender=bob)
    
    amount = teller.deposit(alpha_token, second_deposit, bob, simple_erc20_vault, sender=bob)
    assert amount == second_deposit

    # Verify final balance is above minimum
    assert alpha_token.balanceOf(simple_erc20_vault) == first_deposit + second_deposit


def test_teller_deposit_min_balance_zero_allows_any_amount(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
):
    """Test that minDepositBalance = 0 allows any deposit amount"""
    # Setup with minDepositBalance = 0 (default)
    setGeneralConfig()
    setAssetConfig(alpha_token, _minDepositBalance=0)

    # Even very small deposits should succeed
    deposit_amount = 1  # 1 wei
    alpha_token.transfer(bob, deposit_amount, sender=alpha_token_whale)  
    alpha_token.approve(teller.address, deposit_amount, sender=bob)

    # Deposit should succeed
    amount = teller.deposit(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)
    assert amount == deposit_amount

    # Verify tokens were transferred
    assert alpha_token.balanceOf(bob) == 0
    assert alpha_token.balanceOf(simple_erc20_vault) == deposit_amount


@pytest.mark.parametrize(
    "transfer_mode",
    (
        pytest.param(1, id="zero-receipt"),
        pytest.param(2, id="one-unit-short"),
        pytest.param(3, id="percentage-fee"),
        pytest.param(4, id="excess-reflection"),
        pytest.param(6, id="false-return"),
        pytest.param(7, id="reverting-transfer"),
    ),
)
def test_m1_direct_nonexact_receipts_revert_atomically(
    transfer_mode,
    simple_erc20_vault,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    ledger,
):
    setGeneralConfig()
    token = _m1_token()
    setAssetConfig(token)
    amount = 100 * EIGHTEEN_DECIMALS
    token.mint(bob, amount)
    token.approve(teller, amount, sender=bob)
    token.configure_transfer(transfer_mode)

    with boa.reverts():
        teller.deposit(token, amount, bob, simple_erc20_vault, sender=bob)

    _m1_assert_no_deposit_effects(
        teller,
        ledger,
        simple_erc20_vault,
        token,
        bob,
        amount,
    )


def test_m1_custody_decrease_reverts_atomically(
    simple_erc20_vault,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    ledger,
):
    setGeneralConfig()
    token = _m1_token()
    setAssetConfig(token)
    amount = 100 * EIGHTEEN_DECIMALS
    donation = 10
    token.mint(bob, amount)
    token.mint(simple_erc20_vault, donation)
    token.approve(teller, amount, sender=bob)
    token.configure_transfer(5)

    with boa.reverts():
        teller.deposit(token, amount, bob, simple_erc20_vault, sender=bob)

    assert token.balanceValue(bob) == amount
    assert token.balanceValue(simple_erc20_vault) == donation
    assert ledger.getNumUserVaults(bob) == 0
    assert filter_logs(teller, "TellerDeposit") == []


@pytest.mark.parametrize(
    "balance_mode",
    (
        pytest.param(1, id="target-revert"),
        pytest.param(2, id="empty"),
        pytest.param(3, id="one-byte"),
        pytest.param(4, id="thirty-one-byte"),
        pytest.param(5, id="thirty-three-byte"),
        pytest.param(6, id="dynamic-shaped"),
    ),
)
@pytest.mark.parametrize("phase", ("pre", "post"))
def test_m1_balance_observation_failures_are_atomic(
    balance_mode,
    phase,
    simple_erc20_vault,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    ledger,
):
    setGeneralConfig()
    token = _m1_token()
    setAssetConfig(token)
    amount = 100 * EIGHTEEN_DECIMALS
    token.mint(bob, amount)
    token.approve(teller, amount, sender=bob)
    if phase == "pre":
        token.configure_balance(simple_erc20_vault, balance_mode, 0, False)
    else:
        token.configure_balance(simple_erc20_vault, 0, balance_mode, True)

    with boa.reverts():
        teller.deposit(token, amount, bob, simple_erc20_vault, sender=bob)

    _m1_assert_no_deposit_effects(
        teller,
        ledger,
        simple_erc20_vault,
        token,
        bob,
        amount,
    )


@pytest.mark.parametrize(
    "vault_mode",
    (
        pytest.param(1, id="returns-zero"),
        pytest.param(2, id="returns-less"),
        pytest.param(3, id="returns-more"),
        pytest.param(4, id="reverts"),
    ),
)
def test_m1_vault_result_mismatch_reverts_exact_transfer(
    vault_mode,
    vault_book,
    governance,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    ledger,
):
    setGeneralConfig()
    token = _m1_token()
    vault = boa.loads(
        M1_ADVERSARIAL_VAULT_SOURCE,
        name="m1_adversarial_vault",
        override_address=boa.env.generate_address(),
    )
    vault_id = _m1_register_vault(vault_book, governance, vault)
    setAssetConfig(token, _vaultIds=[vault_id])
    vault.configure(vault_mode, teller, b"")

    amount = 100 * EIGHTEEN_DECIMALS
    token.mint(bob, amount)
    token.approve(teller, amount, sender=bob)

    with boa.reverts():
        teller.deposit(token, amount, bob, vault, sender=bob)

    _m1_assert_no_deposit_effects(teller, ledger, vault, token, bob, amount)


def test_m1_lock_duration_vault_mismatch_reverts_atomically(
    vault_book,
    governance,
    credit_engine,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    ledger,
):
    setGeneralConfig()
    token = _m1_token()
    vault = boa.loads(
        M1_ADVERSARIAL_VAULT_SOURCE,
        name="m1_lock_vault",
        override_address=boa.env.generate_address(),
    )
    vault_id = _m1_register_vault(vault_book, governance, vault)
    setAssetConfig(token, _vaultIds=[vault_id])
    vault.configure(2, teller, b"")

    amount = 100 * EIGHTEEN_DECIMALS
    token.mint(credit_engine, amount)
    token.approve(teller, amount, sender=credit_engine.address)

    with boa.reverts():
        teller.depositFromTrusted(
            bob,
            vault_id,
            token,
            amount,
            100,
            sender=credit_engine.address,
        )

    assert token.balanceValue(credit_engine) == amount
    assert token.balanceValue(vault) == 0
    assert ledger.getNumUserVaults(bob) == 0
    assert filter_logs(teller, "TellerDeposit") == []


@pytest.mark.parametrize("bad_index", (0, 1), ids=("first-element", "later-element"))
def test_m1_deposit_many_rolls_back_all_elements_on_nonexact_receipt(
    bad_index,
    simple_erc20_vault,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    vault_book,
    ledger,
):
    setGeneralConfig()
    exact = _m1_token()
    hostile = _m1_token()
    setAssetConfig(exact)
    setAssetConfig(hostile)
    amount = 100 * EIGHTEEN_DECIMALS
    for token in (exact, hostile):
        token.mint(bob, amount)
        token.approve(teller, amount, sender=bob)
    hostile.configure_transfer(2)

    vault_id = vault_book.getRegId(simple_erc20_vault)
    ordered = (hostile, exact) if bad_index == 0 else (exact, hostile)
    deposits = [
        (token.address, amount, simple_erc20_vault.address, vault_id)
        for token in ordered
    ]

    with boa.reverts():
        teller.depositMany(bob, deposits, sender=bob)

    for token in (exact, hostile):
        assert token.balanceValue(bob) == amount
        assert token.balanceValue(simple_erc20_vault) == 0
    assert ledger.getNumUserVaults(bob) == 0
    assert filter_logs(teller, "TellerDeposit") == []


M1_TRUSTED_FIXTURES = (
    "stability_pool",
    "deleverage",
    "human_resources",
    "lootbox",
    "bond_room",
    "credit_engine",
    "credit_redeem",
)


@pytest.mark.parametrize("producer_fixture", M1_TRUSTED_FIXTURES)
def test_m1_named_trusted_producer_custody_exact_and_short_atomicity(
    producer_fixture,
    request,
    simple_erc20_vault,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    ledger,
    vault_book,
):
    setGeneralConfig()
    producer = request.getfixturevalue(producer_fixture)
    token = _m1_token()
    setAssetConfig(token)
    amount = 100 * EIGHTEEN_DECIMALS
    vault_id = vault_book.getRegId(simple_erc20_vault)

    token.mint(producer, 2 * amount)
    token.approve(teller, 2 * amount, sender=producer.address)
    assert teller.depositFromTrusted(
        bob,
        vault_id,
        token,
        amount,
        0,
        sender=producer.address,
    ) == amount
    assert token.balanceValue(producer) == amount
    assert token.balanceValue(simple_erc20_vault) == amount

    token.configure_transfer(2)
    user_claim_before = simple_erc20_vault.getTotalAmountForUser(bob, token)
    with boa.reverts():
        teller.depositFromTrusted(
            bob,
            vault_id,
            token,
            amount,
            0,
            sender=producer.address,
        )

    assert token.balanceValue(producer) == amount
    assert token.balanceValue(simple_erc20_vault) == amount
    assert simple_erc20_vault.getTotalAmountForUser(bob, token) == user_claim_before
    assert ledger.getNumUserVaults(bob) == 1


def test_m1_transfer_callback_reentrancy_reverts_and_mutex_recovers(
    simple_erc20_vault,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    ledger,
):
    setGeneralConfig()
    token = _m1_token()
    setAssetConfig(token)
    amount = 100 * EIGHTEEN_DECIMALS
    token.mint(bob, 2 * amount)
    token.approve(teller, 2 * amount, sender=bob)
    token.mint(token, amount)
    token.set_self_allowance(teller, amount)
    callback = teller.deposit.prepare_calldata(
        token,
        amount,
        bob,
        simple_erc20_vault,
    )
    token.configure_callback(teller, callback, True)
    token.configure_transfer(8)

    with boa.reverts():
        teller.deposit(token, amount, bob, simple_erc20_vault, sender=bob)

    assert token.balanceValue(bob) == 2 * amount
    assert token.balanceValue(simple_erc20_vault) == 0
    assert ledger.getNumUserVaults(bob) == 0

    _m1_clear_titanoboa_transient_storage()
    token.configure_callback(teller, b"", False)
    token.configure_transfer(0)
    teller_address = bytes.fromhex(str(teller.address)[2:])
    assert boa.env.evm.vm.state.get_transient_storage(teller_address, 0) == b""
    assert boa.env.evm.vm.state.get_transient_storage(teller_address, 1) == b""
    assert not token.callback_enabled()
    assert token.transfer_mode() == 0
    assert token.allowance(bob, teller) == 2 * amount
    retry_amount = teller.deposit(
        token,
        amount,
        bob,
        simple_erc20_vault,
        sender=bob,
    )
    assert retry_amount == amount


@pytest.mark.parametrize(
    ("requested_lock", "effective_lock"),
    (
        pytest.param(0, 100, id="no-lock-request-uses-minimum"),
        pytest.param(500, 500, id="explicit-lock"),
        pytest.param(1500, 1000, id="lock-capped"),
    ),
)
def test_m1_gov_vault_exact_receipt_return_event_shares_and_lock(
    requested_lock,
    effective_lock,
    ripe_gov_vault,
    whale,
    setGeneralConfig,
    setAssetConfig,
    mission_control,
    switchboard_alpha,
    teller,
):
    setGeneralConfig()
    token = _m1_token()
    _m1_configure_gov_asset(
        token,
        mission_control,
        switchboard_alpha,
        setAssetConfig,
    )
    amount = 100 * EIGHTEEN_DECIMALS
    token.mint(whale, amount)
    token.approve(teller, amount, sender=whale)
    custody_before = token.balanceValue(ripe_gov_vault)

    returned = teller.depositIntoGovVault(
        token,
        amount,
        requested_lock,
        whale,
        sender=whale,
    )

    assert returned == amount
    assert token.balanceValue(ripe_gov_vault) - custody_before == amount
    assert ripe_gov_vault.getTotalAmountForUser(whale, token) == amount
    gov_data = ripe_gov_vault.userGovData(whale, token)
    assert gov_data.lastShares > 0
    assert gov_data.unlock == boa.env.evm.patch.block_number + effective_lock
    deposit_log = filter_logs(teller, "TellerDeposit")[0]
    assert deposit_log.amount == amount
    assert deposit_log.user == whale
    assert deposit_log.vaultAddr == ripe_gov_vault.address
    assert deposit_log.vaultId == 2


def test_m1_gov_vault_authorized_deposit_for_another_user(
    ripe_gov_vault,
    mock_undy_v2,
    bob,
    setGeneralConfig,
    setAssetConfig,
    mission_control,
    switchboard_alpha,
    teller,
):
    setGeneralConfig()
    token = _m1_token()
    _m1_configure_gov_asset(
        token,
        mission_control,
        switchboard_alpha,
        setAssetConfig,
    )
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    amount = 100 * EIGHTEEN_DECIMALS
    token.mint(mock_undy_v2, amount)
    token.approve(teller, amount, sender=mock_undy_v2.address)

    assert teller.depositIntoGovVault(
        token,
        amount,
        500,
        bob,
        sender=mock_undy_v2.address,
    ) == amount
    assert token.balanceValue(ripe_gov_vault) == amount
    assert ripe_gov_vault.getTotalAmountForUser(bob, token) == amount
    assert filter_logs(teller, "TellerDeposit")[0].depositor == mock_undy_v2.address


@pytest.mark.parametrize("failure_kind", ("short", "malformed"))
def test_m1_gov_vault_receipt_failure_is_atomic(
    failure_kind,
    ripe_gov_vault,
    whale,
    setGeneralConfig,
    setAssetConfig,
    mission_control,
    switchboard_alpha,
    teller,
    ledger,
):
    setGeneralConfig()
    token = _m1_token()
    _m1_configure_gov_asset(
        token,
        mission_control,
        switchboard_alpha,
        setAssetConfig,
    )
    amount = 100 * EIGHTEEN_DECIMALS
    token.mint(whale, amount)
    token.approve(teller, amount, sender=whale)
    if failure_kind == "short":
        token.configure_transfer(2)
    else:
        token.configure_balance(ripe_gov_vault, 0, 4, True)

    with boa.reverts():
        teller.depositIntoGovVault(
            token,
            amount,
            500,
            whale,
            sender=whale,
        )

    assert token.balanceValue(whale) == amount
    assert token.balanceValue(ripe_gov_vault) == 0
    assert ripe_gov_vault.getTotalAmountForUser(whale, token) == 0
    assert ripe_gov_vault.userGovData(whale, token).lastShares == 0
    assert ledger.getNumUserVaults(whale) == 0
    assert filter_logs(teller, "TellerDeposit") == []


@pytest.mark.parametrize("failure_kind", ("short", "malformed"))
def test_m1_fixed_sgreen_failure_is_inducible_and_atomic(
    failure_kind,
    stability_pool,
    green_token,
    whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    ripe_hq,
    governance,
    ledger,
):
    setGeneralConfig()
    fixed_sgreen = _m1_token()
    fixed_sgreen.configure_underlying(green_token)
    _m1_replace_hq_address(ripe_hq, governance, 2, fixed_sgreen)
    assert ripe_hq.getAddr(2) == fixed_sgreen.address
    setAssetConfig(fixed_sgreen, _vaultIds=[1])

    amount = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, amount, sender=whale)
    green_token.approve(teller, amount, sender=bob)
    if failure_kind == "short":
        fixed_sgreen.configure_transfer(2)
    else:
        fixed_sgreen.configure_balance(stability_pool, 0, 4, True)

    bob_green_before = green_token.balanceOf(bob)
    bob_allowance_before = green_token.allowance(bob, teller)
    with boa.reverts():
        teller.convertToSavingsGreenAndDepositIntoStabPool(
            bob,
            amount,
            sender=bob,
        )

    assert green_token.balanceOf(bob) == bob_green_before
    assert green_token.allowance(bob, teller) == bob_allowance_before
    assert green_token.balanceOf(teller) == 0
    assert green_token.balanceOf(fixed_sgreen) == 0
    assert green_token.allowance(teller, fixed_sgreen) == 0
    assert fixed_sgreen.balanceValue(teller) == 0
    assert fixed_sgreen.balanceValue(stability_pool) == 0
    assert stability_pool.getTotalAmountForUser(bob, fixed_sgreen) == 0
    assert ledger.getNumUserVaults(bob) == 0
    assert filter_logs(teller, "TellerDeposit") == []


def test_m1_credit_engine_borrower_proceeds_auto_deposit_remains_live(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    green_token,
    savings_green,
    stability_pool,
    credit_engine,
):
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(savings_green, _vaultIds=[1])
    setGeneralDebtConfig()
    collateral = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, collateral, alpha_token, alpha_token_whale)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)

    borrow_amount = 50 * EIGHTEEN_DECIMALS
    custody_before = savings_green.balanceOf(stability_pool)
    user_before = stability_pool.getTotalAmountForUser(bob, savings_green)
    returned = teller.borrow(
        borrow_amount,
        bob,
        True,
        True,
        sender=bob,
    )

    assert returned == borrow_amount
    custody_delta = savings_green.balanceOf(stability_pool) - custody_before
    user_delta = (
        stability_pool.getTotalAmountForUser(bob, savings_green) - user_before
    )
    assert custody_delta > 0
    assert user_delta == custody_delta
    assert green_token.balanceOf(bob) == 0
    assert savings_green.balanceOf(bob) == 0
    assert savings_green.balanceOf(credit_engine) == 0
    assert savings_green.allowance(credit_engine, teller) == 0
    deposit_log = filter_logs(teller, "TellerDeposit")[0]
    assert deposit_log.depositor == credit_engine.address
    assert deposit_log.asset == savings_green.address
    assert deposit_log.amount == custody_delta
    assert deposit_log.vaultAddr == stability_pool.address


def test_m1_credit_redeem_surplus_route_remains_dormant_and_refunds_user(
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    green_token,
    whale,
    simple_erc20_vault,
    vault_book,
    createDebtTerms,
    savings_green,
    stability_pool,
    credit_redeem,
):
    setGeneralConfig()
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=70_00,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setAssetConfig(savings_green, _vaultIds=[1])
    setGeneralDebtConfig()
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)

    performDeposit(
        bob,
        200 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
    )
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    mock_price_source.setPrice(
        alpha_token,
        70 * EIGHTEEN_DECIMALS // 100,
    )

    payment = 200 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, payment, sender=whale)
    green_token.approve(teller, payment, sender=alice)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    user_sgreen_before = savings_green.balanceOf(alice)
    pool_custody_before = savings_green.balanceOf(stability_pool)
    pool_claim_before = stability_pool.getTotalAmountForUser(
        alice,
        savings_green,
    )

    spent = teller.redeemCollateral(
        bob,
        vault_id,
        alpha_token,
        payment,
        False,
        False,
        True,
        alice,
        sender=alice,
    )

    assert spent < payment
    assert savings_green.balanceOf(alice) > user_sgreen_before
    assert savings_green.balanceOf(stability_pool) == pool_custody_before
    assert (
        stability_pool.getTotalAmountForUser(alice, savings_green)
        == pool_claim_before
    )
    assert savings_green.balanceOf(credit_redeem) == 0
    assert savings_green.allowance(credit_redeem, teller) == 0
    assert filter_logs(teller, "TellerDeposit") == []


def test_m1_teller_runtime_size_dual_guard():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "vyper",
            "-p",
            ".",
            "-f",
            "bytecode_runtime",
            "contracts/core/Teller.vy",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    output = result.stdout.strip()
    assert output.startswith("0x")
    runtime = bytes.fromhex(output[2:])
    assert len(runtime) > 0
    assert len(runtime) <= 24_576
    assert len(runtime) <= 24_152
