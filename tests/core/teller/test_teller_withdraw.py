import boa

from constants import EIGHTEEN_DECIMALS, MAX_UINT256
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
    assert log.isDepleted

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
    with boa.reverts("not allowed to withdraw for user"):
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
    assert alpha_log.isDepleted

    # Verify bravo token withdrawal
    bravo_log = logs[1]
    assert bravo_log.user == bob
    assert bravo_log.asset == bravo_token.address
    assert bravo_log.caller == bob
    assert bravo_log.amount == deposit_amount
    assert bravo_log.vaultAddr == simple_erc20_vault.address
    assert bravo_log.vaultId == vault_id
    assert bravo_log.isDepleted

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
    switchboard_alpha,
    performDeposit,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # pause the teller
    teller.pause(True, sender=switchboard_alpha.address)
    assert teller.isPaused()

    # attempt withdrawal should fail
    with boa.reverts("contract paused"):
        teller.withdraw(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)

    # unpause the teller
    teller.pause(False, sender=switchboard_alpha.address)
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


#################################
# Debt-Related Withdrawal Tests #
#################################


def test_teller_withdraw_with_no_debt(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    teller,
    credit_engine,
):
    """Test that users with no debt can withdraw their full balance"""
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()

    # deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # verify user can withdraw full amount (no debt)
    max_withdrawable = credit_engine.getMaxWithdrawableForAsset(
        bob, 
        0,  # will be resolved by vault address
        alpha_token,
        simple_erc20_vault
    )
    assert max_withdrawable == MAX_UINT256  # max_value(uint256)

    # withdraw full amount should succeed
    amount = teller.withdraw(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)
    assert amount == deposit_amount
    assert alpha_token.balanceOf(bob) == deposit_amount


def test_teller_withdraw_with_debt_good_ltv(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    teller,
    credit_engine,
    mock_price_source,
    green_token,
    createDebtTerms,
    vault_book,
):
    """Test withdrawal limits when user has debt but maintains good LTV"""
    # basic setup with 50% LTV
    setGeneralConfig()
    debt_terms = createDebtTerms(_ltv=50_00)  # 50% LTV
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    # deposit and set price
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)  # $1 per token

    # borrow 25% of collateral value ($25 out of $100)
    borrow_amount = 25 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)
    assert green_token.balanceOf(bob) == borrow_amount

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # calculate max withdrawable
    # With single asset and debt, cannot withdraw any
    max_withdrawable = credit_engine.getMaxWithdrawableForAsset(
        bob,
        vault_id,
        alpha_token,
        simple_erc20_vault
    )

    # With $25 debt and 50% LTV, need to maintain $50.50 collateral (with 1% buffer)
    # Can withdraw $49.50 worth = 49.5 tokens
    assert max_withdrawable == 495 * EIGHTEEN_DECIMALS // 10  # 49.5 tokens

    # Can withdraw up to the max
    withdraw_amount = 49 * EIGHTEEN_DECIMALS
    before_balance = alpha_token.balanceOf(bob)
    teller.withdraw(alpha_token, withdraw_amount, bob, simple_erc20_vault, sender=bob)
    assert alpha_token.balanceOf(bob) == before_balance + withdraw_amount

    # After withdrawing 49 tokens, only ~51 tokens remain as collateral
    # Trying to withdraw another 10 would bring collateral below required
    # Should be capped at 0.5 tokens (the max withdrawable)
    before_balance_2 = alpha_token.balanceOf(bob)
    amount = teller.withdraw(alpha_token, 10 * EIGHTEEN_DECIMALS, bob, simple_erc20_vault, sender=bob)
    
    # With 51 tokens and $25 debt at 50% LTV, need $50.50 minimum
    # Can only withdraw 0.5 tokens
    assert amount == 5 * EIGHTEEN_DECIMALS // 10  # 0.5 tokens
    assert alpha_token.balanceOf(bob) == before_balance_2 + amount
    
    # Now at exactly minimum collateral, cannot withdraw any more
    with boa.reverts("cannot withdraw anything"):
        teller.withdraw(alpha_token, 1, bob, simple_erc20_vault, sender=bob)


def test_teller_withdraw_at_max_ltv(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    teller,
    credit_engine,
    mock_price_source,
    createDebtTerms,
    vault_book,
):
    """Test that users at max LTV cannot withdraw"""
    # basic setup with 50% LTV
    setGeneralConfig()
    debt_terms = createDebtTerms(_ltv=50_00)  # 50% LTV
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    # deposit and set price
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # borrow at max LTV (50% of $100 = $50)
    borrow_amount = 50 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # max withdrawable is 0 for single asset with debt
    max_withdrawable = credit_engine.getMaxWithdrawableForAsset(
        bob,
        vault_id,
        alpha_token,
        simple_erc20_vault
    )
    assert max_withdrawable == 0
    
    # attempt to withdraw should fail
    with boa.reverts("cannot withdraw anything"):
        teller.withdraw(alpha_token, 1 * EIGHTEEN_DECIMALS, bob, simple_erc20_vault, sender=bob)


def test_teller_withdraw_multiple_assets_with_debt(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    teller,
    credit_engine,
    mock_price_source,
    createDebtTerms,
    vault_book,
):
    """Test withdrawal calculation with multiple assets as collateral"""
    # basic setup
    setGeneralConfig()
    
    # Alpha: 50% LTV, Bravo: 75% LTV
    alpha_debt_terms = createDebtTerms(_ltv=50_00)
    bravo_debt_terms = createDebtTerms(_ltv=75_00)
    setAssetConfig(alpha_token, _debtTerms=alpha_debt_terms)
    setAssetConfig(bravo_token, _debtTerms=bravo_debt_terms)
    setGeneralDebtConfig()

    # deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    performDeposit(bob, deposit_amount, bravo_token, bravo_token_whale)

    # set prices: alpha=$1, bravo=$2
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)

    # Total collateral: $100 + $200 = $300
    # Total max debt: $50 + $150 = $200
    # Borrow $100
    borrow_amount = 100 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Test withdrawing alpha
    # Without alpha: $200 bravo collateral, $150 max debt from bravo
    # Need $100 debt * 100/74 (with buffer) = $135.14 collateral
    # Bravo provides $200, so no alpha needed - can withdraw all
    max_withdrawable_alpha = credit_engine.getMaxWithdrawableForAsset(
        bob,
        vault_id,
        alpha_token,
        simple_erc20_vault
    )
    assert max_withdrawable_alpha == MAX_UINT256  # Can withdraw all alpha

    # Test withdrawing bravo
    # Without bravo: $100 alpha collateral, $50 max debt capacity from alpha
    # Total debt needed (with 1% buffer): $100 * 101% = $101
    # Debt bravo must support: $101 - $50 = $51
    # Min bravo collateral needed: $51 / 75% = $68
    # Can withdraw: $200 - $68 = $132 worth of bravo = 66 tokens
    max_withdrawable_bravo = credit_engine.getMaxWithdrawableForAsset(
        bob,
        vault_id,
        bravo_token,
        simple_erc20_vault
    )
    assert max_withdrawable_bravo == 66 * EIGHTEEN_DECIMALS


def test_teller_withdraw_user_in_liquidation(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    teller,
    credit_engine,
    ledger,
    createDebtTerms,
):
    """Test that users in liquidation cannot withdraw"""
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()

    # deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # manually set user in liquidation
    debt_terms = createDebtTerms()
    user_debt = (50 * EIGHTEEN_DECIMALS, 50 * EIGHTEEN_DECIMALS, debt_terms, 0, True)  # inLiquidation=True
    ledger.setUserDebt(bob, user_debt, 0, (0, 0), sender=credit_engine.address)

    # max withdrawable should be 0
    max_withdrawable = credit_engine.getMaxWithdrawableForAsset(
        bob,
        0,
        alpha_token,
        simple_erc20_vault
    )
    assert max_withdrawable == 0

    # attempt to withdraw should fail
    with boa.reverts("cannot withdraw anything"):
        teller.withdraw(alpha_token, 1 * EIGHTEEN_DECIMALS, bob, simple_erc20_vault, sender=bob)


def test_teller_withdraw_asset_zero_ltv(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    teller,
    credit_engine,
    mock_price_source,
    createDebtTerms,
):
    """Test withdrawal of assets with 0% LTV (non-borrowable)"""
    # basic setup
    setGeneralConfig()
    
    # Alpha: 0% LTV (e.g., staked tokens), Bravo: 50% LTV
    alpha_debt_terms = createDebtTerms(_ltv=0)
    bravo_debt_terms = createDebtTerms(_ltv=50_00)
    setAssetConfig(alpha_token, _debtTerms=alpha_debt_terms)
    setAssetConfig(bravo_token, _debtTerms=bravo_debt_terms)
    setGeneralDebtConfig()

    # deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    performDeposit(bob, deposit_amount, bravo_token, bravo_token_whale)

    # set prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)

    # borrow against bravo only
    borrow_amount = 50 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    # should be able to withdraw all alpha (0% LTV asset)
    max_withdrawable_alpha = credit_engine.getMaxWithdrawableForAsset(
        bob,
        0,
        alpha_token,
        simple_erc20_vault
    )
    assert max_withdrawable_alpha == MAX_UINT256

    # withdraw all alpha
    amount = teller.withdraw(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)
    assert amount == deposit_amount


def test_teller_withdraw_asset_no_price(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    teller,
    credit_engine,
    mock_price_source,
    createDebtTerms,
    vault_book,
):
    """Test withdrawal when asset price is unavailable"""
    # basic setup
    setGeneralConfig()
    debt_terms = createDebtTerms(_ltv=50_00)
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    # deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    
    # set initial price for borrowing
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # borrow
    borrow_amount = 25 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # set price to 0 (unavailable)
    mock_price_source.setPrice(alpha_token, 0)

    # When asset has no price, getUsdValue returns 0, so max withdrawable is 0
    max_withdrawable = credit_engine.getMaxWithdrawableForAsset(
        bob,
        vault_id,
        alpha_token,
        simple_erc20_vault
    )
    assert max_withdrawable == 0
    
    # Cannot withdraw when price is unavailable
    with boa.reverts("cannot withdraw anything"):
        teller.withdraw(alpha_token, 1 * EIGHTEEN_DECIMALS, bob, simple_erc20_vault, sender=bob)


def test_teller_withdraw_after_partial_repay(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    teller,
    credit_engine,
    mock_price_source,
    green_token,
    createDebtTerms,
    vault_book,
):
    """Test that withdrawal limits update correctly after partial debt repayment"""
    # basic setup
    setGeneralConfig()
    debt_terms = createDebtTerms(_ltv=50_00)
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    # deposit and set price
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # borrow at max LTV
    borrow_amount = 50 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Single asset with debt returns 0
    max_withdrawable = credit_engine.getMaxWithdrawableForAsset(
        bob,
        vault_id,
        alpha_token,
        simple_erc20_vault
    )
    assert max_withdrawable == 0

    # repay half the debt
    repay_amount = 25 * EIGHTEEN_DECIMALS
    green_token.approve(teller, repay_amount, sender=bob)
    teller.repay(repay_amount, bob, False, True, sender=bob)

    # After repaying half, debt is $25 with 50% LTV, need $50.50 collateral
    # Can withdraw $49.50 worth = 49.5 tokens
    max_withdrawable = credit_engine.getMaxWithdrawableForAsset(
        bob,
        vault_id,
        alpha_token,
        simple_erc20_vault
    )
    assert max_withdrawable == 495 * EIGHTEEN_DECIMALS // 10  # 49.5 tokens
    
    # Can withdraw some amount
    withdraw_amount = 40 * EIGHTEEN_DECIMALS
    amount = teller.withdraw(alpha_token, withdraw_amount, bob, simple_erc20_vault, sender=bob)
    assert amount == withdraw_amount
    
    # Repay all debt
    green_token.approve(teller, 25 * EIGHTEEN_DECIMALS, sender=bob)
    teller.repay(25 * EIGHTEEN_DECIMALS, bob, False, True, sender=bob)
    
    # Now with no debt, can withdraw all remaining
    max_withdrawable = credit_engine.getMaxWithdrawableForAsset(
        bob,
        vault_id,
        alpha_token,
        simple_erc20_vault
    )
    assert max_withdrawable == MAX_UINT256


def test_teller_withdraw_single_asset_no_withdrawal_with_debt(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    teller,
    credit_engine,
    mock_price_source,
    createDebtTerms,
    vault_book,
):
    """Test that users with single collateral asset can withdraw when well under LTV"""
    # basic setup
    setGeneralConfig()
    debt_terms = createDebtTerms(_ltv=80_00)  # High LTV 80%
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    # deposit and set price
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # borrow small amount
    borrow_amount = 10 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # With $10 debt and 80% LTV, need $10 * 101% / 80% = $12.625 collateral
    # Can withdraw $100 - $12.625 = $87.375
    max_withdrawable = credit_engine.getMaxWithdrawableForAsset(
        bob,
        vault_id,
        alpha_token,
        simple_erc20_vault
    )
    expected_withdrawable = 87375 * EIGHTEEN_DECIMALS // 1000  # 87.375 tokens
    assert max_withdrawable == expected_withdrawable

    # Can withdraw up to the max
    withdraw_amount = 87 * EIGHTEEN_DECIMALS
    amount = teller.withdraw(alpha_token, withdraw_amount, bob, simple_erc20_vault, sender=bob)
    assert amount == withdraw_amount


def test_teller_withdraw_min_balance_below_minimum(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    performDeposit,
):
    """Test that withdrawals fail when they would leave a balance below minDepositBalance"""
    # Setup with minDepositBalance = 50 tokens
    min_balance = 50 * EIGHTEEN_DECIMALS
    setGeneralConfig()
    setAssetConfig(alpha_token, _minDepositBalance=min_balance)

    # Deposit 100 tokens
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # Try to withdraw 75 tokens, leaving 25 (below minimum of 50) - should fail
    withdraw_amount = 75 * EIGHTEEN_DECIMALS
    with boa.reverts("too small a balance"):
        teller.withdraw(alpha_token, withdraw_amount, bob, simple_erc20_vault, sender=bob)

    # Verify no tokens were withdrawn
    assert alpha_token.balanceOf(bob) == 0
    assert alpha_token.balanceOf(simple_erc20_vault) == deposit_amount


def test_teller_withdraw_min_balance_exactly_minimum(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    performDeposit,
):
    """Test that withdrawals succeed when they leave exactly the minDepositBalance"""
    # Setup with minDepositBalance = 50 tokens
    min_balance = 50 * EIGHTEEN_DECIMALS
    setGeneralConfig()
    setAssetConfig(alpha_token, _minDepositBalance=min_balance)

    # Deposit 100 tokens
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # Withdraw 50 tokens, leaving exactly 50 (meets minimum) - should succeed
    withdraw_amount = 50 * EIGHTEEN_DECIMALS
    amount = teller.withdraw(alpha_token, withdraw_amount, bob, simple_erc20_vault, sender=bob)
    assert amount == withdraw_amount

    # Verify correct amounts were withdrawn
    assert alpha_token.balanceOf(bob) == withdraw_amount
    assert alpha_token.balanceOf(simple_erc20_vault) == min_balance


def test_teller_withdraw_min_balance_above_minimum(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    performDeposit,
):
    """Test that withdrawals succeed when they leave a balance above minDepositBalance"""
    # Setup with minDepositBalance = 50 tokens
    min_balance = 50 * EIGHTEEN_DECIMALS
    setGeneralConfig()
    setAssetConfig(alpha_token, _minDepositBalance=min_balance)

    # Deposit 150 tokens
    deposit_amount = 150 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # Withdraw 75 tokens, leaving 75 (above minimum of 50) - should succeed
    withdraw_amount = 75 * EIGHTEEN_DECIMALS
    amount = teller.withdraw(alpha_token, withdraw_amount, bob, simple_erc20_vault, sender=bob)
    assert amount == withdraw_amount

    # Verify correct amounts were withdrawn
    assert alpha_token.balanceOf(bob) == withdraw_amount
    assert alpha_token.balanceOf(simple_erc20_vault) == deposit_amount - withdraw_amount


def test_teller_withdraw_min_balance_full_withdrawal_allowed(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    performDeposit,
):
    """Test that full withdrawal (depletion) is allowed regardless of minDepositBalance"""
    # Setup with minDepositBalance = 50 tokens
    min_balance = 50 * EIGHTEEN_DECIMALS
    setGeneralConfig()
    setAssetConfig(alpha_token, _minDepositBalance=min_balance)

    # Deposit 100 tokens
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # Withdraw all tokens - should succeed even though it goes below minimum
    amount = teller.withdraw(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)
    assert amount == deposit_amount

    # Verify all tokens were withdrawn (position is depleted)
    assert alpha_token.balanceOf(bob) == deposit_amount
    assert alpha_token.balanceOf(simple_erc20_vault) == 0

    # Verify the log shows isDepleted = True
    logs = filter_logs(teller, "TellerWithdrawal")
    assert len(logs) == 1
    assert logs[0].isDepleted == True


def test_teller_withdraw_min_balance_zero_allows_any_withdrawal(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    performDeposit,
):
    """Test that minDepositBalance = 0 allows any withdrawal amount"""
    # Setup with minDepositBalance = 0 (default)
    setGeneralConfig()
    setAssetConfig(alpha_token, _minDepositBalance=0)

    # Deposit 100 tokens
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # Withdraw leaving only 1 wei - should succeed with no minimum balance
    withdraw_amount = deposit_amount - 1
    amount = teller.withdraw(alpha_token, withdraw_amount, bob, simple_erc20_vault, sender=bob)
    assert amount == withdraw_amount

    # Verify correct amounts
    assert alpha_token.balanceOf(bob) == withdraw_amount
    assert alpha_token.balanceOf(simple_erc20_vault) == 1


def test_teller_withdraw_min_balance_partial_then_blocked(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    teller,
    performDeposit,
):
    """Test partial withdrawal that brings balance to minimum, then further withdrawal is blocked"""
    # Setup with minDepositBalance = 30 tokens
    min_balance = 30 * EIGHTEEN_DECIMALS
    setGeneralConfig()
    setAssetConfig(alpha_token, _minDepositBalance=min_balance)

    # Deposit 100 tokens
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # First withdrawal: 70 tokens, leaving 30 (exactly minimum) - should succeed
    first_withdraw = 70 * EIGHTEEN_DECIMALS
    amount1 = teller.withdraw(alpha_token, first_withdraw, bob, simple_erc20_vault, sender=bob)
    assert amount1 == first_withdraw
    assert alpha_token.balanceOf(simple_erc20_vault) == min_balance

    # Second withdrawal: any amount would go below minimum - should fail
    with boa.reverts("too small a balance"):
        teller.withdraw(alpha_token, 1, bob, simple_erc20_vault, sender=bob)

    # Full withdrawal should still be allowed (depletion)
    amount2 = teller.withdraw(alpha_token, min_balance, bob, simple_erc20_vault, sender=bob)
    assert amount2 == min_balance
    assert alpha_token.balanceOf(simple_erc20_vault) == 0


def test_teller_withdraw_small_debt_buffer_precision(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    teller,
    credit_engine,
    mock_price_source,
    createDebtTerms,
    vault_book,
):
    """Test that 1% buffer works correctly even with small debt amounts"""
    setGeneralConfig()

    # Alpha: 50% LTV, Bravo: 80% LTV
    alpha_debt_terms = createDebtTerms(_ltv=50_00)
    bravo_debt_terms = createDebtTerms(_ltv=80_00)
    setAssetConfig(alpha_token, _debtTerms=alpha_debt_terms)
    setAssetConfig(bravo_token, _debtTerms=bravo_debt_terms)
    setGeneralDebtConfig()

    # Deposits: Small amounts to create small debt
    deposit_amount_alpha = 10 * EIGHTEEN_DECIMALS
    deposit_amount_bravo = 20 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount_alpha, alpha_token, alpha_token_whale)
    performDeposit(bob, deposit_amount_bravo, bravo_token, bravo_token_whale)

    # Prices: alpha=$1, bravo=$1
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)

    # Borrow tiny amount: $10
    borrow_amount = 10 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Test withdrawing bravo with small debt
    # Without bravo: $10 alpha, $5 capacity
    # Need: $10 * 1.01 = $10.1 (buffer should apply even for small amounts)
    # Bravo must cover: $10.1 - $5 = $5.1
    # Min bravo needed: $5.1 / 80% = $6.375
    # Can withdraw: $20 - $6.375 = $13.625
    max_withdrawable_bravo = credit_engine.getMaxWithdrawableForAsset(
        bob,
        vault_id,
        bravo_token,
        simple_erc20_vault
    )

    # Expected: 13.625 tokens (since price is $1)
    # Due to integer division: 10 * 10100 // 10000 = 1010000 // 10000 = 101 (works!)
    # 101 - 5 = 96 (in wei: $0.96)
    # Need more precision - let me calculate in wei properly
    # debtNeeded = 10e18 * 10100 // 10000 = 10.1e18
    # gap = 10.1e18 - 5e18 = 5.1e18
    # minBravo = 5.1e18 * 10000 // 8000 = 6.375e18
    # canWithdraw = 20e18 - 6.375e18 = 13.625e18
    expected = 13625 * EIGHTEEN_DECIMALS // 1000  # 13.625 tokens
    assert max_withdrawable_bravo == expected


def test_teller_withdraw_three_assets_different_ltvs(
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
    performDeposit,
    teller,
    credit_engine,
    mock_price_source,
    createDebtTerms,
    vault_book,
):
    """Test withdrawal calculation with three assets having different LTVs"""
    setGeneralConfig()

    # Three assets: Alpha 40%, Bravo 60%, Charlie 80%
    alpha_debt_terms = createDebtTerms(_ltv=40_00)
    bravo_debt_terms = createDebtTerms(_ltv=60_00)
    charlie_debt_terms = createDebtTerms(_ltv=80_00)
    setAssetConfig(alpha_token, _debtTerms=alpha_debt_terms)
    setAssetConfig(bravo_token, _debtTerms=bravo_debt_terms)
    setAssetConfig(charlie_token, _debtTerms=charlie_debt_terms)
    setGeneralDebtConfig()

    # Deposits: $100 each (use proper decimals for each token)
    deposit_alpha = 100 * (10 ** alpha_token.decimals())
    deposit_bravo = 100 * (10 ** bravo_token.decimals())
    deposit_charlie = 100 * (10 ** charlie_token.decimals())
    performDeposit(bob, deposit_alpha, alpha_token, alpha_token_whale)
    performDeposit(bob, deposit_bravo, bravo_token, bravo_token_whale)
    performDeposit(bob, deposit_charlie, charlie_token, charlie_token_whale)

    # Prices: all $1 (adjust for decimals)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, 1 * EIGHTEEN_DECIMALS)

    # Total: $300 collateral
    # Max debt: $40 + $60 + $80 = $180
    # Borrow $150
    borrow_amount = 150 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Test 1: Withdraw Charlie (highest LTV)
    # Without charlie: $200 collateral, $100 capacity (40+60)
    # Need: $150 * 1.01 = $151.5
    # Charlie must cover: $151.5 - $100 = $51.5
    # Min charlie: $51.5 / 80% = $64.375
    # Can withdraw: $100 - $64.375 = $35.625
    max_withdrawable_charlie = credit_engine.getMaxWithdrawableForAsset(
        bob,
        vault_id,
        charlie_token,
        simple_erc20_vault
    )
    # Charlie has 6 decimals, so convert: 35.625 * 1e6
    expected_charlie = 35625000  # 35.625 tokens with 6 decimals
    assert max_withdrawable_charlie == expected_charlie

    # Test 2: Withdraw Alpha (lowest LTV)
    # Without alpha: $200 collateral, $140 capacity (60+80)
    # Need: $151.5
    # $140 < $151.5, so alpha must cover gap
    # Alpha must cover: $151.5 - $140 = $11.5
    # Min alpha: $11.5 / 40% = $28.75
    # Can withdraw: $100 - $28.75 = $71.25
    max_withdrawable_alpha = credit_engine.getMaxWithdrawableForAsset(
        bob,
        vault_id,
        alpha_token,
        simple_erc20_vault
    )
    expected_alpha = 7125 * EIGHTEEN_DECIMALS // 100  # 71.25 tokens
    assert max_withdrawable_alpha == expected_alpha

    # Test 3: Withdraw Bravo (middle LTV)
    # Without bravo: $200 collateral, $120 capacity (40+80)
    # Bravo must cover: $151.5 - $120 = $31.5
    # Min bravo: $31.5 / 60% = $52.5
    # Can withdraw: $100 - $52.5 = $47.5
    max_withdrawable_bravo = credit_engine.getMaxWithdrawableForAsset(
        bob,
        vault_id,
        bravo_token,
        simple_erc20_vault
    )
    expected_bravo = 475 * EIGHTEEN_DECIMALS // 10  # 47.5 tokens
    assert max_withdrawable_bravo == expected_bravo


def test_teller_withdraw_high_ltv_asset(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    teller,
    credit_engine,
    mock_price_source,
    createDebtTerms,
    vault_book,
):
    """Test calculation with very high LTV asset (90%)"""
    setGeneralConfig()

    # Alpha: 30% LTV (safe), Bravo: 90% LTV (risky)
    alpha_debt_terms = createDebtTerms(_ltv=30_00)
    bravo_debt_terms = createDebtTerms(_ltv=90_00)
    setAssetConfig(alpha_token, _debtTerms=alpha_debt_terms)
    setAssetConfig(bravo_token, _debtTerms=bravo_debt_terms)
    setGeneralDebtConfig()

    # Deposits
    deposit_alpha = 100 * EIGHTEEN_DECIMALS
    deposit_bravo = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_alpha, alpha_token, alpha_token_whale)
    performDeposit(bob, deposit_bravo, bravo_token, bravo_token_whale)

    # Prices: both $1
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)

    # Borrow $100
    # Max capacity: $30 + $90 = $120
    borrow_amount = 100 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Withdraw the high-LTV asset (bravo)
    # Without bravo: $100 alpha, $30 capacity
    # Need: $100 * 1.01 = $101
    # Bravo must cover: $101 - $30 = $71
    # Min bravo: $71 / 90% = $78.888...
    # Can withdraw: $100 - $78.889 = $21.111
    max_withdrawable_bravo = credit_engine.getMaxWithdrawableForAsset(
        bob,
        vault_id,
        bravo_token,
        simple_erc20_vault
    )

    # Calculation in wei:
    # gap = 101e18 - 30e18 = 71e18
    # minBravo = 71e18 * 10000 // 9000 = 78.888...e18 (rounds down in division)
    # 71e18 * 10000 = 710000e18
    # 710000e18 // 9000 = 78888888888888888888 (78.888... tokens)
    # withdraw = 100e18 - 78888888888888888888 = 21111111111111111112
    expected = 21111111111111111112  # ~21.111 tokens
    assert max_withdrawable_bravo == expected

    # Verify can actually withdraw this amount
    teller.withdraw(bravo_token, expected, bob, simple_erc20_vault, sender=bob)


def test_teller_withdraw_exact_capacity_edge_case(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    teller,
    credit_engine,
    mock_price_source,
    createDebtTerms,
    vault_book,
):
    """Test edge case where remaining capacity exactly equals debt needed"""
    setGeneralConfig()

    # Alpha: 75% LTV, Bravo: 50% LTV
    alpha_debt_terms = createDebtTerms(_ltv=75_00)
    bravo_debt_terms = createDebtTerms(_ltv=50_00)
    setAssetConfig(alpha_token, _debtTerms=alpha_debt_terms)
    setAssetConfig(bravo_token, _debtTerms=bravo_debt_terms)
    setGeneralDebtConfig()

    # Carefully chosen deposits to create exact capacity scenario
    # Want: debt * 1.01 == remaining capacity
    # If debt = $100, need remaining capacity = $101
    # Bravo with 50% LTV needs $202 collateral for $101 capacity
    deposit_alpha = 100 * EIGHTEEN_DECIMALS
    deposit_bravo = 202 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_alpha, alpha_token, alpha_token_whale)
    performDeposit(bob, deposit_bravo, bravo_token, bravo_token_whale)

    # Prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)

    # Borrow exactly $100
    borrow_amount = 100 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Try to withdraw Alpha
    # Without alpha: $202 bravo, $101 capacity
    # Need: $100 * 1.01 = $101
    # Exactly equal! Should be able to withdraw ALL alpha
    max_withdrawable_alpha = credit_engine.getMaxWithdrawableForAsset(
        bob,
        vault_id,
        alpha_token,
        simple_erc20_vault
    )

    # Should return max_value(uint256) when remaining can support all debt
    assert max_withdrawable_alpha == MAX_UINT256

    # Verify can actually withdraw all
    teller.withdraw(alpha_token, deposit_alpha, bob, simple_erc20_vault, sender=bob)


def test_teller_withdraw_order_dependency(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    alice,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    teller,
    credit_engine,
    mock_price_source,
    createDebtTerms,
    vault_book,
):
    """Test that withdrawal order affects how much can be withdrawn"""
    setGeneralConfig()

    # Alpha: 30% LTV, Bravo: 60% LTV, Charlie: 90% LTV
    alpha_debt_terms = createDebtTerms(_ltv=30_00)
    bravo_debt_terms = createDebtTerms(_ltv=60_00)
    charlie_debt_terms = createDebtTerms(_ltv=90_00)
    setAssetConfig(alpha_token, _debtTerms=alpha_debt_terms)
    setAssetConfig(bravo_token, _debtTerms=bravo_debt_terms)
    setAssetConfig(charlie_token, _debtTerms=charlie_debt_terms)
    setGeneralDebtConfig()

    # Set up two users with identical positions (use proper decimals)
    deposit_alpha = 100 * (10 ** alpha_token.decimals())
    deposit_bravo = 100 * (10 ** bravo_token.decimals())
    deposit_charlie = 100 * (10 ** charlie_token.decimals())

    # Bob's deposits
    performDeposit(bob, deposit_alpha, alpha_token, alpha_token_whale)
    performDeposit(bob, deposit_bravo, bravo_token, bravo_token_whale)
    performDeposit(bob, deposit_charlie, charlie_token, charlie_token_whale)

    # Alice's deposits
    performDeposit(alice, deposit_alpha, alpha_token, alpha_token_whale)
    performDeposit(alice, deposit_bravo, bravo_token, bravo_token_whale)
    performDeposit(alice, deposit_charlie, charlie_token, charlie_token_whale)

    # Prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, 1 * EIGHTEEN_DECIMALS)

    # Both borrow $100
    borrow_amount = 100 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)
    teller.borrow(borrow_amount, alice, False, sender=alice)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Strategy 1 (Bob): Withdraw low-LTV first, then check high-LTV
    # First check: how much charlie can bob withdraw initially?
    max_charlie_initial = credit_engine.getMaxWithdrawableForAsset(
        bob,
        vault_id,
        charlie_token,
        simple_erc20_vault
    )

    # Now Bob withdraws alpha (low LTV) first
    max_alpha_bob = credit_engine.getMaxWithdrawableForAsset(
        bob,
        vault_id,
        alpha_token,
        simple_erc20_vault
    )
    # Should be able to withdraw most/all alpha since bravo+charlie provide good capacity
    teller.withdraw(alpha_token, max_alpha_bob, bob, simple_erc20_vault, sender=bob)

    # Now check charlie again for Bob (after withdrawing alpha)
    max_charlie_after_alpha = credit_engine.getMaxWithdrawableForAsset(
        bob,
        vault_id,
        charlie_token,
        simple_erc20_vault
    )

    # Strategy 2 (Alice): Check charlie without withdrawing anything
    max_charlie_alice = credit_engine.getMaxWithdrawableForAsset(
        alice,
        vault_id,
        charlie_token,
        simple_erc20_vault
    )

    # Bob's max charlie (after withdrawing alpha) should be LESS than Alice's max charlie
    # Because Bob lost the low-LTV alpha capacity
    # Alice still has alpha+bravo remaining if she withdraws charlie
    # Bob only has bravo remaining if he withdraws charlie
    assert max_charlie_after_alpha < max_charlie_alice

    # Initial check should equal Alice's current check (both have all assets)
    assert max_charlie_initial == max_charlie_alice


def test_teller_withdraw_remaining_capacity_exceeds_debt(
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    teller,
    credit_engine,
    mock_price_source,
    createDebtTerms,
    vault_book,
):
    """Test when one asset alone can support all debt (other asset fully withdrawable)"""
    setGeneralConfig()

    # Alpha: 40% LTV, Bravo: 80% LTV
    alpha_debt_terms = createDebtTerms(_ltv=40_00)
    bravo_debt_terms = createDebtTerms(_ltv=80_00)
    setAssetConfig(alpha_token, _debtTerms=alpha_debt_terms)
    setAssetConfig(bravo_token, _debtTerms=bravo_debt_terms)
    setGeneralDebtConfig()

    # Large deposits, small debt
    deposit_alpha = 50 * EIGHTEEN_DECIMALS
    deposit_bravo = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_alpha, alpha_token, alpha_token_whale)
    performDeposit(bob, deposit_bravo, bravo_token, bravo_token_whale)

    # Prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)

    # Small debt: $50
    # Bravo alone provides: $200 * 80% = $160 capacity >> $50 debt
    borrow_amount = 50 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Try to withdraw Alpha
    # Without alpha: $200 bravo, $160 capacity
    # Need: $50 * 1.01 = $50.5
    # $160 > $50.5, so can withdraw ALL alpha
    max_withdrawable_alpha = credit_engine.getMaxWithdrawableForAsset(
        bob,
        vault_id,
        alpha_token,
        simple_erc20_vault
    )

    assert max_withdrawable_alpha == MAX_UINT256

    # Verify can withdraw all
    teller.withdraw(alpha_token, deposit_alpha, bob, simple_erc20_vault, sender=bob)
