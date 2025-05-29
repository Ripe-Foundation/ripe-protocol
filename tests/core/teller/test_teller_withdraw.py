import pytest
import boa

from constants import EIGHTEEN_DECIMALS
from conf_utils import filter_logs


def test_teller_basic_withdraw(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    performDeposit,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # withdrawal
    amount = teller.withdraw(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)

    log = filter_logs(teller, "TellerWithdrawal")[0]
    assert log.user == bob
    assert log.asset == alpha_token.address
    assert log.caller == bob
    assert log.amount == deposit_amount == amount
    assert log.vaultAddr == simple_erc20_vault.address
    assert log.vaultId != 0
    assert log.isDepleted == True

    # check balance
    assert alpha_token.balanceOf(simple_erc20_vault) == 0
    assert alpha_token.balanceOf(bob) == amount


def test_teller_withdraw_protocol_disabled(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    performDeposit,
):
    # Setup with protocol withdrawals disabled
    setGeneralConfig(_canWithdraw=False)
    setAssetConfig(alpha_token)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # Attempt withdrawal should fail
    with boa.reverts("protocol withdrawals disabled"):
        teller.withdraw(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)


def test_teller_withdraw_asset_disabled(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    performDeposit,
):
    # Setup with asset withdrawals disabled
    setGeneralConfig()
    setAssetConfig(alpha_token, _canWithdraw=False)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # Attempt withdrawal should fail
    with boa.reverts("asset withdrawals disabled"):
        teller.withdraw(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)


def test_teller_withdraw_user_not_allowed(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    mock_whitelist,
    teller,
    performDeposit,
):
    # Setup with user not allowed
    setGeneralConfig()
    setAssetConfig(alpha_token)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # add whitelist
    setAssetConfig(alpha_token, _whitelist=mock_whitelist)

    # Attempt withdrawal should fail
    with boa.reverts("user not on whitelist"):
        teller.withdraw(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)

    # add to whitelist
    mock_whitelist.setAllowed(bob, alpha_token, True, sender=bob)

    # attempt withdrawal again
    amount = teller.withdraw(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)
    assert amount == deposit_amount


def test_teller_withdraw_others_not_allowed(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    setGeneralConfig,
    setAssetConfig,
    setUserDelegation,
    teller,
    performDeposit,
):
    # Setup with others not allowed to withdraw
    setGeneralConfig()
    setAssetConfig(alpha_token)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # Attempt withdrawal by sally for bob should fail
    with boa.reverts("caller not allowed to withdraw for user"):
        teller.withdraw(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=sally)

    # allow sally to withdraw for bob
    setUserDelegation(bob, sally, _canWithdraw=True)

    # attempt withdrawal again
    amount = teller.withdraw(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=sally)
    assert amount == deposit_amount

    # verify withdrawal was successful
    assert alpha_token.balanceOf(bob) == deposit_amount
    assert alpha_token.balanceOf(simple_erc20_vault) == 0
    assert alpha_token.balanceOf(sally) == 0


def test_teller_withdraw_many(
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
    performDeposit,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(bravo_token)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Perform deposits for both tokens
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    performDeposit(bob, deposit_amount, bravo_token, bravo_token_whale)

    # Create withdrawal actions
    vault_id = vault_book.getRegId(simple_erc20_vault)
    withdrawals = [
        (alpha_token.address, deposit_amount, simple_erc20_vault.address, vault_id),
        (bravo_token.address, deposit_amount, simple_erc20_vault.address, vault_id)
    ]

    # Execute multiple withdrawals
    num_withdrawals = teller.withdrawMany(bob, withdrawals, sender=bob)

    # Get withdrawal logs
    logs = filter_logs(teller, "TellerWithdrawal")
    assert len(logs) == 2

    # Verify number of withdrawals
    assert num_withdrawals == 2

    # Verify alpha token withdrawal
    alpha_log = logs[0]
    assert alpha_log.user == bob
    assert alpha_log.asset == alpha_token.address
    assert alpha_log.caller == bob
    assert alpha_log.amount == deposit_amount
    assert alpha_log.vaultAddr == simple_erc20_vault.address
    assert alpha_log.vaultId == vault_id
    assert alpha_log.isDepleted == True

    # Verify bravo token withdrawal
    bravo_log = logs[1]
    assert bravo_log.user == bob
    assert bravo_log.asset == bravo_token.address
    assert bravo_log.caller == bob
    assert bravo_log.amount == deposit_amount
    assert bravo_log.vaultAddr == simple_erc20_vault.address
    assert bravo_log.vaultId == vault_id
    assert bravo_log.isDepleted == True

    # Verify balances
    assert alpha_token.balanceOf(simple_erc20_vault) == 0
    assert bravo_token.balanceOf(simple_erc20_vault) == 0
    assert alpha_token.balanceOf(bob) == deposit_amount
    assert bravo_token.balanceOf(bob) == deposit_amount


def test_teller_withdraw_teller_paused(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    mission_control,
    performDeposit,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # pause the teller
    teller.pause(True, sender=mission_control.address)
    assert teller.isPaused()

    # attempt withdrawal should fail
    with boa.reverts("contract paused"):
        teller.withdraw(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)

    # unpause the teller
    teller.pause(False, sender=mission_control.address)
    assert not teller.isPaused()

    # withdrawal should now succeed
    amount = teller.withdraw(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)
    assert amount == deposit_amount

    # verify withdrawal was successful
    assert alpha_token.balanceOf(bob) == deposit_amount
    assert alpha_token.balanceOf(simple_erc20_vault) == 0


def test_teller_withdraw_zero_amount(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    performDeposit,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # Attempt withdrawal of zero amount should fail
    with boa.reverts("cannot withdraw 0"):
        teller.withdraw(alpha_token, 0, bob, simple_erc20_vault, sender=bob)


def test_teller_withdraw_nonexistent_vault(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    performDeposit,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # Attempt withdrawal from non-existent vault should fail
    bad_vault_id = 9999
    with boa.reverts("invalid vault id"):
        teller.withdraw(alpha_token, deposit_amount, bob, simple_erc20_vault, bad_vault_id, sender=bob)


def test_teller_withdraw_vault_mismatch(
    simple_erc20_vault,
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    performDeposit,
    vault_book,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # Get vault IDs
    simple_vault_id = vault_book.getRegId(simple_erc20_vault)

    # Attempt withdrawal with mismatched vault ID and address should fail
    with boa.reverts("vault id and vault addr mismatch"):
        teller.withdraw(alpha_token, deposit_amount, bob, rebase_erc20_vault, simple_vault_id, sender=bob)


def test_teller_withdraw_no_balance(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    performDeposit,
    teller,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)

    # deposit / withdraw all
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    teller.withdraw(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)

    # Attempt withdrawal without any balance should fail
    with boa.reverts("nothing to withdraw"):
        teller.withdraw(alpha_token, 100 * EIGHTEEN_DECIMALS, bob, simple_erc20_vault, sender=bob)
