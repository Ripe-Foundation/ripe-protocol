import subprocess
import sys
from pathlib import Path

import boa
import pytest
from boa.contracts.base_evm_contract import BoaError
from eth_abi import encode
from eth_utils import keccak

from constants import EIGHTEEN_DECIMALS, MAX_UINT256
from conf_utils import filter_logs, redeem_collateral


M1_ADVERSARIAL_TOKEN_SOURCE = """
# @version 0.4.3

from ethereum.ercs import IERC20

BALANCE_MODE_CONSTANT_MAX: constant(uint256) = 7
BALANCE_MODE_OFFSETTING_LIE: constant(uint256) = 8
TRANSFER_MODE_EXACT_ALIAS: constant(uint256) = 8

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
callback_transfer_mode: public(uint256)
callback_catches_rejection: public(bool)
callback_was_attempted: public(bool)
callback_succeeded: public(bool)

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
def configure_callback_rejection_policy(_should_catch: bool):
    self.callback_catches_rejection = _should_catch

@external
def configure_callback_transfer_mode(_mode: uint256):
    self.callback_transfer_mode = _mode

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
        if self.balance_mode == BALANCE_MODE_CONSTANT_MAX:
            return slice(convert(max_value(uint256), bytes32), 0, 32)
        if self.balance_mode == BALANCE_MODE_OFFSETTING_LIE:
            return slice(convert(self.balances[_holder] + 1, bytes32), 0, 32)
    return slice(convert(self.balances[_holder], bytes32), 0, 32)

@external
def approve(_spender: address, _amount: uint256) -> bool:
    self.allowances[msg.sender][_spender] = _amount
    return True

@internal
def _move(_from: address, _to: address, _amount: uint256) -> (bool, uint256):
    transferMode: uint256 = self.transfer_mode
    if transferMode == 6:
        return False, transferMode
    if transferMode == 7:
        raise

    assert self.balances[_from] >= _amount
    self.balances[_from] -= _amount

    if self.callback_enabled:
        self.callback_enabled = False
        self.transfer_mode = self.callback_transfer_mode
        self.callback_was_attempted = True
        if self.callback_catches_rejection:
            success: bool = False
            response: Bytes[1] = b""
            success, response = raw_call(
                self.callback_target,
                self.callback_data,
                max_outsize=1,
                revert_on_failure=False,
            )
            self.callback_succeeded = success
        else:
            raw_call(self.callback_target, self.callback_data)

    if transferMode in [0, TRANSFER_MODE_EXACT_ALIAS, 9, 10, 11, 12]:
        self.balances[_to] += _amount
    elif transferMode == 2:
        self.balances[_to] += _amount - 1
    elif transferMode == 3:
        self.balances[_to] += _amount * 99 // 100
    elif transferMode == 4:
        self.balances[_to] += _amount + 1
        self.total_supply += 1
    elif transferMode == 5:
        if self.balances[_to] != 0:
            self.balances[_to] -= 1
            self.total_supply -= 1

    if self.change_balance_mode_on_transfer:
        self.balance_mode = self.post_balance_mode
    return True, transferMode

@external
@raw_return
def transfer(_to: address, _amount: uint256) -> Bytes[33]:
    success: bool = False
    mode: uint256 = 0
    success, mode = self._move(msg.sender, _to, _amount)
    if mode == 9:
        return b""
    if mode == 10:
        return b"\x01"
    if mode == 11:
        return concat(convert(success, bytes32), b"x")
    return slice(convert(success, bytes32), 0, 32)

@external
@raw_return
def transferFrom(_from: address, _to: address, _amount: uint256) -> Bytes[33]:
    allowed: uint256 = self.allowances[_from][msg.sender]
    assert allowed >= _amount
    if allowed != max_value(uint256):
        self.allowances[_from][msg.sender] = allowed - _amount
    success: bool = False
    mode: uint256 = 0
    success, mode = self._move(_from, _to, _amount)
    if mode == 9:
        return b""
    if mode == 10:
        return b"\x01"
    if mode == 11:
        return concat(convert(success, bytes32), b"x")
    return slice(convert(success, bytes32), 0, 32)

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
from ethereum.ercs import IERC20

mode: public(uint256)
callback_target: public(address)
callback_data: public(Bytes[1024])

@external
def configure(_mode: uint256, _target: address, _data: Bytes[1024]):
    self.mode = _mode
    self.callback_target = _target
    self.callback_data = _data

@external
def approve_teller(_asset: address, _teller: address, _amount: uint256):
    assert extcall IERC20(_asset).approve(_teller, _amount)

@view
@external
def getVaultDataOnDeposit(_user: address, _asset: address) -> Vault.VaultDataOnDeposit:
    return Vault.VaultDataOnDeposit(
        hasPosition=False,
        numAssets=0,
        userBalance=0,
        totalBalance=0,
    )

@view
@external
def getUserLootBoxShare(_user: address, _asset: address) -> uint256:
    return 0

@view
@external
def getTotalAmountForVault(_asset: address) -> uint256:
    return 0

@internal
def _deposit(_amount: uint256) -> uint256:
    mode: uint256 = self.mode
    if mode == 4:
        raise
    if mode == 5:
        self.mode = 0
        raw_call(self.callback_target, self.callback_data)
    if mode == 1:
        return 0
    if mode == 2:
        return _amount - 1
    if mode == 3:
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


CALLER_SENSITIVE_BALANCE_TOKEN_SOURCE = """
# @version 0.4.3

balances: HashMap[address, uint256]
allowances: HashMap[address, HashMap[address, uint256]]
vault_caller: public(address)
vault_mode: public(uint256)

@external
def mint(_to: address, _amount: uint256):
    self.balances[_to] += _amount

@external
def configure_vault_observation(_vault: address, _mode: uint256):
    self.vault_caller = _vault
    self.vault_mode = _mode

@view
@external
@raw_return
def balanceOf(_holder: address) -> Bytes[65]:
    value: uint256 = self.balances[_holder]
    if msg.sender == self.vault_caller:
        if self.vault_mode == 1:
            if value != 0:
                value -= 1
            return slice(convert(value, bytes32), 0, 32)
        if self.vault_mode == 2:
            return concat(convert(value, bytes32), b"x")
        if self.vault_mode == 3:
            return concat(convert(value, bytes32), convert(0, bytes32))
    return slice(convert(value, bytes32), 0, 32)

@view
@external
def balanceValue(_holder: address) -> uint256:
    return self.balances[_holder]

@view
@external
def decimals() -> uint256:
    return 18

@external
def approve(_spender: address, _amount: uint256) -> bool:
    self.allowances[msg.sender][_spender] = _amount
    return True

@external
def transfer(_to: address, _amount: uint256) -> bool:
    self.balances[msg.sender] -= _amount
    self.balances[_to] += _amount
    return True

@external
def transferFrom(_from: address, _to: address, _amount: uint256) -> bool:
    self.allowances[_from][msg.sender] -= _amount
    self.balances[_from] -= _amount
    self.balances[_to] += _amount
    return True
"""


M1_PRICE_CALLBACK_SOURCE = """
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
        raw_call(self.callback_target, self.callback_data)
    return True
"""


M1_ROLLBACK_PROBE_SOURCE = """
# @version 0.4.3

from ethereum.ercs import IERC20

@external
def attemptThenRetry(
    _asset: address,
    _teller: address,
    _firstCalldata: Bytes[1024],
    _retryCalldata: Bytes[1024],
    _allowance: uint256,
) -> (bool, bool):
    assert extcall IERC20(_asset).approve(_teller, _allowance)

    firstSuccess: bool = False
    firstResponse: Bytes[1] = b""
    firstSuccess, firstResponse = raw_call(
        _teller,
        _firstCalldata,
        max_outsize=1,
        revert_on_failure=False,
    )
    assert not firstSuccess

    retrySuccess: bool = False
    retryResponse: Bytes[1] = b""
    retrySuccess, retryResponse = raw_call(
        _teller,
        _retryCalldata,
        max_outsize=1,
        revert_on_failure=False,
    )
    assert retrySuccess

    return firstSuccess, retrySuccess
"""


def _m1_token():
    return boa.loads(
        M1_ADVERSARIAL_TOKEN_SOURCE,
        name="m1_adversarial_token",
        override_address=boa.env.generate_address(),
    )


def _caller_sensitive_balance_token():
    return boa.loads(
        CALLER_SENSITIVE_BALANCE_TOKEN_SOURCE,
        name="caller_sensitive_balance_token",
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


# Keep source-mutant registrations outside Boa's generated-address sequence.
# Auto-anchored tests can reuse generated addresses while Boa retains diagnostic
# type metadata for the prior contract registered at that address.
T6_RECEIPT_EQUALITY_MUTANT_ADDRESS = (
    "0x00000000000000000000000000000000C0DE0001"
)


def _t1_mutex_removal_mutant_source():
    source = Path("contracts/core/Teller.vy").read_text()
    assertion = (
        "    assert not self.receiptMeasurementActive"
        " # dev: receipt measurement active\n"
    )
    assert source.count(assertion) == 1
    source = source.replace(assertion, "", 1)
    assert assertion not in source
    assert (
        "    assert not self.receiptMeasurementActive"
        " # dev: receipt window active\n"
    ) in source
    return source


def _boa_error_has_dev_reason(error, expected_reason):
    return any(
        not isinstance(frame, str)
        and getattr(frame, "dev_reason", None) is not None
        and frame.dev_reason.reason_str == expected_reason
        for frame in error.stack_trace
    )


def _t6_receipt_equality_bypass_mutant_source():
    source = Path("contracts/core/Teller.vy").read_text()
    equality = (
        "        assert extcall Vault(vaultAddr).depositTokensInVault("
        "_user, _asset, amount, _a) == amount # dev: deposit failed\n"
    )
    bypass = (
        "        extcall Vault(vaultAddr).depositTokensInVault("
        "_user, _asset, amount, _a)\n"
    )
    assert source.count(equality) == 1
    source = source.replace(equality, bypass, 1)
    assert equality not in source
    return source


def _t1_setup_mutex_sensitive_trusted_callback(
    active_teller,
    canonical_teller,
    ripe_hq,
    governance,
    credit_engine,
    simple_erc20_vault,
    bob,
    setGeneralConfig,
    setAssetConfig,
    vault_book,
):
    setGeneralConfig()
    token = _m1_token()
    setAssetConfig(token)
    if active_teller.address != canonical_teller.address:
        _m1_replace_hq_address(ripe_hq, governance, 17, active_teller)
    # HumanResources is not otherwise used in this scenario. Rebinding that
    # test registry slot makes the callback token an authorized trusted
    # producer without disturbing the real CreditEngine outer producer.
    _m1_replace_hq_address(ripe_hq, governance, 15, token)

    amount = 100 * EIGHTEEN_DECIMALS
    nested_amount = 1
    vault_id = vault_book.getRegId(simple_erc20_vault)
    token.mint(credit_engine, amount)
    token.approve(active_teller, amount, sender=credit_engine.address)
    token.mint(token, nested_amount)
    token.set_self_allowance(active_teller, nested_amount)
    nested = active_teller.depositFromTrusted.prepare_calldata(
        bob,
        vault_id,
        token,
        nested_amount,
        0,
    )
    token.configure_callback(active_teller, nested, True)
    token.configure_callback_transfer_mode(0)
    token.configure_transfer(2)
    return token, amount, nested_amount, vault_id


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


def test_teller_conversion_uses_preferred_stability_pool_pointer(
    alternate_stability_pool,
    stability_pool,
    registerVault,
    mission_control,
    switchboard_alpha,
    green_token,
    savings_green,
    whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
):
    preferred_id = registerVault(alternate_stability_pool, "Preferred Stability Pool")
    setGeneralConfig()
    setAssetConfig(savings_green, [preferred_id])
    mission_control.setPreferredStabVaultId(preferred_id, sender=switchboard_alpha.address)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, deposit_amount, sender=whale)
    green_token.approve(teller.address, deposit_amount, sender=bob)
    sgreen_amount = teller.convertToSavingsGreenAndDepositIntoStabPool(
        bob,
        deposit_amount,
        sender=bob,
    )

    log = filter_logs(teller, "TellerDeposit")[0]
    assert log.vaultId == preferred_id
    assert log.vaultAddr == alternate_stability_pool.address
    assert alternate_stability_pool.getTotalAmountForUser(bob, savings_green) == sgreen_amount
    assert stability_pool.getTotalAmountForUser(bob, savings_green) == 0


def test_teller_conversion_fails_closed_when_preferred_pointer_is_unset(
    mission_control,
    green_token,
    savings_green,
    whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
):
    setGeneralConfig()
    setAssetConfig(savings_green, [1])
    mission_control.eval("self.preferredStabVaultId = 0")

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, deposit_amount, sender=whale)
    green_token.approve(teller.address, deposit_amount, sender=bob)
    with boa.reverts("invalid vault id"):
        teller.convertToSavingsGreenAndDepositIntoStabPool(bob, deposit_amount, sender=bob)


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
        pytest.param(6, id="dynamic-shaped-first-word-mismatch"),
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


@pytest.mark.parametrize("phase", ("pre", "post"))
def test_m1_typed_balance_observation_accepts_trailing_data(
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
        token.configure_balance(simple_erc20_vault, 5, 0, False)
    else:
        token.configure_balance(simple_erc20_vault, 0, 5, True)

    assert teller.deposit(
        token,
        amount,
        bob,
        simple_erc20_vault,
        sender=bob,
    ) == amount

    assert token.balanceValue(bob) == 0
    assert token.balanceValue(simple_erc20_vault) == amount
    assert simple_erc20_vault.getTotalAmountForUser(bob, token) == amount
    assert ledger.getNumUserVaults(bob) == 1


@pytest.mark.parametrize(
    "vault_mode",
    (
        pytest.param(1, id="returns-zero"),
        pytest.param(2, id="returns-less"),
        pytest.param(3, id="returns-more"),
        pytest.param(4, id="reverts"),
    ),
)
def test_deposit_reverts_when_vault_reports_result_different_from_receipt(
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


def test_deposit_succeeds_when_vault_result_matches_exact_receipt(
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

    assert teller.deposit(
        token,
        amount,
        bob,
        simple_erc20_vault,
        sender=bob,
    ) == amount
    assert token.balanceValue(bob) == 0
    assert token.balanceValue(simple_erc20_vault) == amount
    assert simple_erc20_vault.getTotalAmountForUser(bob, token) == amount
    assert ledger.isParticipatingInVault(bob, 3)
    assert ledger.getNumUserVaults(bob) == 1


def test_removed_single_item_routes_are_not_callable_at_runtime(teller, bob):
    probe = boa.loads(
        """# @version 0.4.3

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
""",
        name="removed_teller_selector_probe",
    )
    route_families = (
        (
            "redeemCollateral",
            ("address", "uint256", "address", "uint256", "bool", "bool", "bool", "address"),
            (str(bob), 1, str(bob), 1, False, False, False, str(bob)),
            range(3, 9),
        ),
        (
            "buyFungibleAuction",
            ("address", "uint256", "address", "uint256", "bool", "bool", "bool", "address"),
            (str(bob), 1, str(bob), 1, False, False, False, str(bob)),
            range(3, 9),
        ),
        (
            "claimFromStabilityPool",
            ("uint256", "address", "address", "uint256", "address", "bool"),
            (1, str(bob), str(bob), 1, str(bob), False),
            range(3, 7),
        ),
        (
            "redeemFromStabilityPool",
            ("uint256", "address", "uint256", "address", "bool", "bool", "bool"),
            (1, str(bob), 1, str(bob), False, False, False),
            range(2, 8),
        ),
    )
    checked_signatures = []
    for name, all_types, all_values, arities in route_families:
        for arity in arities:
            types = all_types[:arity]
            signature = f"{name}({','.join(types)})"
            calldata = keccak(text=signature)[:4] + encode(types, all_values[:arity])
            assert not probe.call_succeeds(teller, calldata), signature
            checked_signatures.append(signature)

    assert len(checked_signatures) == 22
    # The four surviving batch-family raw-calldata controls live in
    # test_teller_action_block.py. They use this same keccak-plus-ABI encoding,
    # compare it with production prepare_calldata, and execute each selector
    # through the deployed Teller and a shared downstream recorder.
    assert probe.call_succeeds(teller, keccak(text="isPaused()")[:4])


def test_t6_vault_receipt_equality_mutant_silently_accepts_short_report(
    ripe_hq,
    governance,
    credit_engine,
    vault_book,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    ledger,
):
    def setup(active_teller):
        setGeneralConfig()
        token = _m1_token()
        vault = boa.loads(
            M1_ADVERSARIAL_VAULT_SOURCE,
            name="t6_short_report_vault",
            override_address=boa.env.generate_address(),
        )
        vault_id = _m1_register_vault(vault_book, governance, vault)
        setAssetConfig(token, _vaultIds=[vault_id])
        vault.configure(2, active_teller, b"")
        amount = 100 * EIGHTEEN_DECIMALS
        token.mint(credit_engine, amount)
        token.approve(active_teller, amount, sender=credit_engine.address)
        return token, vault, vault_id, amount

    with boa.env.anchor():
        token, vault, vault_id, amount = setup(teller)
        # Teller's equality assert has no dev reason. The succeeding SHA-pinned
        # mutant branch below isolates this bare revert to that exact guard.
        with boa.reverts():
            teller.depositFromTrusted(
                bob,
                vault_id,
                token,
                amount,
                0,
                sender=credit_engine.address,
            )
        assert token.balanceValue(credit_engine) == amount
        assert token.balanceValue(vault) == 0
        assert ledger.getNumUserVaults(bob) == 0
        assert filter_logs(teller, "TellerDeposit") == []

    with boa.env.anchor():
        mutant = boa.loads(
            _t6_receipt_equality_bypass_mutant_source(),
            ripe_hq,
            False,
            name="t6_teller_without_receipt_equality",
            override_address=T6_RECEIPT_EQUALITY_MUTANT_ADDRESS,
        )
        _m1_replace_hq_address(ripe_hq, governance, 17, mutant)
        token, vault, vault_id, amount = setup(mutant)

        assert mutant.depositFromTrusted(
            bob,
            vault_id,
            token,
            amount,
            0,
            sender=credit_engine.address,
        ) == amount
        assert token.balanceValue(vault) == amount
        assert vault.mode() == 2
        assert ledger.isParticipatingInVault(bob, vault_id)
        assert [log.amount for log in filter_logs(mutant, "TellerDeposit")] == [
            amount
        ]


def test_t6_real_basic_vault_blocks_short_report_without_teller_equality(
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
    """BasicVault remains a defense if Teller's receipt equality is removed."""

    mutant = boa.loads(
        _t6_receipt_equality_bypass_mutant_source(),
        ripe_hq,
        False,
        name="t6_real_vault_without_receipt_equality",
        override_address=T6_RECEIPT_EQUALITY_MUTANT_ADDRESS,
    )
    _m1_replace_hq_address(ripe_hq, governance, 17, mutant)
    setGeneralConfig()
    token = _caller_sensitive_balance_token()
    setAssetConfig(token)
    token.configure_vault_observation(simple_erc20_vault, 1)
    amount = 100 * EIGHTEEN_DECIMALS
    token.mint(credit_engine, amount)
    token.approve(mutant, amount, sender=credit_engine.address)
    vault_id = vault_book.getRegId(simple_erc20_vault)

    with boa.reverts(dev="insufficient vault backing"):
        mutant.depositFromTrusted(
            bob,
            vault_id,
            token,
            amount,
            0,
            sender=credit_engine.address,
        )

    assert token.balanceValue(credit_engine) == amount
    assert token.balanceValue(simple_erc20_vault) == 0
    assert ledger.getNumUserVaults(bob) == 0


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


def test_t1_trusted_callback_is_blocked_by_receipt_measurement_mutex(
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
    token, amount, _, vault_id = _t1_setup_mutex_sensitive_trusted_callback(
        teller,
        teller,
        ripe_hq,
        governance,
        credit_engine,
        simple_erc20_vault,
        bob,
        setGeneralConfig,
        setAssetConfig,
        vault_book,
    )

    with boa.reverts():
        teller.depositFromTrusted(
            bob,
            vault_id,
            token,
            amount,
            0,
            sender=credit_engine.address,
        )

    assert token.balanceValue(credit_engine) == amount
    assert token.balanceValue(simple_erc20_vault) == 0
    assert ledger.getNumUserVaults(bob) == 0
    assert filter_logs(teller, "TellerDeposit") == []


def test_t1_mutex_removal_mutant_exposes_offsetting_nested_receipt(
    ripe_hq,
    governance,
    credit_engine,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    ledger,
    vault_book,
):
    def setup(active_teller):
        setGeneralConfig()
        token = _m1_token()
        vault = boa.loads(
            M1_ADVERSARIAL_VAULT_SOURCE,
            name="t1_offsetting_receipt_vault",
            override_address=boa.env.generate_address(),
        )
        vault_id = _m1_register_vault(vault_book, governance, vault)
        setAssetConfig(token, _vaultIds=[vault_id])
        vault.configure(0, active_teller, b"")
        if active_teller.address != teller.address:
            _m1_replace_hq_address(ripe_hq, governance, 17, active_teller)
        _m1_replace_hq_address(ripe_hq, governance, 15, token)

        amount = 100 * EIGHTEEN_DECIMALS
        nested_amount = 1
        token.mint(credit_engine, amount)
        token.approve(active_teller, amount, sender=credit_engine.address)
        token.mint(token, nested_amount)
        token.set_self_allowance(active_teller, nested_amount)
        nested = active_teller.depositFromTrusted.prepare_calldata(
            bob,
            vault_id,
            token,
            nested_amount,
            0,
        )
        token.configure_callback(active_teller, nested, True)
        token.configure_callback_transfer_mode(0)
        token.configure_transfer(2)
        return token, vault, vault_id, amount, nested_amount

    # S2 baseline: the exact named scenario rejects with the reviewed source.
    with boa.env.anchor():
        token, _, vault_id, amount, _ = setup(teller)
        with boa.reverts():
            teller.depositFromTrusted(
                bob,
                vault_id,
                token,
                amount,
                0,
                sender=credit_engine.address,
            )

    # S2 mutant: all four dedicated-mutex constructs are removed exactly once.
    # The mutant compiles/deploys, reaches the same route, and incorrectly
    # allows a Q-1 outer receipt plus one nested receipt to satisfy the outer
    # Q measurement against a deliberately permissive disposable vault.
    with boa.env.anchor():
        mutant = boa.loads(
            _t1_mutex_removal_mutant_source(),
            ripe_hq,
            False,
            name="t1_teller_without_receipt_mutex",
            override_address=boa.env.generate_address(),
        )
        token, vault, vault_id, amount, nested_amount = setup(mutant)

        assert (
            mutant.depositFromTrusted(
                bob,
                vault_id,
                token,
                amount,
                0,
                sender=credit_engine.address,
            )
            == amount
        )
        assert token.balanceValue(vault) == amount
        assert ledger.getNumUserVaults(bob) == 1
        assert [log.amount for log in filter_logs(mutant, "TellerDeposit")] == [
            nested_amount,
            amount,
        ]


def test_t1_real_basic_vault_blocks_offsetting_receipt_without_teller_mutex(
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
    """BasicVault also rejects the offsetting-receipt Teller mutant."""

    mutant = boa.loads(
        _t1_mutex_removal_mutant_source(),
        ripe_hq,
        False,
        name="t1_real_vault_without_receipt_mutex",
        override_address=boa.env.generate_address(),
    )
    token, amount, _, vault_id = _t1_setup_mutex_sensitive_trusted_callback(
        mutant,
        teller,
        ripe_hq,
        governance,
        credit_engine,
        simple_erc20_vault,
        bob,
        setGeneralConfig,
        setAssetConfig,
        vault_book,
    )

    # The outer Teller frame masks the nested BasicVault dev label from
    # boa.reverts(dev=...), so inspect every structured trace frame instead.
    with pytest.raises(BoaError) as exc_info:
        mutant.depositFromTrusted(
            bob,
            vault_id,
            token,
            amount,
            0,
            sender=credit_engine.address,
        )
    assert _boa_error_has_dev_reason(
        exc_info.value,
        "insufficient vault backing",
    )

    assert token.balanceValue(credit_engine) == amount
    assert token.balanceValue(simple_erc20_vault) == 0
    assert ledger.getNumUserVaults(bob) == 0


def test_t2_vault_callback_mode_five_is_blocked_after_custody_read(
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
    setGeneralConfig()
    token = _m1_token()
    callback_vault = boa.loads(
        M1_ADVERSARIAL_VAULT_SOURCE,
        name="t2_callback_vault",
        override_address=boa.env.generate_address(),
    )
    callback_vault_id = _m1_register_vault(
        vault_book,
        governance,
        callback_vault,
    )
    ordinary_vault_id = vault_book.getRegId(simple_erc20_vault)
    setAssetConfig(token, _vaultIds=[callback_vault_id, ordinary_vault_id])
    _m1_replace_hq_address(ripe_hq, governance, 15, callback_vault)

    amount = 100 * EIGHTEEN_DECIMALS
    nested_amount = 1
    token.mint(credit_engine, amount)
    token.approve(teller, amount, sender=credit_engine.address)
    token.mint(callback_vault, nested_amount)
    callback_vault.approve_teller(token, teller, nested_amount)
    nested = teller.depositFromTrusted.prepare_calldata(
        bob,
        ordinary_vault_id,
        token,
        nested_amount,
        0,
    )
    callback_vault.configure(5, teller, nested)

    with boa.reverts():
        teller.depositFromTrusted(
            bob,
            callback_vault_id,
            token,
            amount,
            0,
            sender=credit_engine.address,
        )

    assert token.balanceValue(credit_engine) == amount
    assert token.balanceValue(callback_vault) == nested_amount
    assert token.balanceValue(simple_erc20_vault) == 0
    assert ledger.getNumUserVaults(bob) == 0
    assert filter_logs(teller, "TellerDeposit") == []


def test_t3_failed_post_acquisition_call_rolls_back_transient_for_retry(
    vault_book,
    governance,
    simple_erc20_vault,
    setGeneralConfig,
    setAssetConfig,
    teller,
):
    setGeneralConfig()
    token = _m1_token()
    bad_vault = boa.loads(
        M1_ADVERSARIAL_VAULT_SOURCE,
        name="t3_bad_vault",
        override_address=boa.env.generate_address(),
    )
    bad_vault_id = _m1_register_vault(vault_book, governance, bad_vault)
    good_vault_id = vault_book.getRegId(simple_erc20_vault)
    setAssetConfig(token, _vaultIds=[bad_vault_id, good_vault_id])
    bad_vault.configure(2, teller, b"")

    probe = boa.loads(
        M1_ROLLBACK_PROBE_SOURCE,
        name="t3_rollback_probe",
        override_address=boa.env.generate_address(),
    )
    amount = 100 * EIGHTEEN_DECIMALS
    token.mint(probe, 2 * amount)
    first = teller.deposit.prepare_calldata(
        token,
        amount,
        probe,
        bad_vault,
    )
    retry = teller.deposit.prepare_calldata(
        token,
        amount,
        probe,
        simple_erc20_vault,
    )

    assert probe.attemptThenRetry(
        token,
        teller,
        first,
        retry,
        2 * amount,
    ) == (False, True)
    assert token.balanceValue(probe) == amount
    assert token.balanceValue(bad_vault) == 0
    assert token.balanceValue(simple_erc20_vault) == amount
    assert simple_erc20_vault.getTotalAmountForUser(probe, token) == amount


def test_t4_offsetting_canonical_balance_lie_is_accepted_trust_boundary(
    simple_erc20_vault,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
):
    setGeneralConfig()
    token = _m1_token()
    setAssetConfig(token)
    amount = 100 * EIGHTEEN_DECIMALS
    token.mint(bob, amount)
    token.mint(simple_erc20_vault, 1)
    token.approve(teller, amount, sender=bob)
    token.configure_transfer(2)
    token.configure_balance(simple_erc20_vault, 0, 8, True)

    assert (
        teller.deposit(
            token,
            amount,
            bob,
            simple_erc20_vault,
            sender=bob,
        )
        == amount
    )
    # The transfer delivered Q-1; a prior one-unit donation plus a canonical
    # post-read lie fabricated reported delta Q. This success is the accepted
    # truthful-balance trust boundary, not supported token behavior.
    assert token.balanceValue(simple_erc20_vault) == amount
    assert simple_erc20_vault.getTotalAmountForUser(bob, token) == amount


def test_t5_post_clear_callback_starts_fresh_measurement_and_succeeds(
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
        M1_PRICE_CALLBACK_SOURCE,
        name="t5_callback_price_desk",
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
        bob,
        vault_id,
        token,
        nested_amount,
        0,
    )
    callback_price_desk.configure(teller, nested)

    assert (
        teller.depositFromTrusted(
            bob,
            vault_id,
            token,
            amount,
            0,
            sender=credit_engine.address,
        )
        == amount
    )
    assert not callback_price_desk.callback_enabled()
    assert token.balanceValue(simple_erc20_vault) == amount + nested_amount
    assert (
        simple_erc20_vault.getTotalAmountForUser(bob, token)
        == amount + nested_amount
    )
    amounts = [log.amount for log in filter_logs(teller, "TellerDeposit")]
    assert amounts == [nested_amount, amount]


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

    spent = redeem_collateral(teller,
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


# The deposit-local mutex and the central housekeeping guard jointly block a
# nested deposit during receipt measurement. This regression separately pins
# the deposit-local half and transient-state recovery.
def test_receipt_measurement_mutex_blocks_nested_deposit(
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
    token, amount, nested_amount, vault_id = (
        _t1_setup_mutex_sensitive_trusted_callback(
            teller,
            teller,
            ripe_hq,
            governance,
            credit_engine,
            simple_erc20_vault,
            bob,
            setGeneralConfig,
            setAssetConfig,
            vault_book,
        )
    )
    token.configure_transfer(0)
    token.configure_callback_rejection_policy(False)
    snapshot = (
        token.balanceValue(credit_engine),
        token.balanceValue(token),
        token.balanceValue(simple_erc20_vault),
        simple_erc20_vault.userBalances(bob, token),
        ledger.getNumUserVaults(bob),
    )

    with pytest.raises(BoaError) as exc_info:
        teller.depositFromTrusted(
            bob,
            vault_id,
            token,
            amount,
            0,
            sender=credit_engine.address,
        )
    assert _boa_error_has_dev_reason(exc_info.value, "receipt measurement active")
    assert snapshot == (
        token.balanceValue(credit_engine),
        token.balanceValue(token),
        token.balanceValue(simple_erc20_vault),
        simple_erc20_vault.userBalances(bob, token),
        ledger.getNumUserVaults(bob),
    )
    assert nested_amount == 1
    assert filter_logs(teller, "TellerDeposit") == []


def test_nonreentrant_deposit_blocks_nested_ordinary_deposit(
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    simple_erc20_vault,
    ledger,
):
    setGeneralConfig()
    token = _m1_token()
    setAssetConfig(token)
    amount = 100 * EIGHTEEN_DECIMALS
    nested_amount = 1
    token.mint(bob, amount)
    token.approve(teller, amount, sender=bob)
    token.mint(token, nested_amount)
    token.set_self_allowance(teller, nested_amount)
    nested = teller.deposit.prepare_calldata(
        token,
        nested_amount,
        bob,
        simple_erc20_vault,
    )
    token.configure_callback(teller, nested, True)
    token.configure_callback_rejection_policy(False)
    token.configure_transfer(0)

    with boa.reverts():
        teller.deposit(token, amount, bob, simple_erc20_vault, sender=bob)
    assert token.balanceValue(bob) == amount
    assert token.balanceValue(token) == nested_amount
    assert token.balanceValue(simple_erc20_vault) == 0
    assert simple_erc20_vault.userBalances(bob, token) == 0
    assert ledger.getNumUserVaults(bob) == 0
    assert filter_logs(teller, "TellerDeposit") == []


def test_receipt_measurement_mutex_allows_normal_sequential_operations(
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
    credit_engine,
):
    setGeneralConfig()
    debt_terms = createDebtTerms(_ltv=50_00, _redemptionThreshold=70_00)
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    mock_price_source.setPrice(alpha_token, 70 * EIGHTEEN_DECIMALS // 100)

    sequential_token = _m1_token()
    setAssetConfig(sequential_token)
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    sequential_token.mint(credit_engine, deposit_amount)
    sequential_token.approve(teller, deposit_amount, sender=credit_engine.address)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    assert teller.depositFromTrusted(
        bob,
        vault_id,
        sequential_token,
        deposit_amount,
        0,
        sender=credit_engine.address,
    ) == deposit_amount
    assert sequential_token.balanceValue(simple_erc20_vault) == deposit_amount

    payment = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, payment, sender=whale)
    green_token.approve(teller, payment, sender=alice)
    bob_collateral_before = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    alice_collateral_before = simple_erc20_vault.getTotalAmountForUser(alice, alpha_token)
    spent = redeem_collateral(
        teller,
        bob,
        vault_id,
        alpha_token,
        payment,
        False,
        True,
        True,
        alice,
        sender=alice,
    )
    assert 0 < spent <= payment
    alice_received = (
        simple_erc20_vault.getTotalAmountForUser(alice, alpha_token)
        - alice_collateral_before
    )
    assert alice_received > 0
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) < bob_collateral_before
    assert alpha_token.balanceOf(alice) == 0


@pytest.mark.parametrize(
    "vault_fixture",
    (
        "simple_erc20_vault",
        "rebase_erc20_vault",
        "stability_pool",
        "ripe_gov_vault",
    ),
)
def test_predeployment_every_canonical_vault_deposit_rejects_non_teller(
    request,
    vault_fixture,
    alpha_token,
    alice,
    bob,
):
    vault = request.getfixturevalue(vault_fixture)
    with boa.reverts("only Teller allowed"):
        vault.depositTokensInVault(
            bob,
            alpha_token,
            1,
            sender=alice,
        )


def test_predeployment_valid_ripe_lock_route_preserves_direct_clamp_boundary(
    ripe_gov_vault,
    switchboard_alpha,
    bob,
    setGeneralConfig,
    setAssetConfig,
    mission_control,
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
    requested = 100 * EIGHTEEN_DECIMALS
    available = requested - 1
    token.mint(ripe_gov_vault, available)

    returned = ripe_gov_vault.depositTokensWithLockDuration(
        bob,
        token,
        requested,
        500,
        sender=teller.address,
    )

    assert returned == available
    assert ripe_gov_vault.getTotalAmountForUser(bob, token) == available
    assert ledger.getNumUserVaults(bob) == 0
    assert filter_logs(teller, "TellerDeposit") == []


@pytest.mark.parametrize(
    ("vault_fixture", "vault_id"),
    (
        pytest.param("simple_erc20_vault", 3, id="basic"),
        pytest.param("rebase_erc20_vault", 4, id="shares"),
        pytest.param("stability_pool", 1, id="stab"),
    ),
)
def test_predeployment_legacy_clamp_is_closed_by_teller_equality_and_rollback(
    request,
    vault_fixture,
    vault_id,
    bob,
    setGeneralConfig,
    setAssetConfig,
    mock_price_source,
    teller,
    ledger,
):
    setGeneralConfig()
    vault = request.getfixturevalue(vault_fixture)
    token = _caller_sensitive_balance_token()
    setAssetConfig(token, _vaultIds=[vault_id])
    mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
    amount = 100 * EIGHTEEN_DECIMALS
    token.configure_vault_observation(vault, 1)

    # Protected Basic rejects a short observed balance; legacy share/stability
    # helpers retain their direct-call clamp. Teller rolls either behavior back.
    with boa.env.anchor():
        token.mint(vault, amount)
        if vault_fixture == "simple_erc20_vault":
            with boa.reverts("insufficient vault backing"):
                vault.depositTokensInVault(
                    bob,
                    token,
                    amount,
                    sender=teller.address,
                )
            assert vault.getTotalAmountForUser(bob, token) == 0
        else:
            assert vault.depositTokensInVault(
                bob,
                token,
                amount,
                sender=teller.address,
            ) == amount - 1
            assert vault.getTotalAmountForUser(bob, token) != 0

    token.mint(bob, amount)
    token.approve(teller, amount, sender=bob)
    with boa.reverts():
        teller.deposit(token, amount, bob, vault, sender=bob)

    assert token.balanceValue(bob) == amount
    assert token.balanceValue(vault) == 0
    assert vault.getTotalAmountForUser(bob, token) == 0
    assert ledger.getNumUserVaults(bob) == 0
    assert filter_logs(teller, "TellerDeposit") == []


@pytest.mark.parametrize(
    "vault_mode",
    (
        pytest.param(2, id="typed-vault-accepts-33-bytes"),
        pytest.param(3, id="typed-vault-accepts-64-bytes"),
    ),
)
def test_predeployment_typed_vault_balance_accepts_trailing_data(
    vault_mode,
    simple_erc20_vault,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
):
    setGeneralConfig()
    token = _caller_sensitive_balance_token()
    setAssetConfig(token)
    amount = 100 * EIGHTEEN_DECIMALS
    token.configure_vault_observation(simple_erc20_vault, vault_mode)
    token.mint(bob, amount)
    token.approve(teller, amount, sender=bob)

    assert teller.deposit(
        token,
        amount,
        bob,
        simple_erc20_vault,
        sender=bob,
    ) == amount
    assert token.balanceValue(bob) == 0
    assert token.balanceValue(simple_erc20_vault) == amount
    assert simple_erc20_vault.getTotalAmountForUser(bob, token) == amount


@pytest.mark.parametrize(
    ("balance_mode", "expected"),
    (
        pytest.param(5, 100 * EIGHTEEN_DECIMALS, id="typed-source-cap-accepts-33-bytes"),
        pytest.param(6, 32, id="dynamic-shaped-source-decodes-offset-word"),
    ),
)
def test_predeployment_typed_source_balance_return_policy(
    balance_mode,
    expected,
    simple_erc20_vault,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
):
    setGeneralConfig()
    token = _m1_token()
    setAssetConfig(token)
    amount = 100 * EIGHTEEN_DECIMALS
    token.mint(bob, amount)
    token.approve(teller, amount, sender=bob)
    token.configure_balance(bob, balance_mode, 0, False)

    assert teller.deposit(
        token,
        amount,
        bob,
        simple_erc20_vault,
        sender=bob,
    ) == expected
    assert token.balanceValue(bob) == amount - expected
    assert token.balanceValue(simple_erc20_vault) == expected


def test_predeployment_eoa_asset_fails_at_typed_source_cap_without_effects(
    simple_erc20_vault,
    alice,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    ledger,
):
    setGeneralConfig()
    setAssetConfig(alice)

    with boa.reverts():
        teller.deposit(
            alice,
            1,
            bob,
            simple_erc20_vault,
            sender=bob,
        )

    assert ledger.getNumUserVaults(bob) == 0
    assert simple_erc20_vault.getTotalAmountForUser(bob, alice) == 0
    assert filter_logs(teller, "TellerDeposit") == []


def test_predeployment_caught_nested_rejection_preserves_exact_outer_receipt(
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
    token, amount, _, vault_id = _t1_setup_mutex_sensitive_trusted_callback(
        teller,
        teller,
        ripe_hq,
        governance,
        credit_engine,
        simple_erc20_vault,
        bob,
        setGeneralConfig,
        setAssetConfig,
        vault_book,
    )
    token.configure_transfer(0)
    token.configure_callback_rejection_policy(True)

    assert teller.depositFromTrusted(
        bob,
        vault_id,
        token,
        amount,
        0,
        sender=credit_engine.address,
    ) == amount

    assert token.callback_was_attempted()
    assert not token.callback_succeeded()
    assert token.balanceValue(simple_erc20_vault) == amount
    assert simple_erc20_vault.getTotalAmountForUser(bob, token) == amount
    assert ledger.getNumUserVaults(bob) == 1
    assert [log.amount for log in filter_logs(teller, "TellerDeposit")] == [
        amount
    ]

    token.mint(credit_engine, 1)
    token.approve(teller, 1, sender=credit_engine.address)
    assert teller.depositFromTrusted(
        bob,
        vault_id,
        token,
        1,
        0,
        sender=credit_engine.address,
    ) == 1
    assert simple_erc20_vault.getTotalAmountForUser(bob, token) == amount + 1


@pytest.mark.parametrize(
    "vault_kind",
    ("simple", "rebase", "stability", "governance"),
)
@pytest.mark.parametrize(
    ("transfer_mode", "recipient_numerator", "recipient_offset"),
    (
        pytest.param(0, 100, 0, id="exact"),
        pytest.param(1, 0, 0, id="burn"),
        pytest.param(3, 99, 0, id="fee"),
        pytest.param(4, 100, 1, id="reflection"),
        pytest.param(6, 0, 0, id="false-return"),
        pytest.param(7, 0, 0, id="revert"),
        pytest.param(9, 100, 0, id="no-return"),
        pytest.param(10, 0, 0, id="malformed-short-return"),
        pytest.param(11, 100, 0, id="trailing-return"),
        pytest.param(12, 100, 0, id="callback"),
    ),
)
def test_predeployment_withdrawal_responsibility_matrix(
    vault_kind,
    transfer_mode,
    recipient_numerator,
    recipient_offset,
    simple_erc20_vault,
    rebase_erc20_vault,
    stability_pool,
    ripe_gov_vault,
    bob,
    setGeneralConfig,
    setAssetConfig,
    mission_control,
    switchboard_alpha,
    mock_price_source,
    teller,
):
    setGeneralConfig()
    token = _m1_token()
    vaults = {
        "simple": (simple_erc20_vault, 3),
        "rebase": (rebase_erc20_vault, 4),
        "stability": (stability_pool, 1),
        "governance": (ripe_gov_vault, 2),
    }
    vault, vault_id = vaults[vault_kind]

    if vault_kind == "governance":
        mission_control.setRipeGovVaultConfig(
            token,
            100_00,
            False,
            (100, 1000, 200_00, True, 10_00),
            sender=switchboard_alpha.address,
        )
    setAssetConfig(token, _vaultIds=[vault_id])
    mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)

    amount = 100 * EIGHTEEN_DECIMALS
    token.mint(vault, amount)
    assert vault.depositTokensInVault(
        bob,
        token,
        amount,
        sender=teller.address,
    ) == amount
    if vault_kind == "governance":
        boa.env.time_travel(blocks=1001)

    token.configure_transfer(transfer_mode)
    if transfer_mode == 12:
        token.configure_callback(
            token,
            token.configure_transfer.prepare_calldata(0),
            True,
        )

    exact_delivery_vault_rejects_short_delivery = (
        vault_kind in ("simple", "stability")
        and transfer_mode in (1, 3, 4)
    )
    universally_rejected = transfer_mode in (6, 7, 10)
    should_revert = (
        exact_delivery_vault_rejects_short_delivery or universally_rejected
    )

    if should_revert:
        with boa.reverts():
            teller.withdraw(
                token,
                amount,
                bob,
                vault,
                vault_id,
                sender=bob,
            )
        assert token.balanceValue(vault) == amount
        assert token.balanceValue(bob) == 0
        assert vault.getTotalAmountForUser(bob, token) == amount
        assert filter_logs(teller, "TellerWithdrawal") == []
        return

    assert teller.withdraw(
        token,
        amount,
        bob,
        vault,
        vault_id,
        sender=bob,
    ) == amount
    expected_recipient = (
        amount * recipient_numerator // 100 + recipient_offset
    )
    assert token.balanceValue(vault) == 0
    assert token.balanceValue(bob) == expected_recipient
    assert vault.getTotalAmountForUser(bob, token) == 0
    assert filter_logs(teller, "TellerWithdrawal")[0].amount == amount
    if transfer_mode == 12:
        assert token.callback_was_attempted()
        assert token.transfer_mode() == 0


@pytest.mark.parametrize("outer_route", ("governance", "trusted"))
@pytest.mark.parametrize(
    "nested_action",
    ("protected-withdrawal", "rebalance", "redemption", "liquidation"),
)
def test_predeployment_undecorated_route_reentrancy_cross_product(
    outer_route,
    nested_action,
    ripe_hq_deploy,
    governance,
    vault_book,
    simple_erc20_vault,
    ripe_gov_vault,
    credit_engine,
    mission_control,
    switchboard_alpha,
    setGeneralConfig,
    setAssetConfig,
    teller,
):
    setGeneralConfig()
    token = _m1_token()
    protected_vault = boa.load(
        "contracts/vaults/SimpleErc20.vy",
        ripe_hq_deploy,
        name=f"reentrancy_protected_{outer_route}_{nested_action}",
        override_address=boa.env.generate_address(),
    )
    protected_id = _m1_register_vault(
        vault_book,
        governance,
        protected_vault,
    )
    simple_id = vault_book.getRegId(simple_erc20_vault)

    if outer_route == "governance":
        mission_control.setRipeGovVaultConfig(
            token,
            100_00,
            False,
            (100, 1000, 200_00, True, 10_00),
            sender=switchboard_alpha.address,
        )
        outer_vault = ripe_gov_vault
        outer_id = 2
    else:
        outer_vault = simple_erc20_vault
        outer_id = simple_id
    setAssetConfig(token, _vaultIds=[outer_id, protected_id])

    user = token.address
    protected_position = 10
    token.mint(protected_vault, protected_position)
    assert protected_vault.depositTokensInVault(
        user,
        token,
        protected_position,
        sender=teller.address,
    ) == protected_position

    if nested_action == "protected-withdrawal":
        nested = teller.withdraw.prepare_calldata(
            token,
            1,
            user,
            protected_vault,
            protected_id,
        )
    elif nested_action == "rebalance":
        nested = teller.rebalance.prepare_calldata(
            token,
            simple_id,
            token,
            protected_id,
            1,
            1,
            user,
        )
    elif nested_action == "redemption":
        nested = teller.redeemCollateralFromMany.prepare_calldata(
            [(user, protected_id, token.address, 1)],
            1,
            False,
            False,
            True,
            user,
        )
    else:
        nested = teller.liquidateUser.prepare_calldata(user, True)

    token.configure_callback(teller, nested, True)
    token.configure_callback_rejection_policy(True)
    token.configure_transfer(0)
    amount = 100 * EIGHTEEN_DECIMALS

    if outer_route == "governance":
        token.mint(token, amount + 1)
        token.set_self_allowance(teller, amount)
        assert teller.depositIntoGovVault(
            token,
            amount,
            500,
            user,
            sender=user,
        ) == amount
    else:
        token.mint(token, 1)
        token.mint(credit_engine, amount)
        token.approve(teller, amount, sender=credit_engine.address)
        assert teller.depositFromTrusted(
            user,
            outer_id,
            token,
            amount,
            0,
            sender=credit_engine.address,
        ) == amount

    assert token.callback_was_attempted()
    assert token.callback_succeeded() is False
    assert token.balanceValue(outer_vault) == amount
    assert outer_vault.getTotalAmountForUser(user, token) == amount
    assert protected_vault.getTotalAmountForUser(user, token) == protected_position
    assert token.balanceValue(protected_vault) == protected_position
    assert token.balanceValue(token) == 1


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
    # Owner-approved receipt-window guard; any further byte growth requires review.
    assert len(runtime) <= 24_436


############################################################################
# WP1 / WP6 (Section 8.4, Section 13): receipt-window interleaving checkpoint
#
# The full cross-product and the focused rows below pin the owner-approved
# central guard: no custody-changing Teller route may complete during an active
# receipt-measurement window.
############################################################################


@pytest.mark.parametrize("nested_action", ("protected-withdrawal", "liquidation"))
def test_receipt_window_blocks_every_custody_changing_nested_route(
    nested_action,
    ripe_hq_deploy,
    governance,
    vault_book,
    simple_erc20_vault,
    credit_engine,
    setGeneralConfig,
    setAssetConfig,
    teller,
):
    """DV-10 hardening target (SV-6, Section 13).

    While Teller measures an inbound custody delta, no callback may change the
    measured destination's custody or create a dependent vault mutation through
    any other Teller route.
    """
    setGeneralConfig()
    token = _m1_token()
    protected_vault = boa.load(
        "contracts/vaults/SimpleErc20.vy",
        ripe_hq_deploy,
        name=f"receipt_window_guard_{nested_action}",
        override_address=boa.env.generate_address(),
    )
    protected_id = _m1_register_vault(vault_book, governance, protected_vault)
    outer_id = vault_book.getRegId(simple_erc20_vault)
    setAssetConfig(token, _vaultIds=[outer_id, protected_id])

    user = token.address
    protected_position = 10
    token.mint(protected_vault, protected_position)
    assert protected_vault.depositTokensInVault(
        user, token, protected_position, sender=teller.address
    ) == protected_position

    if nested_action == "protected-withdrawal":
        nested = teller.withdraw.prepare_calldata(
            token, 1, user, protected_vault, protected_id
        )
    else:
        nested = teller.liquidateUser.prepare_calldata(user, True)

    token.configure_callback(teller, nested, True)
    token.configure_callback_rejection_policy(True)
    token.configure_transfer(0)

    amount = 100 * EIGHTEEN_DECIMALS
    token.mint(token, 1)
    token.mint(credit_engine, amount)
    token.approve(teller, amount, sender=credit_engine.address)
    assert teller.depositFromTrusted(
        user, outer_id, token, amount, 0, sender=credit_engine.address
    ) == amount

    assert token.callback_was_attempted()
    # No nested custody-changing route may have succeeded inside the window.
    assert token.callback_succeeded() is False
    assert protected_vault.getTotalAmountForUser(user, token) == protected_position
    assert token.balanceValue(protected_vault) == protected_position


############################################################################
# WP1 / WP6 (Section 13): remaining callback-matrix rows
#
# The bound baseline already covers the before-credit callback placement
# (test_predeployment_undecorated_route_reentrancy_cross_product) and mutex
# clearing (test_m1_transfer_callback_reentrancy_reverts_and_mutex_recovers,
# test_t3_failed_post_acquisition_call_rolls_back_transient_for_retry,
# test_t5_post_clear_callback_starts_fresh_measurement_and_succeeds). These add
# the two nested routes and the after-credit placement that were missing.
############################################################################

# transferFrom that credits the destination FIRST and only then fires the
# callback, so the nested action observes a fully credited destination vault.
# The bound repository has no token with this placement.
AFTER_CREDIT_CALLBACK_TOKEN_SOURCE = """
# @version 0.4.3

event Transfer:
    sender: indexed(address)
    receiver: indexed(address)
    value: uint256

name: public(constant(String[32])) = "After Credit Token"
symbol: public(constant(String[32])) = "ACRED"
decimals: public(constant(uint8)) = 18
balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
totalSupply: public(uint256)

callback_target: public(address)
callback_data: public(Bytes[1024])
callback_enabled: public(bool)
callback_was_attempted: public(bool)
callback_succeeded: public(bool)

@deploy
def __init__():
    pass

@external
def mint(_to: address, _value: uint256):
    self.balanceOf[_to] += _value
    self.totalSupply += _value

@external
def configure_callback(_target: address, _data: Bytes[1024]):
    self.callback_target = _target
    self.callback_data = _data
    self.callback_enabled = True
    self.callback_was_attempted = False
    self.callback_succeeded = False

@external
def approve(_spender: address, _value: uint256) -> bool:
    self.allowance[msg.sender][_spender] = _value
    return True

@internal
def _move(_from: address, _to: address, _value: uint256):
    self.balanceOf[_from] -= _value
    # credit FIRST ...
    self.balanceOf[_to] += _value
    log Transfer(sender=_from, receiver=_to, value=_value)
    # ... then hand control to the callback.
    if self.callback_enabled:
        self.callback_enabled = False
        self.callback_was_attempted = True
        success: bool = False
        response: Bytes[1] = b""
        success, response = raw_call(
            self.callback_target,
            self.callback_data,
            max_outsize=1,
            revert_on_failure=False,
        )
        self.callback_succeeded = success

@external
def transfer(_to: address, _value: uint256) -> bool:
    self._move(msg.sender, _to, _value)
    return True

@external
def transferFrom(_from: address, _to: address, _value: uint256) -> bool:
    self.allowance[_from][msg.sender] -= _value
    self._move(_from, _to, _value)
    return True
"""


def _after_credit_token():
    return boa.loads(
        AFTER_CREDIT_CALLBACK_TOKEN_SOURCE,
        name="after_credit_callback_token",
        override_address=boa.env.generate_address(),
    )


@pytest.mark.parametrize("nested_action", ("same_route_deposit", "claim_loot", "deleverage"))
def test_receipt_window_remaining_nested_routes(
    nested_action,
    ripe_hq_deploy,
    governance,
    vault_book,
    simple_erc20_vault,
    credit_engine,
    setGeneralConfig,
    setAssetConfig,
    teller,
):
    """Section 13 rows the baseline cross-product did not cover.

    Characterizes whether each nested route completes inside the receipt
    measurement window of an undecorated outer `depositFromTrusted`.
    """
    setGeneralConfig()
    token = _m1_token()
    protected_vault = boa.load(
        "contracts/vaults/SimpleErc20.vy",
        ripe_hq_deploy,
        name=f"receipt_window_extra_{nested_action}",
        override_address=boa.env.generate_address(),
    )
    protected_id = _m1_register_vault(vault_book, governance, protected_vault)
    outer_id = vault_book.getRegId(simple_erc20_vault)
    setAssetConfig(token, _vaultIds=[outer_id, protected_id])

    user = token.address
    token.mint(protected_vault, 10)
    assert protected_vault.depositTokensInVault(
        user, token, 10, sender=teller.address
    ) == 10

    if nested_action == "same_route_deposit":
        nested = teller.depositFromTrusted.prepare_calldata(
            user, protected_id, token.address, 1, 0
        )
    elif nested_action == "claim_loot":
        nested = teller.claimLoot.prepare_calldata(user, False)
    else:
        nested = teller.deleverageManyUsers.prepare_calldata(
            [(user, MAX_UINT256)]
        )

    token.configure_callback(teller, nested, True)
    token.configure_callback_rejection_policy(True)
    token.configure_transfer(0)

    amount = 100 * EIGHTEEN_DECIMALS
    token.mint(token, 1)
    token.mint(credit_engine, amount)
    token.approve(teller, amount, sender=credit_engine.address)
    assert teller.depositFromTrusted(
        user, outer_id, token, amount, 0, sender=credit_engine.address
    ) == amount

    assert token.callback_was_attempted()
    assert token.callback_succeeded() is False
    # The outer measurement still produced an exact receipt either way.
    assert simple_erc20_vault.getTotalAmountForUser(user, token) == amount
    assert protected_vault.getTotalAmountForUser(user, token) == 10


def test_after_credit_callback_cannot_corrupt_the_measured_receipt(
    ripe_hq_deploy,
    governance,
    vault_book,
    simple_erc20_vault,
    credit_engine,
    setGeneralConfig,
    setAssetConfig,
    teller,
):
    """Section 13: callback placement AFTER the destination is credited.

    The baseline matrix only exercises a callback fired between debiting the
    depositor and crediting the vault. Here the vault is already credited when
    control is handed over, so a nested withdrawal could remove exactly the
    tokens Teller is about to measure.
    """
    setGeneralConfig()
    token = _after_credit_token()
    protected_vault = boa.load(
        "contracts/vaults/SimpleErc20.vy",
        ripe_hq_deploy,
        name="receipt_window_after_credit_vault",
        override_address=boa.env.generate_address(),
    )
    protected_id = _m1_register_vault(vault_book, governance, protected_vault)
    outer_id = vault_book.getRegId(simple_erc20_vault)
    setAssetConfig(token, _vaultIds=[outer_id, protected_id])

    user = token.address
    token.mint(protected_vault, 10)
    assert protected_vault.depositTokensInVault(
        user, token, 10, sender=teller.address
    ) == 10

    nested = teller.withdraw.prepare_calldata(
        token, 1, user, protected_vault, protected_id
    )
    token.configure_callback(teller, nested)

    amount = 100 * EIGHTEEN_DECIMALS
    token.mint(credit_engine, amount)
    token.approve(teller, amount, sender=credit_engine.address)
    deposited = teller.depositFromTrusted(
        user, outer_id, token, amount, 0, sender=credit_engine.address
    )

    assert token.callback_was_attempted()
    assert token.callback_succeeded() is False
    assert deposited == amount
    assert simple_erc20_vault.getTotalAmountForUser(user, token) == amount
    assert protected_vault.getTotalAmountForUser(user, token) == 10


def test_after_credit_callback_nested_withdrawal_is_blocked(
    ripe_hq_deploy,
    governance,
    vault_book,
    simple_erc20_vault,
    credit_engine,
    setGeneralConfig,
    setAssetConfig,
    teller,
):
    """DV-10 hardening target for the after-credit callback placement (SV-6)."""
    setGeneralConfig()
    token = _after_credit_token()
    protected_vault = boa.load(
        "contracts/vaults/SimpleErc20.vy",
        ripe_hq_deploy,
        name="receipt_window_after_credit_guard_vault",
        override_address=boa.env.generate_address(),
    )
    protected_id = _m1_register_vault(vault_book, governance, protected_vault)
    outer_id = vault_book.getRegId(simple_erc20_vault)
    setAssetConfig(token, _vaultIds=[outer_id, protected_id])

    user = token.address
    token.mint(protected_vault, 10)
    protected_vault.depositTokensInVault(user, token, 10, sender=teller.address)

    token.configure_callback(
        teller,
        teller.withdraw.prepare_calldata(token, 1, user, protected_vault, protected_id),
    )
    amount = 100 * EIGHTEEN_DECIMALS
    token.mint(credit_engine, amount)
    token.approve(teller, amount, sender=credit_engine.address)
    teller.depositFromTrusted(
        user, outer_id, token, amount, 0, sender=credit_engine.address
    )

    assert token.callback_was_attempted()
    assert token.callback_succeeded() is False
    assert protected_vault.getTotalAmountForUser(user, token) == 10
