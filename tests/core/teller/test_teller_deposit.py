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

