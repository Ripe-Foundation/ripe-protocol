import boa

from constants import EIGHTEEN_DECIMALS, MAX_UINT256
from conf_utils import filter_logs


#####################
# Basic Rebalance Tests #
#####################


def test_teller_basic_rebalance(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    performDeposit,
    vault_book,
):
    """Test basic rebalance from alpha to bravo token"""
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(bravo_token)

    # deposit alpha tokens
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # prepare bravo tokens for deposit
    bravo_token.transfer(bob, deposit_amount, sender=bravo_token_whale)
    bravo_token.approve(teller.address, deposit_amount, sender=bob)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Record initial balances
    initial_bob_alpha = alpha_token.balanceOf(bob)
    initial_bob_bravo = bravo_token.balanceOf(bob)
    initial_vault_alpha = alpha_token.balanceOf(simple_erc20_vault)
    initial_vault_bravo = bravo_token.balanceOf(simple_erc20_vault)

    # rebalance: deposit bravo, withdraw alpha
    withdrawn_amount, deposited_amount = teller.rebalance(
        bravo_token.address,  # deposit asset
        vault_id,  # deposit vault id
        alpha_token.address,  # withdraw asset
        vault_id,  # withdraw vault id
        deposit_amount,  # deposit amount
        deposit_amount,  # withdraw amount
        bob,  # user
        sender=bob
    )

    # verify return values
    assert withdrawn_amount == deposit_amount
    assert deposited_amount == deposit_amount

    # verify event was emitted
    rebalance_logs = filter_logs(teller, "TellerRebalance")
    assert len(rebalance_logs) == 1
    log = rebalance_logs[0]
    assert log.user == bob
    assert log.caller == bob
    assert log.depositAsset == bravo_token.address
    assert log.withdrawAsset == alpha_token.address
    assert log.depositAmount == deposit_amount
    assert log.withdrawAmount == deposit_amount
    assert log.depositVaultId == vault_id
    assert log.withdrawVaultId == vault_id

    # verify balances
    assert alpha_token.balanceOf(bob) == initial_bob_alpha + deposit_amount
    assert bravo_token.balanceOf(bob) == initial_bob_bravo - deposit_amount
    assert alpha_token.balanceOf(simple_erc20_vault) == initial_vault_alpha - deposit_amount
    assert bravo_token.balanceOf(simple_erc20_vault) == initial_vault_bravo + deposit_amount


def test_teller_rebalance_partial_amounts(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    performDeposit,
    vault_book,
):
    """Test rebalancing with partial amounts (not full balance)"""
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(bravo_token)

    # deposit 100 alpha tokens
    total_deposit = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, total_deposit, alpha_token, alpha_token_whale)

    # prepare bravo tokens
    bravo_amount = 50 * EIGHTEEN_DECIMALS
    bravo_token.transfer(bob, bravo_amount, sender=bravo_token_whale)
    bravo_token.approve(teller.address, bravo_amount, sender=bob)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # rebalance: deposit 50 bravo, withdraw 50 alpha (keep 50 alpha)
    withdraw_amount = 50 * EIGHTEEN_DECIMALS
    withdrawn_amount, deposited_amount = teller.rebalance(
        bravo_token.address,  # deposit asset
        vault_id,  # deposit vault id
        alpha_token.address,  # withdraw asset
        vault_id,  # withdraw vault id
        bravo_amount,  # deposit amount
        withdraw_amount,  # withdraw amount
        bob,  # user
        sender=bob
    )

    # verify event was emitted
    rebalance_logs = filter_logs(teller, "TellerRebalance")
    assert len(rebalance_logs) == 1

    assert withdrawn_amount == withdraw_amount
    assert deposited_amount == bravo_amount

    # verify bob still has 50 alpha in vault
    vault_alpha_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    assert vault_alpha_balance == 50 * EIGHTEEN_DECIMALS

    # verify bob has 50 bravo in vault
    vault_bravo_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    assert vault_bravo_balance == bravo_amount


def test_teller_rebalance_same_asset_different_vaults(
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
    """Test rebalancing same asset between different vaults"""
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token, _vaultIds=[3, 4])  # Support alpha in both vaults

    # deposit to simple vault
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # prepare tokens for second deposit
    alpha_token.transfer(bob, deposit_amount, sender=alpha_token_whale)
    alpha_token.approve(teller.address, deposit_amount, sender=bob)

    simple_vault_id = vault_book.getRegId(simple_erc20_vault)
    rebase_vault_id = vault_book.getRegId(rebase_erc20_vault)

    # rebalance: move from simple vault to rebase vault
    withdrawn_amount, deposited_amount = teller.rebalance(
        alpha_token.address,  # deposit asset
        rebase_vault_id,  # deposit vault id
        alpha_token.address,  # withdraw asset
        simple_vault_id,  # withdraw vault id
        deposit_amount,  # deposit amount
        deposit_amount,  # withdraw amount
        bob,  # user
        sender=bob
    )

    # verify event was emitted
    rebalance_logs = filter_logs(teller, "TellerRebalance")
    assert len(rebalance_logs) == 1

    assert withdrawn_amount == deposit_amount
    assert deposited_amount == deposit_amount

    # verify simple vault is depleted
    simple_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    assert simple_vault_balance == 0

    # verify rebase vault has the tokens
    rebase_vault_balance = rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    assert rebase_vault_balance == deposit_amount


def test_teller_rebalance_using_max_value(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    performDeposit,
    vault_book,
):
    """Test rebalancing using MAX_UINT256 for amounts"""
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(bravo_token)

    # deposit alpha tokens
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # prepare bravo tokens - give bob 150, will deposit all
    bravo_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(bob, bravo_amount, sender=bravo_token_whale)
    bravo_token.approve(teller.address, bravo_amount, sender=bob)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # rebalance using max_value for both amounts
    withdrawn_amount, deposited_amount = teller.rebalance(
        bravo_token.address,  # deposit asset
        vault_id,  # deposit vault id
        alpha_token.address,  # withdraw asset
        vault_id,  # withdraw vault id
        MAX_UINT256,  # deposit amount
        MAX_UINT256,  # withdraw amount
        bob,  # user
        sender=bob
    )

    # verify event was emitted
    rebalance_logs = filter_logs(teller, "TellerRebalance")
    assert len(rebalance_logs) == 1

    # verify withdrew all alpha
    assert withdrawn_amount == deposit_amount

    # verify deposited all bravo bob had
    assert deposited_amount == bravo_amount

    # verify balances
    assert bravo_token.balanceOf(bob) == 0
    assert alpha_token.balanceOf(bob) == deposit_amount


#####################
# Permission Tests #
#####################


def test_teller_rebalance_by_delegate_with_both_permissions(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    sally,
    setGeneralConfig,
    setAssetConfig,
    setUserDelegation,
    teller,
    performDeposit,
    vault_book,
):
    """Test that delegate with both withdraw and deposit permissions can rebalance"""
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(bravo_token)

    # deposit alpha for bob
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # give sally bravo tokens to deposit for bob
    bravo_token.transfer(sally, deposit_amount, sender=bravo_token_whale)
    bravo_token.approve(teller.address, deposit_amount, sender=sally)

    # give sally both withdraw and deposit delegation (deposit not in current delegation struct, but handled by canAnyoneDeposit)
    setUserDelegation(bob, sally, _canWithdraw=True)
    teller.setUserConfig(bob, True, True, True, sender=bob)  # allow anyone to deposit for bob

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # sally rebalances for bob
    withdrawn_amount, deposited_amount = teller.rebalance(
        bravo_token.address,  # deposit asset
        vault_id,  # deposit vault id
        alpha_token.address,  # withdraw asset
        vault_id,  # withdraw vault id
        deposit_amount,  # deposit amount
        deposit_amount,  # withdraw amount
        bob,  # user
        sender=sally  # sally is the caller
    )

    assert withdrawn_amount == deposit_amount
    assert deposited_amount == deposit_amount

    # verify event shows correct caller
    log = filter_logs(teller, "TellerRebalance")[0]
    assert log.user == bob
    assert log.caller == sally

    # verify bob got the alpha back (sally withdrew it for bob)
    assert alpha_token.balanceOf(bob) == deposit_amount


def test_teller_rebalance_delegate_without_withdraw_permission_fails(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    sally,
    setGeneralConfig,
    setAssetConfig,
    teller,
    performDeposit,
    vault_book,
):
    """Test that delegate without withdraw permission cannot rebalance"""
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(bravo_token)

    # deposit alpha for bob
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # give sally bravo tokens
    bravo_token.transfer(sally, deposit_amount, sender=bravo_token_whale)
    bravo_token.approve(teller.address, deposit_amount, sender=sally)

    # allow anyone to deposit for bob (so sally can deposit)
    teller.setUserConfig(bob, True, True, True, sender=bob)

    # sally does NOT have withdraw permission for bob

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # sally attempts to rebalance for bob - should fail on withdrawal validation
    with boa.reverts("not allowed to withdraw for user"):
        teller.rebalance(
            bravo_token.address,  # deposit asset
            vault_id,  # deposit vault id
            alpha_token.address,  # withdraw asset
            vault_id,  # withdraw vault id
            deposit_amount,  # deposit amount
            deposit_amount,  # withdraw amount
            bob,  # user
            sender=sally
        )


#####################
# Configuration Tests #
#####################


def test_teller_rebalance_contract_paused(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    performDeposit,
    switchboard_alpha,
    vault_book,
):
    """Test that rebalance fails when contract is paused"""
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(bravo_token)

    # deposit alpha
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # prepare bravo tokens
    bravo_token.transfer(bob, deposit_amount, sender=bravo_token_whale)
    bravo_token.approve(teller.address, deposit_amount, sender=bob)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # pause teller
    teller.pause(True, sender=switchboard_alpha.address)
    assert teller.isPaused()

    # attempt rebalance should fail
    with boa.reverts("contract paused"):
        teller.rebalance(
            bravo_token.address,  # deposit asset
            vault_id,  # deposit vault id
            alpha_token.address,  # withdraw asset
            vault_id,  # withdraw vault id
            deposit_amount,  # deposit amount
            deposit_amount,  # withdraw amount
            bob,  # user
            sender=bob
        )

    # unpause and verify it works
    teller.pause(False, sender=switchboard_alpha.address)
    assert not teller.isPaused()

    withdrawn_amount, deposited_amount = teller.rebalance(
        bravo_token.address,  # deposit asset
        vault_id,  # deposit vault id
        alpha_token.address,  # withdraw asset
        vault_id,  # withdraw vault id
        deposit_amount,  # deposit amount
        deposit_amount,  # withdraw amount
        bob,  # user
        sender=bob
    )

    # verify event was emitted
    rebalance_logs = filter_logs(teller, "TellerRebalance")
    assert len(rebalance_logs) == 1

    assert withdrawn_amount == deposit_amount
    assert deposited_amount == deposit_amount


def test_teller_rebalance_deposit_asset_disabled(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    performDeposit,
    vault_book,
):
    """Test that rebalance fails when deposit asset is disabled"""
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(bravo_token, _canDeposit=False)  # disable bravo deposits

    # deposit alpha
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # prepare bravo tokens
    bravo_token.transfer(bob, deposit_amount, sender=bravo_token_whale)
    bravo_token.approve(teller.address, deposit_amount, sender=bob)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # attempt rebalance should fail
    with boa.reverts("asset deposits disabled"):
        teller.rebalance(
            bravo_token.address,  # deposit asset
            vault_id,  # deposit vault id
            alpha_token.address,  # withdraw asset
            vault_id,  # withdraw vault id
            deposit_amount,  # deposit amount
            deposit_amount,  # withdraw amount
            bob,  # user
            sender=bob
        )


def test_teller_rebalance_withdraw_asset_disabled(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    performDeposit,
    vault_book,
):
    """Test that rebalance fails when withdraw asset is disabled"""
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token, _canWithdraw=False)  # disable alpha withdrawals
    setAssetConfig(bravo_token)

    # deposit alpha
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # prepare bravo tokens
    bravo_token.transfer(bob, deposit_amount, sender=bravo_token_whale)
    bravo_token.approve(teller.address, deposit_amount, sender=bob)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # attempt rebalance should fail
    with boa.reverts("asset withdrawals disabled"):
        teller.rebalance(
            bravo_token.address,  # deposit asset
            vault_id,  # deposit vault id
            alpha_token.address,  # withdraw asset
            vault_id,  # withdraw vault id
            deposit_amount,  # deposit amount
            deposit_amount,  # withdraw amount
            bob,  # user
            sender=bob
        )


#####################
# Debt Health Tests #
#####################


def test_teller_rebalance_with_debt_maintains_health(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    teller,
    performDeposit,
    mock_price_source,
    createDebtTerms,
    vault_book,
    green_token,
):
    """Test that rebalancing with debt succeeds when health remains good"""
    # Setup with LTV terms
    setGeneralConfig()

    # Alpha: 50% LTV, Bravo: 75% LTV
    alpha_debt_terms = createDebtTerms(_ltv=50_00)
    bravo_debt_terms = createDebtTerms(_ltv=75_00)
    setAssetConfig(alpha_token, _debtTerms=alpha_debt_terms)
    setAssetConfig(bravo_token, _debtTerms=bravo_debt_terms)
    setGeneralDebtConfig()

    # Deposit 100 alpha tokens
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # Set prices: alpha=$1, bravo=$1
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)

    # Borrow $25 (well within 50% LTV of $100)
    borrow_amount = 25 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)
    assert green_token.balanceOf(bob) == borrow_amount

    # Prepare bravo tokens (100 tokens = $100 value)
    bravo_token.transfer(bob, deposit_amount, sender=bravo_token_whale)
    bravo_token.approve(teller.address, deposit_amount, sender=bob)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Rebalance: deposit 100 bravo (75% LTV, $75 max debt), withdraw all alpha
    # Final state: $100 bravo collateral with 75% LTV = $75 max debt
    # Current debt: $25
    # Health should be good: $25 < $75
    withdrawn_amount, deposited_amount = teller.rebalance(
        bravo_token.address,  # deposit asset
        vault_id,  # deposit vault id
        alpha_token.address,  # withdraw asset
        vault_id,  # withdraw vault id
        deposit_amount,  # deposit amount
        deposit_amount,  # withdraw amount
        bob,  # user
        sender=bob
    )

    # verify event was emitted
    rebalance_logs = filter_logs(teller, "TellerRebalance")
    assert len(rebalance_logs) == 1

    assert withdrawn_amount == deposit_amount
    assert deposited_amount == deposit_amount

    # Verify balances changed correctly
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == deposit_amount


def test_teller_rebalance_improves_debt_health(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    teller,
    performDeposit,
    mock_price_source,
    createDebtTerms,
    vault_book,
):
    """Test rebalancing from lower LTV asset to higher LTV asset"""
    # Setup with different LTV terms
    setGeneralConfig()

    # Alpha: 50% LTV, Bravo: 80% LTV
    alpha_debt_terms = createDebtTerms(_ltv=50_00)
    bravo_debt_terms = createDebtTerms(_ltv=80_00)
    setAssetConfig(alpha_token, _debtTerms=alpha_debt_terms)
    setAssetConfig(bravo_token, _debtTerms=bravo_debt_terms)
    setGeneralDebtConfig()

    # Deposit 100 alpha
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # Set prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)

    # Borrow $40 (80% of alpha's max capacity)
    borrow_amount = 40 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    # Prepare bravo tokens
    bravo_token.transfer(bob, deposit_amount, sender=bravo_token_whale)
    bravo_token.approve(teller.address, deposit_amount, sender=bob)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Rebalance to bravo (better LTV)
    # Before: $100 alpha @ 50% LTV = $50 max debt, $40 borrowed (80% utilized)
    # After: $100 bravo @ 80% LTV = $80 max debt, $40 borrowed (50% utilized)
    withdrawn_amount, deposited_amount = teller.rebalance(
        bravo_token.address,  # deposit asset
        vault_id,  # deposit vault id
        alpha_token.address,  # withdraw asset
        vault_id,  # withdraw vault id
        deposit_amount,  # deposit amount
        deposit_amount,  # withdraw amount
        bob,  # user
        sender=bob
    )

    # verify event was emitted
    rebalance_logs = filter_logs(teller, "TellerRebalance")
    assert len(rebalance_logs) == 1

    assert withdrawn_amount == deposit_amount
    assert deposited_amount == deposit_amount


def test_teller_rebalance_fails_if_final_health_bad(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    teller,
    performDeposit,
    mock_price_source,
    createDebtTerms,
    vault_book,
):
    """Test rebalancing with moderate debt from better to worse LTV asset"""
    # Setup with different LTV terms
    setGeneralConfig()

    # Alpha: 80% LTV, Bravo: 60% LTV
    alpha_debt_terms = createDebtTerms(_ltv=80_00)
    bravo_debt_terms = createDebtTerms(_ltv=60_00)
    setAssetConfig(alpha_token, _debtTerms=alpha_debt_terms)
    setAssetConfig(bravo_token, _debtTerms=bravo_debt_terms)
    setGeneralDebtConfig()

    # Deposit 100 alpha
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # Set prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)

    # Borrow $50 (moderate debt)
    borrow_amount = 50 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    # Prepare bravo tokens
    bravo_token.transfer(bob, deposit_amount, sender=bravo_token_whale)
    bravo_token.approve(teller.address, deposit_amount, sender=bob)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Rebalance from alpha to bravo (lower LTV but still healthy)
    # Before: $100 alpha @ 80% LTV = $80 max debt, $50 borrowed (healthy)
    # After: $100 bravo @ 60% LTV = $60 max debt, $50 borrowed (still healthy)
    withdrawn_amount, deposited_amount = teller.rebalance(
        bravo_token.address,  # deposit asset
        vault_id,  # deposit vault id
        alpha_token.address,  # withdraw asset
        vault_id,  # withdraw vault id
        deposit_amount,  # deposit amount
        deposit_amount,  # withdraw amount
        bob,  # user
        sender=bob
    )

    # verify event was emitted
    rebalance_logs = filter_logs(teller, "TellerRebalance")
    assert len(rebalance_logs) == 1

    # Verify rebalance completed successfully
    assert withdrawn_amount == deposit_amount
    assert deposited_amount == deposit_amount
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == deposit_amount


def test_teller_rebalance_multi_asset_collateral(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    teller,
    performDeposit,
    mock_price_source,
    createDebtTerms,
    vault_book,
):
    """Test rebalancing when user has multiple collateral assets"""
    # Setup
    setGeneralConfig()

    # Different LTV for each asset
    alpha_debt_terms = createDebtTerms(_ltv=50_00)
    bravo_debt_terms = createDebtTerms(_ltv=60_00)
    charlie_debt_terms = createDebtTerms(_ltv=70_00)
    setAssetConfig(alpha_token, _debtTerms=alpha_debt_terms)
    setAssetConfig(bravo_token, _debtTerms=bravo_debt_terms)
    setAssetConfig(charlie_token, _debtTerms=charlie_debt_terms)
    setGeneralDebtConfig()

    # Deposit alpha and bravo
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    performDeposit(bob, deposit_amount, bravo_token, bravo_token_whale)

    # Set prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, 1 * EIGHTEEN_DECIMALS)

    # Borrow $50
    borrow_amount = 50 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    # Prepare charlie tokens (charlie has 6 decimals)
    charlie_deposit_amount = 100 * (10 ** charlie_token.decimals())
    charlie_token.transfer(bob, charlie_deposit_amount, sender=charlie_token_whale)
    charlie_token.approve(teller.address, charlie_deposit_amount, sender=bob)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Rebalance: deposit charlie, withdraw all alpha
    # Before: $100 alpha (50% LTV=$50 capacity) + $100 bravo (60% LTV=$60 capacity) = $110 total capacity
    # After: $100 charlie (70% LTV=$70 capacity) + $100 bravo (60% LTV=$60 capacity) = $130 total capacity
    # Debt: $50 - should remain healthy
    withdrawn_amount, deposited_amount = teller.rebalance(
        charlie_token.address,  # deposit asset
        vault_id,  # deposit vault id
        alpha_token.address,  # withdraw asset
        vault_id,  # withdraw vault id
        charlie_deposit_amount,  # deposit amount (charlie decimals)
        deposit_amount,  # withdraw amount (alpha decimals)
        bob,  # user
        sender=bob
    )

    # verify event was emitted
    rebalance_logs = filter_logs(teller, "TellerRebalance")
    assert len(rebalance_logs) == 1

    assert withdrawn_amount == deposit_amount
    assert deposited_amount == charlie_deposit_amount

    # Verify final collateral composition
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == deposit_amount
    assert simple_erc20_vault.getTotalAmountForUser(bob, charlie_token) == charlie_deposit_amount


#####################
# Error Cases #
#####################


def test_teller_rebalance_zero_deposit_amount(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    performDeposit,
    vault_book,
):
    """Test that rebalance fails with zero deposit amount"""
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(bravo_token)

    # deposit alpha
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # attempt rebalance with zero deposit amount
    with boa.reverts("cannot deposit 0"):
        teller.rebalance(
            bravo_token.address,  # deposit asset
            vault_id,  # deposit vault id
            alpha_token.address,  # withdraw asset
            vault_id,  # withdraw vault id
            0,  # deposit amount
            deposit_amount,  # withdraw amount
            bob,  # user
            sender=bob
        )


def test_teller_rebalance_zero_withdraw_amount(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    performDeposit,
    vault_book,
):
    """Test that rebalance fails with zero withdraw amount"""
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(bravo_token)

    # deposit alpha
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # prepare bravo
    bravo_token.transfer(bob, deposit_amount, sender=bravo_token_whale)
    bravo_token.approve(teller.address, deposit_amount, sender=bob)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # attempt rebalance with zero withdraw amount
    with boa.reverts("cannot withdraw 0"):
        teller.rebalance(
            bravo_token.address,  # deposit asset
            vault_id,  # deposit vault id
            alpha_token.address,  # withdraw asset
            vault_id,  # withdraw vault id
            deposit_amount,  # deposit amount
            0,  # withdraw amount
            bob,  # user
            sender=bob
        )


def test_teller_rebalance_insufficient_deposit_balance(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    performDeposit,
    vault_book,
):
    """Test that rebalance fails if user doesn't have enough deposit tokens"""
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(bravo_token)

    # deposit alpha
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # DON'T give bob any bravo tokens, but approve teller
    bravo_token.approve(teller.address, deposit_amount, sender=bob)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # attempt rebalance without bravo tokens should fail
    with boa.reverts("cannot deposit 0"):
        teller.rebalance(
            bravo_token.address,  # deposit asset
            vault_id,  # deposit vault id
            alpha_token.address,  # withdraw asset
            vault_id,  # withdraw vault id
            deposit_amount,  # deposit amount
            deposit_amount,  # withdraw amount
            bob,  # user
            sender=bob
        )


def test_teller_rebalance_no_withdrawal_balance(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    vault_book,
):
    """Test that rebalance fails if user has no withdrawal balance"""
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(bravo_token)

    # DON'T deposit any alpha (bob has no alpha in vault)

    # prepare bravo for deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    bravo_token.transfer(bob, deposit_amount, sender=bravo_token_whale)
    bravo_token.approve(teller.address, deposit_amount, sender=bob)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # attempt rebalance should fail when trying to withdraw alpha (none available)
    with boa.reverts():  # Will fail in withdrawal validation
        teller.rebalance(
            bravo_token.address,  # deposit asset
            vault_id,  # deposit vault id
            alpha_token.address,  # withdraw asset
            vault_id,  # withdraw vault id
            deposit_amount,  # deposit amount
            deposit_amount,  # withdraw amount
            bob,  # user
            sender=bob
        )


def test_teller_rebalance_invalid_deposit_vault_id(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    performDeposit,
    vault_book,
):
    """Test that rebalance fails with invalid deposit vault ID"""
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(bravo_token)

    # deposit alpha
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # prepare bravo
    bravo_token.transfer(bob, deposit_amount, sender=bravo_token_whale)
    bravo_token.approve(teller.address, deposit_amount, sender=bob)

    vault_id = vault_book.getRegId(simple_erc20_vault)
    invalid_vault_id = 9999

    # attempt rebalance with invalid vault ID for deposit
    with boa.reverts("invalid vault id"):
        teller.rebalance(
            bravo_token.address,  # deposit asset
            invalid_vault_id,  # deposit vault id
            alpha_token.address,  # withdraw asset
            vault_id,  # withdraw vault id
            deposit_amount,  # deposit amount
            deposit_amount,  # withdraw amount
            bob,  # user
            sender=bob
        )


def test_teller_rebalance_invalid_withdraw_vault_id(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    performDeposit,
    vault_book,
):
    """Test that rebalance fails with invalid withdraw vault ID"""
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(bravo_token)

    # deposit alpha
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # prepare bravo
    bravo_token.transfer(bob, deposit_amount, sender=bravo_token_whale)
    bravo_token.approve(teller.address, deposit_amount, sender=bob)

    vault_id = vault_book.getRegId(simple_erc20_vault)
    invalid_vault_id = 9999

    # attempt rebalance with invalid vault ID for withdrawal
    with boa.reverts("invalid vault id"):
        teller.rebalance(
            bravo_token.address,  # deposit asset
            vault_id,  # deposit vault id
            alpha_token.address,  # withdraw asset
            invalid_vault_id,  # withdraw vault id
            deposit_amount,  # deposit amount
            deposit_amount,  # withdraw amount
            bob,  # user
            sender=bob
        )


#####################
# Edge Cases #
#####################


def test_teller_rebalance_depletes_withdrawal_position(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    performDeposit,
    vault_book,
):
    """Test rebalancing that fully depletes the withdrawal asset position"""
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(bravo_token)

    # deposit alpha
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # prepare bravo
    bravo_token.transfer(bob, deposit_amount, sender=bravo_token_whale)
    bravo_token.approve(teller.address, deposit_amount, sender=bob)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # rebalance: withdraw ALL alpha
    withdrawn_amount, deposited_amount = teller.rebalance(
        bravo_token.address,  # deposit asset
        vault_id,  # deposit vault id
        alpha_token.address,  # withdraw asset
        vault_id,  # withdraw vault id
        deposit_amount,  # deposit amount
        MAX_UINT256,  # withdraw amount
        bob,  # user
        sender=bob
    )

    # verify withdrawal log shows isDepleted
    withdrawal_logs = filter_logs(teller, "TellerWithdrawal")
    assert len(withdrawal_logs) == 1
    assert withdrawal_logs[0].isDepleted == True

    assert withdrawn_amount == deposit_amount

    # verify alpha position is completely depleted
    alpha_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    assert alpha_balance == 0


def test_teller_rebalance_respects_min_balance_on_deposit(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    performDeposit,
    vault_book,
):
    """Test that rebalance respects min balance requirement on deposit"""
    # Setup with min balance requirement
    min_balance = 50 * EIGHTEEN_DECIMALS
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(bravo_token, _minDepositBalance=min_balance)

    # deposit alpha
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # prepare bravo - less than min balance
    small_amount = 25 * EIGHTEEN_DECIMALS
    bravo_token.transfer(bob, small_amount, sender=bravo_token_whale)
    bravo_token.approve(teller.address, deposit_amount, sender=bob)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # attempt rebalance with deposit below min balance should fail
    with boa.reverts("too small a balance"):
        teller.rebalance(
            bravo_token.address,  # deposit asset
            vault_id,  # deposit vault id
            alpha_token.address,  # withdraw asset
            vault_id,  # withdraw vault id
            small_amount,  # deposit amount
            deposit_amount,  # withdraw amount
            bob,  # user
            sender=bob
        )


def test_teller_rebalance_respects_deposit_limits(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    performDeposit,
    vault_book,
):
    """Test that rebalance respects per-user deposit limits"""
    # Setup with user deposit limit
    user_limit = 50 * EIGHTEEN_DECIMALS
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(bravo_token, _perUserDepositLimit=user_limit)

    # deposit alpha
    alpha_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, alpha_amount, alpha_token, alpha_token_whale)

    # prepare bravo - more than user limit
    bravo_amount = 100 * EIGHTEEN_DECIMALS
    bravo_token.transfer(bob, bravo_amount, sender=bravo_token_whale)
    bravo_token.approve(teller.address, bravo_amount, sender=bob)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # rebalance will succeed but deposit only up to limit
    withdrawn_amount, deposited_amount = teller.rebalance(
        bravo_token.address,  # deposit asset
        vault_id,  # deposit vault id
        alpha_token.address,  # withdraw asset
        vault_id,  # withdraw vault id
        bravo_amount,  # deposit amount
        alpha_amount,  # withdraw amount
        bob,  # user
        sender=bob
    )

    # verify event was emitted
    rebalance_logs = filter_logs(teller, "TellerRebalance")
    assert len(rebalance_logs) == 1

    # deposit should be capped at user limit
    assert deposited_amount == user_limit
    assert withdrawn_amount == alpha_amount
