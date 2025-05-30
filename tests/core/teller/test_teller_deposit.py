import pytest
import boa

from constants import EIGHTEEN_DECIMALS
from conf_utils import filter_logs


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
    with boa.reverts("others cannot deposit for user"):
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
    setAssetConfig(alpha_token)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, deposit_amount, sender=alpha_token_whale)
    alpha_token.approve(teller.address, deposit_amount, sender=bob)

    # First deposit should succeed
    teller.deposit(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)

    # Second deposit to a different vault should fail
    with boa.reverts("reached max vaults"):
        teller.deposit(alpha_token, deposit_amount, bob, rebase_erc20_vault, sender=bob)


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
    mission_control_gov,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, deposit_amount, sender=alpha_token_whale)
    alpha_token.approve(teller.address, deposit_amount, sender=bob)

    # pause the teller
    teller.pause(True, sender=mission_control_gov.address)
    assert teller.isPaused()

    # attempt deposit should fail
    with boa.reverts("contract paused"):
        teller.deposit(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)

    # unpause the teller
    teller.pause(False, sender=mission_control_gov.address)
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
