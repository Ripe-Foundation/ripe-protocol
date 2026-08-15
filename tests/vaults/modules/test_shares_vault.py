import boa
import pytest
from boa.contracts.base_evm_contract import BoaError

from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS
from conf_utils import assert_reverted_call


DECIMAL_OFFSET = 10 ** 8


REBASE_TOKEN_SOURCE = """
# pragma version ~=0.4.3

scaledBalances: HashMap[address, uint256]
allowance: public(HashMap[address, HashMap[address, uint256]])
scaledTotalSupply: uint256
index: public(uint256)

@deploy
def __init__():
    self.index = 10 ** 18

@view
@external
def decimals() -> uint8:
    return 18

@view
@external
def balanceOf(_user: address) -> uint256:
    return self.scaledBalances[_user] * self.index // 10 ** 18

@view
@external
def totalSupply() -> uint256:
    return self.scaledTotalSupply * self.index // 10 ** 18

@external
def approve(_spender: address, _amount: uint256) -> bool:
    self.allowance[msg.sender][_spender] = _amount
    return True

@internal
def _transfer(_sender: address, _recipient: address, _amount: uint256):
    scaledAmount: uint256 = _amount * 10 ** 18 // self.index
    assert scaledAmount != 0
    assert self.scaledBalances[_sender] >= scaledAmount
    self.scaledBalances[_sender] -= scaledAmount
    self.scaledBalances[_recipient] += scaledAmount

@external
def transfer(_recipient: address, _amount: uint256) -> bool:
    self._transfer(msg.sender, _recipient, _amount)
    return True

@external
def transferFrom(_sender: address, _recipient: address, _amount: uint256) -> bool:
    allowed: uint256 = self.allowance[_sender][msg.sender]
    assert allowed >= _amount
    self.allowance[_sender][msg.sender] = allowed - _amount
    self._transfer(_sender, _recipient, _amount)
    return True

@external
def mint(_recipient: address, _amount: uint256):
    scaledAmount: uint256 = _amount * 10 ** 18 // self.index
    self.scaledBalances[_recipient] += scaledAmount
    self.scaledTotalSupply += scaledAmount

@external
def rebase(_newIndex: uint256):
    assert _newIndex > self.index
    self.index = _newIndex
"""


EXTRA_DEBIT_TOKEN_SOURCE = """
# pragma version ~=0.4.3

balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
totalSupply: public(uint256)
extraDebitBps: public(uint256)
feeSink: public(address)
hq: public(address)

@deploy
def __init__(_hq: address, _feeSink: address):
    self.hq = _hq
    self.feeSink = _feeSink
    self.totalSupply = 1_000_000 * 10 ** 18
    self.balanceOf[_hq] = self.totalSupply

@view
@external
def decimals() -> uint8:
    return 18

@external
def setExtraDebitBps(_extraDebitBps: uint256):
    assert msg.sender == self.hq
    assert _extraDebitBps <= 10_000
    self.extraDebitBps = _extraDebitBps

@internal
def _transfer(_sender: address, _recipient: address, _amount: uint256):
    extraDebit: uint256 = _amount * self.extraDebitBps // 10_000
    self.balanceOf[_sender] -= _amount + extraDebit
    self.balanceOf[_recipient] += _amount
    self.balanceOf[self.feeSink] += extraDebit

@external
def transfer(_recipient: address, _amount: uint256) -> bool:
    self._transfer(msg.sender, _recipient, _amount)
    return True

@external
def transferFrom(_sender: address, _recipient: address, _amount: uint256) -> bool:
    self.allowance[_sender][msg.sender] -= _amount
    self._transfer(_sender, _recipient, _amount)
    return True

@external
def approve(_spender: address, _amount: uint256) -> bool:
    self.allowance[msg.sender][_spender] = _amount
    return True
"""


SELECTOR_SPOOF_TOKEN_SOURCE = """
# pragma version ~=0.4.3

balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
totalSupply: public(uint256)
hq: public(address)

@deploy
def __init__(_hq: address):
    self.hq = _hq
    self.totalSupply = 1_000_000 * 10 ** 18
    self.balanceOf[_hq] = self.totalSupply

@view
@external
def decimals() -> uint8:
    return 18

# Spoof both indexed-token interface families. These selectors must not grant
# compatibility to a governance-admitted token with an unknown runtime.
@view
@external
def UNDERLYING_ASSET_ADDRESS() -> address:
    return self.hq

@view
@external
def POOL() -> address:
    return self.hq

@view
@external
def scaledBalanceOf(_user: address) -> uint256:
    return self.balanceOf[_user]

@view
@external
def baseToken() -> address:
    return self.hq

@view
@external
def totalsBasic() -> (uint64, uint64, uint64, uint64, uint104, uint104, uint40, uint8):
    return 10 ** 15, 0, 0, 0, 0, 0, 0, 0

@view
@external
def userBasic(_user: address) -> (int104, uint64, uint64, uint16, uint8):
    return 0, 0, 0, 0, 0

@external
def accrueAccount(_account: address):
    pass

@external
def transfer(_recipient: address, _amount: uint256) -> bool:
    self.balanceOf[msg.sender] -= _amount
    self.balanceOf[_recipient] += _amount + 1
    self.totalSupply += 1
    return True

@external
def transferFrom(_sender: address, _recipient: address, _amount: uint256) -> bool:
    self.allowance[_sender][msg.sender] -= _amount
    self.balanceOf[_sender] -= _amount
    self.balanceOf[_recipient] += _amount
    return True

@external
def approve(_spender: address, _amount: uint256) -> bool:
    self.allowance[msg.sender][_spender] = _amount
    return True
"""


CALLBACK_TOKEN_SOURCE = """
# pragma version ~=0.4.3

balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
totalSupply: public(uint256)
hq: public(address)
attackTarget: public(address)
attackUser: public(address)
attackVault: public(address)
attackVaultId: public(uint256)
attackEnabled: public(bool)
attackAttempted: public(bool)
attackSucceeded: public(bool)

@deploy
def __init__(_hq: address):
    self.hq = _hq
    self.totalSupply = 1_000_000 * 10 ** 18
    self.balanceOf[_hq] = self.totalSupply

@view
@external
def decimals() -> uint8:
    return 18

@external
def configureAttack(_target: address, _user: address, _vault: address, _vaultId: uint256):
    assert msg.sender == self.hq
    self.attackTarget = _target
    self.attackUser = _user
    self.attackVault = _vault
    self.attackVaultId = _vaultId
    self.attackEnabled = True

@internal
def _attemptCallback():
    if self.attackEnabled and not self.attackAttempted:
        self.attackAttempted = True
        payload: Bytes[164] = concat(
            method_id("withdraw(address,uint256,address,address,uint256)"),
            abi_encode(
                self,
                convert(1, uint256),
                self.attackUser,
                self.attackVault,
                self.attackVaultId,
            ),
        )
        self.attackSucceeded = raw_call(
            self.attackTarget,
            payload,
            max_outsize=0,
            revert_on_failure=False,
        )

@external
def transfer(_recipient: address, _amount: uint256) -> bool:
    self._attemptCallback()
    self.balanceOf[msg.sender] -= _amount
    self.balanceOf[_recipient] += _amount
    return True

@external
def transferFrom(_sender: address, _recipient: address, _amount: uint256) -> bool:
    self.allowance[_sender][msg.sender] -= _amount
    self.balanceOf[_sender] -= _amount
    self.balanceOf[_recipient] += _amount
    return True

@external
def approve(_spender: address, _amount: uint256) -> bool:
    self.allowance[msg.sender][_spender] = _amount
    return True
"""


def test_shares_vault_teller_zero_share_deposit_reverts_atomically(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    ledger,
    setGeneralConfig,
    setAssetConfig,
):
    """AUD-024: a nonzero receipt may never be recorded for zero shares."""
    setGeneralConfig()
    setAssetConfig(
        alpha_token,
        _vaultIds=[4],
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
    )

    donation = DECIMAL_OFFSET
    attempted_deposit = 1
    alpha_token.transfer(rebase_erc20_vault, donation, sender=alpha_token_whale)
    alpha_token.transfer(bob, attempted_deposit, sender=alpha_token_whale)
    alpha_token.approve(teller, attempted_deposit, sender=bob)

    vault_id = 4
    assert rebase_erc20_vault.amountToShares(alpha_token, attempted_deposit, False) == 0
    assert attempted_deposit * DECIMAL_OFFSET // (donation + 1) == 0

    user_balance_before = alpha_token.balanceOf(bob)
    allowance_before = alpha_token.allowance(bob, teller)
    custody_before = alpha_token.balanceOf(rebase_erc20_vault)
    user_shares_before = rebase_erc20_vault.userBalances(bob, alpha_token)
    total_shares_before = rebase_erc20_vault.totalBalances(alpha_token)
    user_assets_before = rebase_erc20_vault.numUserAssets(bob)
    vault_assets_before = rebase_erc20_vault.numAssets()
    ledger_data_before = ledger.getDepositLedgerData(bob, vault_id)
    user_points_before = ledger.userDepositPoints(bob, vault_id, alpha_token)
    asset_points_before = ledger.assetDepositPoints(vault_id, alpha_token)
    global_points_before = ledger.globalDepositPoints()
    rewards_before = ledger.ripeRewards()

    # The outer Teller extcall masks nested dev labels from boa.reverts(...),
    # so inspect every structured trace frame for the exact SharesVault reason.
    with pytest.raises(BoaError) as exc_info:
        teller.deposit(
            alpha_token,
            attempted_deposit,
            bob,
            rebase_erc20_vault,
            vault_id,
            sender=bob,
        )
    assert_reverted_call(exc_info.value, "cannot receive 0 shares", teller)

    assert alpha_token.balanceOf(bob) == user_balance_before
    assert alpha_token.allowance(bob, teller) == allowance_before
    assert alpha_token.balanceOf(rebase_erc20_vault) == custody_before
    assert rebase_erc20_vault.userBalances(bob, alpha_token) == user_shares_before
    assert rebase_erc20_vault.totalBalances(alpha_token) == total_shares_before
    assert rebase_erc20_vault.numUserAssets(bob) == user_assets_before
    assert rebase_erc20_vault.numAssets() == vault_assets_before
    assert ledger.getDepositLedgerData(bob, vault_id) == ledger_data_before
    assert ledger.userDepositPoints(bob, vault_id, alpha_token) == user_points_before
    assert ledger.assetDepositPoints(vault_id, alpha_token) == asset_points_before
    assert ledger.globalDepositPoints() == global_points_before
    assert ledger.ripeRewards() == rewards_before


def test_shares_vault_teller_exact_one_share_boundary_succeeds(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    ledger,
    setGeneralConfig,
    setAssetConfig,
):
    """AUD-024: the adjacent fresh-vault boundary still issues one share."""
    setGeneralConfig()
    setAssetConfig(
        alpha_token,
        _vaultIds=[4],
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
    )

    donation = DECIMAL_OFFSET
    deposit_amount = 2
    alpha_token.transfer(rebase_erc20_vault, donation, sender=alpha_token_whale)
    alpha_token.transfer(bob, deposit_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, deposit_amount, sender=bob)

    assert deposit_amount * DECIMAL_OFFSET // (donation + 1) == 1
    deposited = teller.deposit(
        alpha_token,
        deposit_amount,
        bob,
        rebase_erc20_vault,
        4,
        sender=bob,
    )
    deposit_logs = teller.get_logs()

    assert deposited == deposit_amount
    assert alpha_token.balanceOf(rebase_erc20_vault) == donation + deposit_amount
    assert rebase_erc20_vault.userBalances(bob, alpha_token) == 1
    assert rebase_erc20_vault.totalBalances(alpha_token) == 1
    assert ledger.getDepositLedgerData(bob, 4).isParticipatingInVault

    teller_log = next(log for log in deposit_logs if type(log).__name__ == "TellerDeposit")
    assert teller_log.user == bob
    assert teller_log.depositor == bob
    assert teller_log.asset == alpha_token.address
    assert teller_log.amount == deposit_amount
    assert teller_log.vaultAddr == rebase_erc20_vault.address
    assert teller_log.vaultId == 4
    vault_log = next(
        log for log in deposit_logs if type(log).__name__ == "RebaseErc20VaultDeposit"
    )
    assert vault_log.user == bob
    assert vault_log.asset == alpha_token.address
    assert vault_log.amount == deposit_amount
    assert vault_log.shares == 1

    redeemable = rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    assert redeemable == 1
    assert teller.withdraw(
        alpha_token,
        MAX_UINT256,
        bob,
        rebase_erc20_vault,
        4,
        sender=bob,
    ) == redeemable
    assert rebase_erc20_vault.userBalances(bob, alpha_token) == 0
    assert rebase_erc20_vault.totalBalances(alpha_token) == 0


def test_shares_vault_seeded_zero_and_one_share_boundaries(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    teller,
    setGeneralConfig,
    setAssetConfig,
):
    """AUD-024 seeded-vault D_min is derived from live S and B."""
    setGeneralConfig()
    setAssetConfig(
        alpha_token,
        _vaultIds=[4],
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
    )
    alpha_token.transfer(bob, 1, sender=alpha_token_whale)
    alpha_token.approve(teller, 1, sender=bob)
    assert teller.deposit(
        alpha_token, 1, bob, rebase_erc20_vault, 4, sender=bob
    ) == 1

    existing_shares = rebase_erc20_vault.totalBalances(alpha_token)
    underlying_before_donation = alpha_token.balanceOf(rebase_erc20_vault)
    attempted_deposit = 1
    minimum_donation = max(
        0,
        attempted_deposit * (existing_shares + DECIMAL_OFFSET)
        - underlying_before_donation,
    )
    assert existing_shares == DECIMAL_OFFSET
    assert underlying_before_donation == 1
    assert minimum_donation == 199_999_999
    alpha_token.transfer(
        rebase_erc20_vault, minimum_donation, sender=alpha_token_whale
    )
    alpha_token.transfer(sally, 3, sender=alpha_token_whale)
    alpha_token.approve(teller, 3, sender=sally)

    assert rebase_erc20_vault.amountToShares(
        alpha_token, attempted_deposit, False
    ) == 0
    with pytest.raises(BoaError) as exc_info:
        teller.deposit(
            alpha_token,
            attempted_deposit,
            sally,
            rebase_erc20_vault,
            4,
            sender=sally,
        )
    assert_reverted_call(exc_info.value, "cannot receive 0 shares", teller)
    assert alpha_token.balanceOf(sally) == 3
    assert alpha_token.allowance(sally, teller) == 3
    assert rebase_erc20_vault.userBalances(sally, alpha_token) == 0

    assert teller.deposit(
        alpha_token,
        2,
        sally,
        rebase_erc20_vault,
        4,
        sender=sally,
    ) == 2
    assert rebase_erc20_vault.userBalances(sally, alpha_token) == 1


def test_shares_vault_positive_rebase_preserves_shares_and_increases_value(
    rebase_erc20_vault,
    bob,
    teller,
    setGeneralConfig,
    setAssetConfig,
):
    """AUD-024 ordinary RebaseErc20 accounting under a true positive rebase."""
    rebase_token = boa.loads(REBASE_TOKEN_SOURCE, name="aud_024_rebase_token")
    setGeneralConfig()
    setAssetConfig(
        rebase_token,
        _vaultIds=[4],
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
    )
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    rebase_token.mint(bob, deposit_amount)
    rebase_token.approve(teller, deposit_amount, sender=bob)
    assert teller.deposit(
        rebase_token,
        deposit_amount,
        bob,
        rebase_erc20_vault,
        4,
        sender=bob,
    ) == deposit_amount

    shares_before = rebase_erc20_vault.userBalances(bob, rebase_token)
    total_shares_before = rebase_erc20_vault.totalBalances(rebase_token)
    amount_before = rebase_erc20_vault.getTotalAmountForUser(bob, rebase_token)
    custody_before = rebase_token.balanceOf(rebase_erc20_vault)
    assert amount_before == deposit_amount

    rebase_token.rebase(2 * EIGHTEEN_DECIMALS)

    custody_after = rebase_token.balanceOf(rebase_erc20_vault)
    amount_after = rebase_erc20_vault.getTotalAmountForUser(bob, rebase_token)
    assert custody_after == 2 * custody_before
    assert rebase_erc20_vault.userBalances(bob, rebase_token) == shares_before
    assert rebase_erc20_vault.totalBalances(rebase_token) == total_shares_before
    assert amount_after == shares_before * (custody_after + 1) // (
        total_shares_before + DECIMAL_OFFSET
    )
    assert amount_after > amount_before

    # At a 2x index, every even amount is exactly representable in scaled units.
    withdrawal_amount = 50 * EIGHTEEN_DECIMALS
    withdrawal_shares = rebase_erc20_vault.amountToShares(
        rebase_token, withdrawal_amount, True
    )
    vault_before = rebase_token.balanceOf(rebase_erc20_vault)
    recipient_before = rebase_token.balanceOf(bob)

    withdrawn, is_depleted = rebase_erc20_vault.withdrawTokensFromVault(
        bob,
        rebase_token,
        withdrawal_amount,
        bob,
        sender=teller.address,
    )

    assert withdrawn == withdrawal_amount
    assert not is_depleted
    assert vault_before - rebase_token.balanceOf(rebase_erc20_vault) == withdrawn
    assert rebase_token.balanceOf(bob) - recipient_before == withdrawn
    assert (
        rebase_erc20_vault.userBalances(bob, rebase_token)
        == shares_before - withdrawal_shares
    )
    assert (
        rebase_erc20_vault.totalBalances(rebase_token)
        == total_shares_before - withdrawal_shares
    )


def test_shares_vault_deposit_validation(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    switchboard_alpha,
    bob,
    teller,
):
    """Test deposit validation logic in SharesVault"""
    # Test deposit with zero address
    with boa.reverts("invalid user or asset"):
        rebase_erc20_vault.depositTokensInVault(ZERO_ADDRESS, alpha_token, 100, sender=teller.address)
    with boa.reverts("invalid user or asset"):
        rebase_erc20_vault.depositTokensInVault(bob, ZERO_ADDRESS, 100, sender=teller.address)

    # Test deposit with zero amount
    with boa.reverts("invalid deposit amount"):
        rebase_erc20_vault.depositTokensInVault(bob, alpha_token, 0, sender=teller.address)

    # Test deposit when paused
    rebase_erc20_vault.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("contract paused"):
        rebase_erc20_vault.depositTokensInVault(bob, alpha_token, 100, sender=teller.address)
    rebase_erc20_vault.pause(False, sender=switchboard_alpha.address)

    # Test deposit with amount larger than balance
    large_amount = 1000000 * EIGHTEEN_DECIMALS
    small_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, small_amount, sender=alpha_token_whale)
    deposited = rebase_erc20_vault.depositTokensInVault(bob, alpha_token, large_amount, sender=teller.address)
    assert deposited == small_amount  # Should only deposit what's available


def test_shares_vault_initial_deposit(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    _test,
):
    """Test initial deposit and share calculation"""
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, deposit_amount, sender=alpha_token_whale)
    
    # First deposit should create 1:1 shares
    deposited = rebase_erc20_vault.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)
    assert deposited == deposit_amount

    # Check shares and amounts
    amount = rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    _test(deposit_amount, amount)  # Amount should be close to deposit_amount


def test_shares_vault_multiple_deposits(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    teller,
    _test,
):
    """Test multiple deposits and share calculations"""
    # First deposit
    deposit1 = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, deposit1, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(bob, alpha_token, deposit1, sender=teller.address)
    
    # Second deposit
    deposit2 = 200 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, deposit2, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(sally, alpha_token, deposit2, sender=teller.address)

    # Check shares and amounts
    bob_amount = rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    sally_amount = rebase_erc20_vault.getTotalAmountForUser(sally, alpha_token)

    # Bob should have ~1/3 of total shares
    _test(deposit1, bob_amount)
    
    # Sally should have ~2/3 of total shares
    _test(deposit2, sally_amount)


def test_shares_vault_withdrawal(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    _test,
):
    """Test withdrawal and share calculations"""
    # Setup initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, deposit_amount, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Withdraw half
    withdraw_amount = deposit_amount // 2
    user_shares_before = rebase_erc20_vault.userBalances(bob, alpha_token)
    total_shares_before = rebase_erc20_vault.totalBalances(alpha_token)
    expected_withdrawal_shares = rebase_erc20_vault.amountToShares(
        alpha_token, withdraw_amount, True
    )
    vault_before = alpha_token.balanceOf(rebase_erc20_vault)
    recipient_before = alpha_token.balanceOf(bob)
    withdrawn, is_depleted = rebase_erc20_vault.withdrawTokensFromVault(
        bob, alpha_token, withdraw_amount, bob, sender=teller.address
    )
    assert not is_depleted
    assert withdrawn == withdraw_amount
    assert vault_before - alpha_token.balanceOf(rebase_erc20_vault) == withdrawn
    assert alpha_token.balanceOf(bob) - recipient_before == withdrawn
    assert (
        rebase_erc20_vault.userBalances(bob, alpha_token)
        == user_shares_before - expected_withdrawal_shares
    )
    assert (
        rebase_erc20_vault.totalBalances(alpha_token)
        == total_shares_before - expected_withdrawal_shares
    )

    # Check remaining shares and amount
    remaining_amount = rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    _test(deposit_amount - withdraw_amount, remaining_amount)

    # Withdraw remaining
    vault_before = alpha_token.balanceOf(rebase_erc20_vault)
    recipient_before = alpha_token.balanceOf(bob)
    withdrawn, is_depleted = rebase_erc20_vault.withdrawTokensFromVault(
        bob, alpha_token, remaining_amount, bob, sender=teller.address
    )
    assert is_depleted
    assert withdrawn == remaining_amount
    assert vault_before - alpha_token.balanceOf(rebase_erc20_vault) == withdrawn
    assert alpha_token.balanceOf(bob) - recipient_before == withdrawn
    assert rebase_erc20_vault.userBalances(bob, alpha_token) == 0
    assert rebase_erc20_vault.totalBalances(alpha_token) == 0
    assert rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0
    assert alpha_token.balanceOf(rebase_erc20_vault) == 0


def test_shares_vault_short_recipient_delivery_reverts_atomically(
    rebase_erc20_vault,
    governance,
    bob,
    alice,
    teller,
):
    fee_token = boa.load(
        "contracts/mock/MockFeeOnTransferErc20.vy",
        governance.address,
        0,
        name="shares_vault_short_delivery_token",
    )
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    withdrawal_amount = 40 * EIGHTEEN_DECIMALS
    fee_token.transfer(
        rebase_erc20_vault, deposit_amount, sender=governance.address
    )
    rebase_erc20_vault.depositTokensInVault(
        bob, fee_token, deposit_amount, sender=teller.address
    )
    fee_token.setTransferFee(5_00, sender=governance.address)

    state_before = (
        rebase_erc20_vault.userBalances(bob, fee_token),
        rebase_erc20_vault.totalBalances(fee_token),
        rebase_erc20_vault.getTotalAmountForUser(bob, fee_token),
        rebase_erc20_vault.getTotalAmountForVault(fee_token),
        rebase_erc20_vault.numUserAssets(bob),
        rebase_erc20_vault.numAssets(),
        fee_token.balanceOf(rebase_erc20_vault),
        fee_token.balanceOf(alice),
        fee_token.balanceOf(governance),
    )

    with boa.reverts("invalid recipient delivery"):
        rebase_erc20_vault.withdrawTokensFromVault(
            bob,
            fee_token,
            withdrawal_amount,
            alice,
            sender=teller.address,
        )

    assert (
        rebase_erc20_vault.userBalances(bob, fee_token),
        rebase_erc20_vault.totalBalances(fee_token),
        rebase_erc20_vault.getTotalAmountForUser(bob, fee_token),
        rebase_erc20_vault.getTotalAmountForVault(fee_token),
        rebase_erc20_vault.numUserAssets(bob),
        rebase_erc20_vault.numAssets(),
        fee_token.balanceOf(rebase_erc20_vault),
        fee_token.balanceOf(alice),
        fee_token.balanceOf(governance),
    ) == state_before


def test_shares_vault_full_short_delivery_reverts_without_consuming_shares(
    rebase_erc20_vault,
    governance,
    bob,
    alice,
    teller,
):
    """B-OBS-037: a full exit below attainable custody remains atomic."""
    fee_token = boa.load(
        "contracts/mock/MockFeeOnTransferErc20.vy",
        governance.address,
        0,
        name="shares_vault_full_short_delivery_token",
    )
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    fee_token.transfer(
        rebase_erc20_vault, deposit_amount, sender=governance.address
    )
    rebase_erc20_vault.depositTokensInVault(
        bob, fee_token, deposit_amount, sender=teller.address
    )
    fee_token.setTransferFee(5_00, sender=governance.address)
    state_before = (
        rebase_erc20_vault.userBalances(bob, fee_token),
        rebase_erc20_vault.totalBalances(fee_token),
        rebase_erc20_vault.getTotalAmountForUser(bob, fee_token),
        fee_token.balanceOf(rebase_erc20_vault),
        fee_token.balanceOf(alice),
        fee_token.balanceOf(governance),
    )

    with boa.reverts("invalid recipient delivery"):
        rebase_erc20_vault.withdrawTokensFromVault(
            bob,
            fee_token,
            MAX_UINT256,
            alice,
            sender=teller.address,
        )

    assert (
        rebase_erc20_vault.userBalances(bob, fee_token),
        rebase_erc20_vault.totalBalances(fee_token),
        rebase_erc20_vault.getTotalAmountForUser(bob, fee_token),
        fee_token.balanceOf(rebase_erc20_vault),
        fee_token.balanceOf(alice),
        fee_token.balanceOf(governance),
    ) == state_before


def test_shares_vault_excess_vault_outflow_reverts_atomically(
    rebase_erc20_vault,
    governance,
    bob,
    alice,
    sally,
    teller,
):
    extra_debit_token = boa.loads(
        EXTRA_DEBIT_TOKEN_SOURCE,
        governance.address,
        sally,
        name="shares_vault_extra_debit_token",
    )
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    vault_surplus = 10 * EIGHTEEN_DECIMALS
    withdrawal_amount = 50 * EIGHTEEN_DECIMALS
    extra_debit_token.transfer(
        rebase_erc20_vault, deposit_amount, sender=governance.address
    )
    rebase_erc20_vault.depositTokensInVault(
        bob, extra_debit_token, deposit_amount, sender=teller.address
    )
    # Fund enough unaccounted surplus for the abnormal gross debit to succeed.
    extra_debit_token.transfer(
        rebase_erc20_vault, vault_surplus, sender=governance.address
    )
    extra_debit_token.setExtraDebitBps(10_00, sender=governance.address)
    assert vault_surplus > withdrawal_amount * 10_00 // 10_000

    state_before = (
        rebase_erc20_vault.userBalances(bob, extra_debit_token),
        rebase_erc20_vault.totalBalances(extra_debit_token),
        rebase_erc20_vault.getTotalAmountForUser(bob, extra_debit_token),
        rebase_erc20_vault.getTotalAmountForVault(extra_debit_token),
        rebase_erc20_vault.numUserAssets(bob),
        rebase_erc20_vault.numAssets(),
        extra_debit_token.balanceOf(rebase_erc20_vault),
        extra_debit_token.balanceOf(alice),
        extra_debit_token.balanceOf(sally),
    )

    # Outflow is checked first. Keep delivery exact so this independently pins
    # that reason rather than relying on a token that violates both invariants.
    with boa.reverts("invalid vault outflow"):
        rebase_erc20_vault.withdrawTokensFromVault(
            bob,
            extra_debit_token,
            withdrawal_amount,
            alice,
            sender=teller.address,
        )

    assert (
        rebase_erc20_vault.userBalances(bob, extra_debit_token),
        rebase_erc20_vault.totalBalances(extra_debit_token),
        rebase_erc20_vault.getTotalAmountForUser(bob, extra_debit_token),
        rebase_erc20_vault.getTotalAmountForVault(extra_debit_token),
        rebase_erc20_vault.numUserAssets(bob),
        rebase_erc20_vault.numAssets(),
        extra_debit_token.balanceOf(rebase_erc20_vault),
        extra_debit_token.balanceOf(alice),
        extra_debit_token.balanceOf(sally),
    ) == state_before


def test_rebase_selector_spoof_cannot_enter_indexed_compatibility(
    rebase_erc20_vault,
    governance,
    bob,
    alice,
    teller,
):
    spoof = boa.loads(
        SELECTOR_SPOOF_TOKEN_SOURCE,
        governance.address,
        name="shares_vault_selector_spoof_token",
    )
    funding_amount = 100 * EIGHTEEN_DECIMALS
    spoof.transfer(
        rebase_erc20_vault.address,
        funding_amount,
        sender=governance.address,
    )
    admitted_amount = funding_amount + 1
    rebase_erc20_vault.depositTokensInVault(
        bob, spoof, admitted_amount, sender=teller.address
    )
    state_before = (
        rebase_erc20_vault.userBalances(bob, spoof),
        rebase_erc20_vault.totalBalances(spoof),
        rebase_erc20_vault.getTotalAmountForUser(bob, spoof),
        spoof.balanceOf(rebase_erc20_vault.address),
        spoof.balanceOf(alice),
        spoof.totalSupply(),
    )

    with boa.reverts("invalid recipient delivery"):
        rebase_erc20_vault.withdrawTokensFromVault(
            bob,
            spoof,
            40 * EIGHTEEN_DECIMALS,
            alice,
            sender=teller.address,
        )

    assert (
        rebase_erc20_vault.userBalances(bob, spoof),
        rebase_erc20_vault.totalBalances(spoof),
        rebase_erc20_vault.getTotalAmountForUser(bob, spoof),
        spoof.balanceOf(rebase_erc20_vault.address),
        spoof.balanceOf(alice),
        spoof.totalSupply(),
    ) == state_before


def test_teller_callback_token_cannot_reenter_withdrawal(
    rebase_erc20_vault,
    vault_book,
    governance,
    bob,
    teller,
    ledger,
    mock_price_source,
    setGeneralConfig,
    setAssetConfig,
):
    callback_token = boa.loads(
        CALLBACK_TOKEN_SOURCE,
        governance.address,
        name="shares_vault_callback_token",
    )
    vault_id = vault_book.getRegId(rebase_erc20_vault)
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    withdrawal_amount = 40 * EIGHTEEN_DECIMALS
    setGeneralConfig()
    setAssetConfig(callback_token, _vaultIds=[vault_id])
    mock_price_source.setPrice(callback_token, EIGHTEEN_DECIMALS)
    callback_token.transfer(bob, deposit_amount, sender=governance.address)
    callback_token.approve(teller, deposit_amount, sender=bob)
    teller.deposit(
        callback_token,
        deposit_amount,
        bob,
        rebase_erc20_vault,
        vault_id,
        sender=bob,
    )
    callback_token.configureAttack(
        teller.address,
        bob,
        rebase_erc20_vault.address,
        vault_id,
        sender=governance.address,
    )
    shares_before = rebase_erc20_vault.userBalances(bob, callback_token)
    expected_shares = rebase_erc20_vault.amountToShares(
        callback_token, withdrawal_amount, True
    )
    vault_before = callback_token.balanceOf(rebase_erc20_vault.address)
    recipient_before = callback_token.balanceOf(bob)

    withdrawn = teller.withdraw(
        callback_token,
        withdrawal_amount,
        bob,
        rebase_erc20_vault,
        vault_id,
        sender=bob,
    )

    assert callback_token.attackAttempted()
    assert not callback_token.attackSucceeded()
    assert withdrawn == withdrawal_amount
    assert vault_before - callback_token.balanceOf(rebase_erc20_vault.address) == withdrawn
    assert callback_token.balanceOf(bob) - recipient_before == withdrawn
    assert (
        shares_before - rebase_erc20_vault.userBalances(bob, callback_token)
        == expected_shares
    )
    assert ledger.isParticipatingInVault(bob, vault_id)


def test_teller_fee_on_transfer_deposit_reverts_atomically(
    rebase_erc20_vault,
    vault_book,
    governance,
    bob,
    teller,
    ledger,
    lootbox,
    mock_price_source,
    setGeneralConfig,
    setAssetConfig,
):
    fee_token = boa.load(
        "contracts/mock/MockFeeOnTransferErc20.vy",
        governance.address,
        0,
        name="shares_vault_fee_deposit_token",
    )
    vault_id = vault_book.getRegId(rebase_erc20_vault)
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    setGeneralConfig()
    setAssetConfig(fee_token, _vaultIds=[vault_id])
    mock_price_source.setPrice(fee_token, EIGHTEEN_DECIMALS)
    fee_token.transfer(bob, deposit_amount, sender=governance.address)
    fee_token.setTransferFee(5_00, sender=governance.address)
    fee_token.approve(teller, deposit_amount, sender=bob)
    state_before = (
        fee_token.balanceOf(bob),
        fee_token.balanceOf(rebase_erc20_vault.address),
        fee_token.allowance(bob, teller.address),
        rebase_erc20_vault.userBalances(bob, fee_token),
        rebase_erc20_vault.totalBalances(fee_token),
        rebase_erc20_vault.getNumUserAssets(bob),
        ledger.isParticipatingInVault(bob, vault_id),
        ledger.getDepositLedgerData(bob, vault_id),
        lootbox.hasUnderscoreRewards(),
    )

    with boa.reverts("custody mismatch"):
        teller.deposit(
            fee_token,
            deposit_amount,
            bob,
            rebase_erc20_vault,
            vault_id,
            sender=bob,
        )

    assert (
        fee_token.balanceOf(bob),
        fee_token.balanceOf(rebase_erc20_vault.address),
        fee_token.allowance(bob, teller.address),
        rebase_erc20_vault.userBalances(bob, fee_token),
        rebase_erc20_vault.totalBalances(fee_token),
        rebase_erc20_vault.getNumUserAssets(bob),
        ledger.isParticipatingInVault(bob, vault_id),
        ledger.getDepositLedgerData(bob, vault_id),
        lootbox.hasUnderscoreRewards(),
    ) == state_before


def test_shares_vault_positive_self_recipient_reverts_atomically(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
):
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    withdrawal_amount = 25 * EIGHTEEN_DECIMALS
    alpha_token.transfer(
        rebase_erc20_vault, deposit_amount, sender=alpha_token_whale
    )
    rebase_erc20_vault.depositTokensInVault(
        bob, alpha_token, deposit_amount, sender=teller.address
    )
    state_before = (
        rebase_erc20_vault.userBalances(bob, alpha_token),
        rebase_erc20_vault.totalBalances(alpha_token),
        rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token),
        rebase_erc20_vault.getTotalAmountForVault(alpha_token),
        alpha_token.balanceOf(rebase_erc20_vault),
    )

    with boa.reverts("invalid vault outflow"):
        rebase_erc20_vault.withdrawTokensFromVault(
            bob,
            alpha_token,
            withdrawal_amount,
            rebase_erc20_vault,
            sender=teller.address,
        )

    assert (
        rebase_erc20_vault.userBalances(bob, alpha_token),
        rebase_erc20_vault.totalBalances(alpha_token),
        rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token),
        rebase_erc20_vault.getTotalAmountForVault(alpha_token),
        alpha_token.balanceOf(rebase_erc20_vault),
    ) == state_before


def test_teller_shares_vault_inexact_withdrawal_reverts_atomically(
    rebase_erc20_vault,
    vault_book,
    governance,
    bob,
    teller,
    ledger,
    lootbox,
    mock_price_source,
    setGeneralConfig,
    setAssetConfig,
):
    fee_token = boa.load(
        "contracts/mock/MockFeeOnTransferErc20.vy",
        governance.address,
        0,
        name="teller_shares_vault_short_delivery_token",
    )
    vault_id = vault_book.getRegId(rebase_erc20_vault)
    assert vault_id != 0
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    withdrawal_amount = 40 * EIGHTEEN_DECIMALS
    setGeneralConfig()
    setAssetConfig(fee_token, _vaultIds=[vault_id])
    mock_price_source.setPrice(fee_token, EIGHTEEN_DECIMALS)
    fee_token.transfer(bob, deposit_amount, sender=governance.address)
    fee_token.approve(teller, deposit_amount, sender=bob)
    assert teller.deposit(
        fee_token,
        deposit_amount,
        bob,
        rebase_erc20_vault,
        vault_id,
        sender=bob,
    ) == deposit_amount
    fee_token.setTransferFee(5_00, sender=governance.address)
    boa.env.time_travel(blocks=5)

    vault_state_before = (
        rebase_erc20_vault.userBalances(bob, fee_token),
        rebase_erc20_vault.totalBalances(fee_token),
        rebase_erc20_vault.getTotalAmountForUser(bob, fee_token),
        rebase_erc20_vault.getTotalAmountForVault(fee_token),
        fee_token.balanceOf(rebase_erc20_vault),
        fee_token.balanceOf(bob),
        fee_token.balanceOf(governance),
    )
    # Lootbox stores its deposit-point and reward mutations in Ledger.
    ledger_state_before = (
        ledger.getDepositLedgerData(bob, vault_id),
        ledger.getDepositPointsBundle(bob, vault_id, fee_token),
        ledger.getRipeRewardsBundle(),
    )
    lootbox_state_before = (
        lootbox.hasUnderscoreRewards(),
        lootbox.underscoreSendInterval(),
        lootbox.lastUnderscoreSend(),
        lootbox.undyDepositRewardsAmount(),
        lootbox.undyYieldBonusAmount(),
    )

    with boa.reverts():
        teller.withdraw(
            fee_token,
            withdrawal_amount,
            bob,
            rebase_erc20_vault,
            vault_id,
            sender=bob,
        )

    assert (
        rebase_erc20_vault.userBalances(bob, fee_token),
        rebase_erc20_vault.totalBalances(fee_token),
        rebase_erc20_vault.getTotalAmountForUser(bob, fee_token),
        rebase_erc20_vault.getTotalAmountForVault(fee_token),
        fee_token.balanceOf(rebase_erc20_vault),
        fee_token.balanceOf(bob),
        fee_token.balanceOf(governance),
    ) == vault_state_before
    assert (
        ledger.getDepositLedgerData(bob, vault_id),
        ledger.getDepositPointsBundle(bob, vault_id, fee_token),
        ledger.getRipeRewardsBundle(),
    ) == ledger_state_before
    assert (
        lootbox.hasUnderscoreRewards(),
        lootbox.underscoreSendInterval(),
        lootbox.lastUnderscoreSend(),
        lootbox.undyDepositRewardsAmount(),
        lootbox.undyYieldBonusAmount(),
    ) == lootbox_state_before


def test_shares_vault_transfer(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    teller,
    auction_house,
    _test,
):
    """Test transfer and share calculations"""
    # Setup initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, deposit_amount, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Transfer half
    transfer_amount = deposit_amount // 2
    transferred, is_depleted = rebase_erc20_vault.transferBalanceWithinVault(
        alpha_token, bob, sally, transfer_amount, sender=auction_house.address
    )
    assert not is_depleted
    _test(transfer_amount, transferred)

    # Check shares and amounts after transfer
    bob_amount = rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    sally_amount = rebase_erc20_vault.getTotalAmountForUser(sally, alpha_token)

    _test(deposit_amount - transfer_amount, bob_amount)
    _test(transfer_amount, sally_amount)


def test_shares_vault_share_calculations(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    _test,
):
    """Test share calculation utilities"""
    # Setup initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, deposit_amount, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Test amountToShares
    test_amount = 50 * EIGHTEEN_DECIMALS
    shares = rebase_erc20_vault.amountToShares(alpha_token, test_amount, False)
    user_shares = rebase_erc20_vault.getUserLootBoxShare(bob, alpha_token)
    _test((user_shares // 2) * (10 ** 8), shares)

    # Test sharesToAmount
    amount = rebase_erc20_vault.sharesToAmount(alpha_token, shares, False)
    _test(test_amount, amount)  # Should convert back to original amount

    # Test with rounding up
    shares_up = rebase_erc20_vault.amountToShares(alpha_token, test_amount, True)
    amount_up = rebase_erc20_vault.sharesToAmount(alpha_token, shares_up, True)
    assert shares_up >= shares  # Rounding up should give more shares
    assert amount_up >= amount  # Rounding up should give more amount


def test_shares_vault_utility_functions(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    _test,
):
    """Test utility functions in SharesVault"""
    # Setup initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, deposit_amount, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Test getVaultDataOnDeposit
    vault_data = rebase_erc20_vault.getVaultDataOnDeposit(bob, alpha_token)
    assert vault_data.hasPosition
    assert vault_data.numAssets == 1
    _test(deposit_amount, vault_data.userBalance)
    _test(deposit_amount, vault_data.totalBalance)

    # Test getUserAssetAndAmountAtIndex
    asset, amount = rebase_erc20_vault.getUserAssetAndAmountAtIndex(bob, 1)
    assert asset == alpha_token.address
    _test(deposit_amount, amount)

    # Test getUserAssetAtIndexAndHasBalance
    asset, has_balance = rebase_erc20_vault.getUserAssetAtIndexAndHasBalance(bob, 1)
    assert asset == alpha_token.address
    assert has_balance 

def test_shares_vault_share_value_increase(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    teller,
    _test,
):
    """Test share value increase when vault balance increases without deposits"""
    # Initial deposits
    deposit1 = 100 * EIGHTEEN_DECIMALS
    deposit2 = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, deposit1, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(bob, alpha_token, deposit1, sender=teller.address)
    alpha_token.transfer(rebase_erc20_vault, deposit2, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(sally, alpha_token, deposit2, sender=teller.address)

    # Record initial share values
    bob_initial_shares = rebase_erc20_vault.getUserLootBoxShare(bob, alpha_token)
    sally_initial_shares = rebase_erc20_vault.getUserLootBoxShare(sally, alpha_token)
    bob_initial_amount = rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    sally_initial_amount = rebase_erc20_vault.getTotalAmountForUser(sally, alpha_token)

    # Transfer additional tokens to vault (simulating value increase)
    additional_tokens = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, additional_tokens, sender=alpha_token_whale)

    # Check new share values
    bob_new_amount = rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    sally_new_amount = rebase_erc20_vault.getTotalAmountForUser(sally, alpha_token)
    bob_new_shares = rebase_erc20_vault.getUserLootBoxShare(bob, alpha_token)
    sally_new_shares = rebase_erc20_vault.getUserLootBoxShare(sally, alpha_token)

    # Shares should remain the same
    assert bob_new_shares == bob_initial_shares
    assert sally_new_shares == sally_initial_shares

    # But amounts should increase proportionally
    _test(bob_initial_amount * 3 // 2, bob_new_amount)  # Should be ~1.5x original
    _test(sally_initial_amount * 3 // 2, sally_new_amount)  # Should be ~1.5x original

    # Test withdrawal with increased share value
    withdraw_amount = bob_new_amount // 2
    withdrawn, is_depleted = rebase_erc20_vault.withdrawTokensFromVault(
        bob, alpha_token, withdraw_amount, bob, sender=teller.address
    )
    assert not is_depleted
    _test(withdraw_amount, withdrawn)


def test_shares_vault_share_value_decrease(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    teller,
    _test,
):
    """Test share value decrease when vault balance decreases without withdrawals"""
    # Initial deposits
    deposit1 = 100 * EIGHTEEN_DECIMALS
    deposit2 = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, deposit1, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(bob, alpha_token, deposit1, sender=teller.address)
    alpha_token.transfer(rebase_erc20_vault, deposit2, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(sally, alpha_token, deposit2, sender=teller.address)

    # Record initial share values
    bob_initial_shares = rebase_erc20_vault.getUserLootBoxShare(bob, alpha_token)
    sally_initial_shares = rebase_erc20_vault.getUserLootBoxShare(sally, alpha_token)
    bob_initial_amount = rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    sally_initial_amount = rebase_erc20_vault.getTotalAmountForUser(sally, alpha_token)

    # Simulate value decrease by transferring tokens out
    tokens_to_recover = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(alpha_token_whale, tokens_to_recover, sender=rebase_erc20_vault.address)

    # Check new share values
    bob_new_amount = rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    sally_new_amount = rebase_erc20_vault.getTotalAmountForUser(sally, alpha_token)
    bob_new_shares = rebase_erc20_vault.getUserLootBoxShare(bob, alpha_token)
    sally_new_shares = rebase_erc20_vault.getUserLootBoxShare(sally, alpha_token)

    # Shares should remain the same
    assert bob_new_shares == bob_initial_shares
    assert sally_new_shares == sally_initial_shares

    # But amounts should decrease proportionally
    _test(bob_initial_amount // 2, bob_new_amount)  # Should be ~0.5x original
    _test(sally_initial_amount // 2, sally_new_amount)  # Should be ~0.5x original

    # Test withdrawal with decreased share value
    withdraw_amount = bob_new_amount // 2
    withdrawn, is_depleted = rebase_erc20_vault.withdrawTokensFromVault(
        bob, alpha_token, withdraw_amount, bob, sender=teller.address
    )
    assert not is_depleted
    _test(withdraw_amount, withdrawn)


def test_shares_vault_share_value_multiple_changes(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    teller,
    _test,
):
    """Test share value changes with multiple balance changes"""
    # Initial deposits
    deposit1 = 100 * EIGHTEEN_DECIMALS
    deposit2 = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, deposit1, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(bob, alpha_token, deposit1, sender=teller.address)
    alpha_token.transfer(rebase_erc20_vault, deposit2, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(sally, alpha_token, deposit2, sender=teller.address)

    # Record initial values
    bob_initial_shares = rebase_erc20_vault.getUserLootBoxShare(bob, alpha_token)
    sally_initial_shares = rebase_erc20_vault.getUserLootBoxShare(sally, alpha_token)
    bob_initial_amount = rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    sally_initial_amount = rebase_erc20_vault.getTotalAmountForUser(sally, alpha_token)

    # First change: Increase value
    additional_tokens = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, additional_tokens, sender=alpha_token_whale)

    # Second change: Decrease value
    tokens_to_recover = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(alpha_token_whale, tokens_to_recover, sender=rebase_erc20_vault.address)

    # Third change: Increase value again
    additional_tokens2 = 200 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, additional_tokens2, sender=alpha_token_whale)

    # Check final values
    bob_final_amount = rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    sally_final_amount = rebase_erc20_vault.getTotalAmountForUser(sally, alpha_token)
    bob_final_shares = rebase_erc20_vault.getUserLootBoxShare(bob, alpha_token)
    sally_final_shares = rebase_erc20_vault.getUserLootBoxShare(sally, alpha_token)

    # Shares should remain the same
    assert bob_final_shares == bob_initial_shares
    assert sally_final_shares == sally_initial_shares

    # But amounts should reflect all changes
    # Initial: 200 tokens
    # After +100: 300 tokens (1.5x)
    # After -100: 200 tokens (1x)
    # After +200: 400 tokens (2x)
    _test(bob_initial_amount * 2, bob_final_amount)  # Should be 2x original
    _test(sally_initial_amount * 2, sally_final_amount)  # Should be 2x original

    # Test withdrawals with final share value
    bob_withdraw = bob_final_amount // 2
    sally_withdraw = sally_final_amount // 2
    
    withdrawn_bob, is_depleted_bob = rebase_erc20_vault.withdrawTokensFromVault(
        bob, alpha_token, bob_withdraw, bob, sender=teller.address
    )
    withdrawn_sally, is_depleted_sally = rebase_erc20_vault.withdrawTokensFromVault(
        sally, alpha_token, sally_withdraw, sally, sender=teller.address
    )
    
    assert not is_depleted_bob
    assert not is_depleted_sally
    _test(bob_withdraw, withdrawn_bob)
    _test(sally_withdraw, withdrawn_sally)


def test_shares_vault_share_calculation_edge_cases(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    _test,
):
    """Test share calculation edge cases"""
    # Test with very small amounts
    tiny_amount = 1  # 1 wei
    alpha_token.transfer(rebase_erc20_vault, tiny_amount, sender=alpha_token_whale)
    shares = rebase_erc20_vault.amountToShares(alpha_token, tiny_amount, False)
    amount = rebase_erc20_vault.sharesToAmount(alpha_token, shares, False)
    _test(tiny_amount, amount)

    # Test with very large amounts
    large_amount = 1000000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, large_amount, sender=alpha_token_whale)
    shares = rebase_erc20_vault.amountToShares(alpha_token, large_amount, False)
    amount = rebase_erc20_vault.sharesToAmount(alpha_token, shares, False)
    _test(large_amount, amount)

    # Test rounding behavior
    odd_amount = 123456789
    alpha_token.transfer(rebase_erc20_vault, odd_amount, sender=alpha_token_whale)
    shares_down = rebase_erc20_vault.amountToShares(alpha_token, odd_amount, False)
    shares_up = rebase_erc20_vault.amountToShares(alpha_token, odd_amount, True)
    assert shares_up >= shares_down
    assert shares_up - shares_down <= 1  # Should only differ by at most 1


def test_shares_vault_withdrawal_edge_cases(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    teller,
    _test,
):
    """Test withdrawal edge cases"""
    # Setup initial deposits
    deposit1 = 100 * EIGHTEEN_DECIMALS
    deposit2 = 2  # Very small deposit, but more than 1 wei
    alpha_token.transfer(rebase_erc20_vault, deposit1, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(bob, alpha_token, deposit1, sender=teller.address)
    alpha_token.transfer(rebase_erc20_vault, deposit2, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(sally, alpha_token, deposit2, sender=teller.address)

    # Test withdrawal of very small amount
    tiny_withdraw = 1
    withdrawn, is_depleted = rebase_erc20_vault.withdrawTokensFromVault(
        sally, alpha_token, tiny_withdraw, sally, sender=teller.address
    )
    assert not is_depleted  # Should not be depleted since we only withdrew half
    _test(tiny_withdraw, withdrawn)

    # Test withdrawal when total balance is very small
    # First reduce total balance
    current_balance = alpha_token.balanceOf(rebase_erc20_vault)
    alpha_token.transfer(alpha_token_whale, current_balance - 2, sender=rebase_erc20_vault.address)
    
    # Try to withdraw a small amount
    small_withdraw = 1
    withdrawn, is_depleted = rebase_erc20_vault.withdrawTokensFromVault(
        bob, alpha_token, small_withdraw, bob, sender=teller.address
    )
    assert not is_depleted  # Should not be depleted since we're only withdrawing 1 wei
    assert withdrawn > 0


def test_shares_vault_transfer_edge_cases(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    teller,
    auction_house,
    _test,
):
    """Test transfer edge cases"""
    # Setup very different share amounts
    deposit1 = 1000000 * EIGHTEEN_DECIMALS  # Large amount
    deposit2 = 2  # Tiny amount, but more than 1 wei
    alpha_token.transfer(rebase_erc20_vault, deposit1, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(bob, alpha_token, deposit1, sender=teller.address)
    alpha_token.transfer(rebase_erc20_vault, deposit2, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(sally, alpha_token, deposit2, sender=teller.address)

    # Test transfer of tiny amount
    tiny_transfer = 1
    transferred, is_depleted = rebase_erc20_vault.transferBalanceWithinVault(
        alpha_token, bob, sally, tiny_transfer, sender=auction_house.address
    )
    assert not is_depleted
    _test(tiny_transfer, transferred)

    # Test transfer when total balance is very small
    # First reduce total balance
    current_balance = alpha_token.balanceOf(rebase_erc20_vault)
    alpha_token.transfer(alpha_token_whale, current_balance - 2, sender=rebase_erc20_vault.address)
    
    # Try to transfer a small amount
    small_transfer = 1
    transferred, is_depleted = rebase_erc20_vault.transferBalanceWithinVault(
        alpha_token, bob, sally, small_transfer, sender=auction_house.address
    )
    assert not is_depleted  # Should not be depleted since we're only transferring 1 wei
    assert transferred > 0


def test_shares_vault_zero_balance_scenarios(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    _test,
):
    """Test scenarios with zero or near-zero balances"""
    # Setup initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(rebase_erc20_vault, deposit_amount, sender=alpha_token_whale)
    rebase_erc20_vault.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Test share calculations with zero balance
    alpha_token.transfer(alpha_token_whale, deposit_amount, sender=rebase_erc20_vault.address)
    
    # Should still be able to get user data
    vault_data = rebase_erc20_vault.getVaultDataOnDeposit(bob, alpha_token)
    assert vault_data.hasPosition
    assert vault_data.numAssets == 1
    assert vault_data.userBalance == 0
    assert vault_data.totalBalance == 0

    # Should still be able to get user shares
    shares = rebase_erc20_vault.getUserLootBoxShare(bob, alpha_token)
    assert shares > 0  # Shares should remain even if balance is zero

    # Should be able to get asset at index
    asset, amount = rebase_erc20_vault.getUserAssetAndAmountAtIndex(bob, 1)
    assert asset == alpha_token.address
    assert amount == 0  # Amount should be zero

    # Should still show has balance (because shares exist)
    asset, has_balance = rebase_erc20_vault.getUserAssetAtIndexAndHasBalance(bob, 1)
    assert asset == alpha_token.address
    assert has_balance  # Should be true because shares exist
