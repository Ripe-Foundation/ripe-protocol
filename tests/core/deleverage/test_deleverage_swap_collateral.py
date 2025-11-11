import boa
import pytest
from constants import EIGHTEEN_DECIMALS, MAX_UINT256
from conf_utils import filter_logs


@pytest.fixture
def setupSwapScenario(
    setAssetConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
):
    """
    Helper fixture to setup swap scenario with user collateral and governance tokens.

    Returns a function that:
    - Configures both withdraw and deposit assets with specified LTVs
    - Sets prices for both assets
    - Deposits withdraw_token collateral for user
    - Funds governance with deposit_token
    - Returns (collateral_amount, governance_deposit_amount) for verification
    """
    def _setup(
        user,
        withdraw_token,
        deposit_token,
        withdraw_whale,
        deposit_whale,
        governance,
        deleverage,
        withdraw_vault,
        deposit_vault=None,
        collateral_amount=1000 * EIGHTEEN_DECIMALS,
        governance_deposit_amount=1000 * EIGHTEEN_DECIMALS,
        withdraw_ltv=50_00,
        deposit_ltv=75_00,
        withdraw_price=1 * EIGHTEEN_DECIMALS,
        deposit_price=1 * EIGHTEEN_DECIMALS,
    ):
        # Default to same vault if not specified
        if deposit_vault is None:
            deposit_vault = withdraw_vault

        # Configure assets with LTVs
        withdraw_terms = createDebtTerms(
            _ltv=withdraw_ltv,
            _redemptionThreshold=60_00,
            _liqThreshold=70_00,
            _liqFee=10_00,
            _borrowRate=5_00,
        )
        deposit_terms = createDebtTerms(
            _ltv=deposit_ltv,
            _redemptionThreshold=60_00,
            _liqThreshold=70_00,
            _liqFee=10_00,
            _borrowRate=5_00,
        )

        setAssetConfig(
            withdraw_token,
            _debtTerms=withdraw_terms,
            _shouldBurnAsPayment=False,
            _shouldTransferToEndaoment=False,
        )
        setAssetConfig(
            deposit_token,
            _debtTerms=deposit_terms,
            _shouldBurnAsPayment=False,
            _shouldTransferToEndaoment=False,
        )

        # Set prices
        mock_price_source.setPrice(withdraw_token, withdraw_price)
        mock_price_source.setPrice(deposit_token, deposit_price)

        # Setup user collateral
        performDeposit(user, collateral_amount, withdraw_token, withdraw_whale, withdraw_vault)

        # Setup governance tokens
        deposit_token.transfer(governance, governance_deposit_amount, sender=deposit_whale)
        deposit_token.approve(deleverage.address, governance_deposit_amount, sender=governance.address)

        return collateral_amount, governance_deposit_amount

    return _setup


@pytest.fixture(autouse=True)
def setup(
    setGeneralConfig,
    setGeneralDebtConfig,
):
    setGeneralConfig()
    setGeneralDebtConfig()


###################
# Basic Swap Tests
###################


def test_swap_collateral_basic_same_vault(
    deleverage,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    simple_erc20_vault,
    vault_book,
    setupSwapScenario,
    price_desk,
    _test,
):
    """Test basic swap from alpha to bravo in same vault with equal USD value"""
    # Setup: bob has 1000 alpha, governance has 1000 bravo
    collateral_amount, gov_deposit_amount = setupSwapScenario(
        user=bob,
        withdraw_token=alpha_token,
        deposit_token=bravo_token,
        withdraw_whale=alpha_token_whale,
        deposit_whale=bravo_token_whale,
        governance=governance,
        deleverage=deleverage,
        withdraw_vault=simple_erc20_vault,
        withdraw_ltv=50_00,
        deposit_ltv=75_00,  # Higher LTV is better for user
    )

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Record initial balances
    initial_bob_alpha_vault = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    initial_bob_bravo_vault = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    initial_gov_alpha = alpha_token.balanceOf(governance)
    initial_gov_bravo = bravo_token.balanceOf(governance)

    # Execute swap: withdraw all alpha, deposit equivalent bravo
    withdrawn, deposited = deleverage.swapCollateral(
        bob,  # _user
        vault_id,  # _withdrawVaultId
        alpha_token.address,  # _withdrawAsset
        vault_id,  # _depositVaultId
        bravo_token.address,  # _depositAsset
        MAX_UINT256,  # _withdrawAmount (max = withdraw all)
        sender=governance.address
    )

    # Verify return values
    assert withdrawn == collateral_amount, "Should withdraw entire collateral"
    # USD value should be preserved (±50 bps tolerance)
    _test(deposited, collateral_amount, _buffer=50)

    # Verify bob's vault balances
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0, "Bob should have no alpha left"
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == deposited, "Bob should have bravo deposited"

    # Verify governance balances
    assert alpha_token.balanceOf(governance) == initial_gov_alpha + withdrawn, "Gov should receive withdrawn alpha"
    _test(bravo_token.balanceOf(governance), initial_gov_bravo - deposited, _buffer=50)

    # Verify event
    logs = filter_logs(deleverage, "CollateralSwapped")
    assert len(logs) == 1
    log = logs[0]
    assert log.user == bob
    assert log.caller == governance.address
    assert log.withdrawVaultId == vault_id
    assert log.withdrawAsset == alpha_token.address
    assert log.withdrawAmount == withdrawn
    assert log.depositVaultId == vault_id
    assert log.depositAsset == bravo_token.address
    assert log.depositAmount == deposited
    # Verify USD value matches the withdrawn amount's value
    expected_usd = price_desk.getUsdValue(alpha_token, withdrawn, True)
    _test(log.usdValue, expected_usd, _buffer=50)


def test_swap_collateral_different_vaults(
    deleverage,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    simple_erc20_vault,
    rebase_erc20_vault,
    vault_book,
    setupSwapScenario,
    setAssetConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
):
    """Test swapping assets across different vaults"""
    # Setup alpha in simple_erc20_vault
    withdraw_terms = createDebtTerms(_ltv=50_00)
    setAssetConfig(alpha_token, _vaultIds=[3], _debtTerms=withdraw_terms)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    collateral_amount = 1000 * EIGHTEEN_DECIMALS
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale, simple_erc20_vault)

    # Setup bravo in rebase_erc20_vault
    deposit_terms = createDebtTerms(_ltv=75_00)
    setAssetConfig(bravo_token, _vaultIds=[4], _debtTerms=deposit_terms)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)

    bravo_token.transfer(governance, collateral_amount, sender=bravo_token_whale)
    bravo_token.approve(deleverage.address, collateral_amount, sender=governance.address)

    withdraw_vault_id = vault_book.getRegId(simple_erc20_vault)
    deposit_vault_id = vault_book.getRegId(rebase_erc20_vault)

    # Execute cross-vault swap
    withdrawn, deposited = deleverage.swapCollateral(
        bob,
        withdraw_vault_id,  # Vault 3 (simple_erc20_vault)
        alpha_token.address,
        deposit_vault_id,  # Vault 4 (rebase_erc20_vault)
        bravo_token.address,
        MAX_UINT256,
        sender=governance.address
    )

    # Verify balances in different vaults
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0
    assert rebase_erc20_vault.getTotalAmountForUser(bob, bravo_token) == deposited

    # Verify event shows different vault IDs
    logs = filter_logs(deleverage, "CollateralSwapped")
    assert len(logs) == 1
    assert logs[0].withdrawVaultId == withdraw_vault_id
    assert logs[0].depositVaultId == deposit_vault_id


def test_swap_collateral_max_value_withdraws_all(
    deleverage,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    simple_erc20_vault,
    vault_book,
    setupSwapScenario,
):
    """Test that max_value(uint256) withdraws entire collateral position"""
    collateral_amount = 500 * EIGHTEEN_DECIMALS
    setupSwapScenario(
        user=bob,
        withdraw_token=alpha_token,
        deposit_token=bravo_token,
        withdraw_whale=alpha_token_whale,
        deposit_whale=bravo_token_whale,
        governance=governance,
        deleverage=deleverage,
        withdraw_vault=simple_erc20_vault,
        collateral_amount=collateral_amount,
        governance_deposit_amount=collateral_amount,
    )

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Verify bob has collateral before swap
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == collateral_amount

    # Swap with MAX_UINT256 (default parameter)
    withdrawn, deposited = deleverage.swapCollateral(
        bob,
        vault_id,
        alpha_token.address,
        vault_id,
        bravo_token.address,
        # _withdrawAmount defaults to MAX_UINT256
        sender=governance.address
    )

    # Should withdraw entire balance
    assert withdrawn == collateral_amount
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0


def test_swap_collateral_partial_amount(
    deleverage,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    simple_erc20_vault,
    vault_book,
    setupSwapScenario,
    _test,
):
    """Test swapping partial amount, leaving some original collateral"""
    total_collateral = 1000 * EIGHTEEN_DECIMALS
    setupSwapScenario(
        user=bob,
        withdraw_token=alpha_token,
        deposit_token=bravo_token,
        withdraw_whale=alpha_token_whale,
        deposit_whale=bravo_token_whale,
        governance=governance,
        deleverage=deleverage,
        withdraw_vault=simple_erc20_vault,
        collateral_amount=total_collateral,
        governance_deposit_amount=total_collateral,
    )

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Swap only half
    partial_amount = 500 * EIGHTEEN_DECIMALS
    withdrawn, deposited = deleverage.swapCollateral(
        bob,
        vault_id,
        alpha_token.address,
        vault_id,
        bravo_token.address,
        partial_amount,  # Specific amount, not max
        sender=governance.address
    )

    # Verify partial withdrawal
    assert withdrawn == partial_amount

    # Bob should still have 500 alpha left
    remaining_alpha = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    assert remaining_alpha == 500 * EIGHTEEN_DECIMALS

    # Bob should have deposited bravo
    bravo_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    _test(bravo_balance, partial_amount, _buffer=50)


############################
# LTV & Health Factor Tests
############################


def test_swap_to_higher_ltv_improves_health(
    deleverage,
    teller,
    credit_engine,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    simple_erc20_vault,
    vault_book,
    setupSwapScenario,
):
    """Test swapping from 50% LTV to 75% LTV improves borrowing capacity"""
    collateral_amount = 1000 * EIGHTEEN_DECIMALS
    setupSwapScenario(
        user=bob,
        withdraw_token=alpha_token,
        deposit_token=bravo_token,
        withdraw_whale=alpha_token_whale,
        deposit_whale=bravo_token_whale,
        governance=governance,
        deleverage=deleverage,
        withdraw_vault=simple_erc20_vault,
        collateral_amount=collateral_amount,
        governance_deposit_amount=collateral_amount,
        withdraw_ltv=50_00,  # 50% LTV
        deposit_ltv=75_00,   # 75% LTV (better)
    )

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Get initial borrowing terms
    initial_terms = credit_engine.getUserBorrowTerms(bob, False)
    initial_max_debt = initial_terms.totalMaxDebt

    # Execute swap
    deleverage.swapCollateral(
        bob,
        vault_id,
        alpha_token.address,
        vault_id,
        bravo_token.address,
        MAX_UINT256,
        sender=governance.address
    )

    # Get new borrowing terms
    new_terms = credit_engine.getUserBorrowTerms(bob, False)
    new_max_debt = new_terms.totalMaxDebt

    # Max debt should increase (75% of collateral value > 50% of collateral value)
    assert new_max_debt > initial_max_debt, "Higher LTV should increase max debt"

    # Specifically: should increase by 50% (from 50% to 75%)
    expected_increase_ratio = 75_00 / 50_00  # 1.5x
    assert new_max_debt >= initial_max_debt * 1.4, "Should see significant increase in borrowing capacity"


def test_swap_to_equal_ltv_maintains_health(
    deleverage,
    credit_engine,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    simple_erc20_vault,
    vault_book,
    setupSwapScenario,
):
    """Test swapping to equal LTV maintains same health"""
    setupSwapScenario(
        user=bob,
        withdraw_token=alpha_token,
        deposit_token=bravo_token,
        withdraw_whale=alpha_token_whale,
        deposit_whale=bravo_token_whale,
        governance=governance,
        deleverage=deleverage,
        withdraw_vault=simple_erc20_vault,
        withdraw_ltv=60_00,  # Same LTV
        deposit_ltv=60_00,   # Same LTV
    )

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Get initial borrowing capacity
    initial_terms = credit_engine.getUserBorrowTerms(bob, False)
    initial_max_debt = initial_terms.totalMaxDebt

    # Execute swap
    deleverage.swapCollateral(
        bob,
        vault_id,
        alpha_token.address,
        vault_id,
        bravo_token.address,
        MAX_UINT256,
        sender=governance.address
    )

    # Get new borrowing capacity
    new_terms = credit_engine.getUserBorrowTerms(bob, False)
    new_max_debt = new_terms.totalMaxDebt

    # Should be approximately equal (allow small rounding differences)
    assert abs(new_max_debt - initial_max_debt) < 100, "Equal LTV should maintain similar borrowing capacity"


def test_swap_to_lower_ltv_fails(
    deleverage,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    simple_erc20_vault,
    vault_book,
    setupSwapScenario,
):
    """Test that swapping to asset with lower LTV fails"""
    setupSwapScenario(
        user=bob,
        withdraw_token=alpha_token,
        deposit_token=bravo_token,
        withdraw_whale=alpha_token_whale,
        deposit_whale=bravo_token_whale,
        governance=governance,
        deleverage=deleverage,
        withdraw_vault=simple_erc20_vault,
        withdraw_ltv=75_00,  # Higher LTV
        deposit_ltv=50_00,   # Lower LTV - should fail!
    )

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Should revert due to LTV check
    with boa.reverts("deposit asset LTV too low"):
        deleverage.swapCollateral(
            bob,
            vault_id,
            alpha_token.address,
            vault_id,
            bravo_token.address,
            MAX_UINT256,
            sender=governance.address
        )


def test_swap_with_debt_maintains_health(
    deleverage,
    teller,
    credit_engine,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    simple_erc20_vault,
    vault_book,
    setupSwapScenario,
    _test,
):
    """Test swapping while user has debt, health remains good"""
    collateral_amount = 1000 * EIGHTEEN_DECIMALS
    setupSwapScenario(
        user=bob,
        withdraw_token=alpha_token,
        deposit_token=bravo_token,
        withdraw_whale=alpha_token_whale,
        deposit_whale=bravo_token_whale,
        governance=governance,
        deleverage=deleverage,
        withdraw_vault=simple_erc20_vault,
        collateral_amount=collateral_amount,
        governance_deposit_amount=collateral_amount,
        withdraw_ltv=50_00,
        deposit_ltv=75_00,
    )

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Borrow some amount (25% of max capacity)
    max_debt = credit_engine.getUserBorrowTerms(bob, False).totalMaxDebt
    borrow_amount = max_debt // 4
    teller.borrow(borrow_amount, bob, False, sender=bob)

    # Verify bob has debt
    user_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0]
    assert user_debt.amount > 0

    # Execute swap (should succeed because new LTV is higher)
    withdrawn, deposited = deleverage.swapCollateral(
        bob,
        vault_id,
        alpha_token.address,
        vault_id,
        bravo_token.address,
        MAX_UINT256,
        sender=governance.address
    )

    # Verify swap succeeded with exact amounts
    assert withdrawn == collateral_amount, "Should withdraw entire collateral"
    _test(deposited, collateral_amount, _buffer=50)

    # Verify debt amount unchanged
    new_user_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0]
    assert new_user_debt.amount == user_debt.amount, "Debt amount should not change"

    # Verify health is still good (no liquidation)
    assert not new_user_debt.inLiquidation, "User should not be in liquidation"


def test_swap_maintains_user_debt_position(
    deleverage,
    credit_engine,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    simple_erc20_vault,
    vault_book,
    setupSwapScenario,
):
    """Test that swap does not modify user's debt amount"""
    setupSwapScenario(
        user=bob,
        withdraw_token=alpha_token,
        deposit_token=bravo_token,
        withdraw_whale=alpha_token_whale,
        deposit_whale=bravo_token_whale,
        governance=governance,
        deleverage=deleverage,
        withdraw_vault=simple_erc20_vault,
    )

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Get initial debt (should be 0 since we didn't borrow)
    initial_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0]

    # Execute swap
    deleverage.swapCollateral(
        bob,
        vault_id,
        alpha_token.address,
        vault_id,
        bravo_token.address,
        MAX_UINT256,
        sender=governance.address
    )

    # Debt should remain unchanged
    final_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0]
    assert final_debt.amount == initial_debt.amount, "Swap should not change debt amount"


########################
# USD Value Equivalence
########################


def test_swap_usd_value_preserved(
    deleverage,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    simple_erc20_vault,
    vault_book,
    setupSwapScenario,
    price_desk,
    _test,
):
    """Test that withdrawn and deposited amounts have equal USD value"""
    collateral_amount = 1000 * EIGHTEEN_DECIMALS
    setupSwapScenario(
        user=bob,
        withdraw_token=alpha_token,
        deposit_token=bravo_token,
        withdraw_whale=alpha_token_whale,
        deposit_whale=bravo_token_whale,
        governance=governance,
        deleverage=deleverage,
        withdraw_vault=simple_erc20_vault,
        collateral_amount=collateral_amount,
        governance_deposit_amount=collateral_amount,
        withdraw_price=1 * EIGHTEEN_DECIMALS,
        deposit_price=1 * EIGHTEEN_DECIMALS,
    )

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Execute swap
    withdrawn, deposited = deleverage.swapCollateral(
        bob,
        vault_id,
        alpha_token.address,
        vault_id,
        bravo_token.address,
        MAX_UINT256,
        sender=governance.address
    )

    # Calculate USD values
    withdrawn_usd = price_desk.getUsdValue(alpha_token, withdrawn, True)
    deposited_usd = price_desk.getUsdValue(bravo_token, deposited, True)

    # USD values should be equal (±50 bps tolerance for rounding)
    _test(withdrawn_usd, deposited_usd, _buffer=50)

    # Verify event also shows correct USD value
    logs = filter_logs(deleverage, "CollateralSwapped")
    assert len(logs) == 1
    _test(logs[0].usdValue, withdrawn_usd, _buffer=50)


def test_swap_different_decimal_tokens(
    deleverage,
    bob,
    alpha_token,
    charlie_token,
    governance,
    simple_erc20_vault,
    vault_book,
    setAssetConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    price_desk,
    alpha_token_whale,
    charlie_token_whale,
    _test,
):
    """
    Test swap between tokens with different decimals (18 vs 6).

    Verifies that swapping from alpha_token (18 decimals) to charlie_token (6 decimals)
    preserves USD value correctly despite the decimal difference.

    Example: 1000 alpha (18 decimals) at $1 = $1000 USD
             Should swap to 1000 charlie (6 decimals) at $1 = $1000 USD
    """
    # Setup alpha (18 decimals) at $1 price
    alpha_terms = createDebtTerms(_ltv=50_00)
    setAssetConfig(alpha_token, _debtTerms=alpha_terms)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Deposit 1000 alpha tokens (18 decimals)
    alpha_amount = 1000 * EIGHTEEN_DECIMALS  # 1000.000000000000000000
    performDeposit(bob, alpha_amount, alpha_token, alpha_token_whale, simple_erc20_vault)

    # Setup charlie (6 decimals) at $1 price
    charlie_terms = createDebtTerms(_ltv=75_00)  # Higher LTV to allow swap
    setAssetConfig(charlie_token, _debtTerms=charlie_terms)
    mock_price_source.setPrice(charlie_token, 1 * EIGHTEEN_DECIMALS)

    # Governance needs charlie tokens (6 decimals)
    charlie_amount = 1000 * 10**6  # 1000.000000 (6 decimals)
    charlie_token.transfer(governance, charlie_amount, sender=charlie_token_whale)
    charlie_token.approve(deleverage.address, charlie_amount, sender=governance.address)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Record balances before swap
    initial_bob_alpha = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    initial_bob_charlie = simple_erc20_vault.getTotalAmountForUser(bob, charlie_token)

    assert initial_bob_alpha == alpha_amount
    assert initial_bob_charlie == 0

    # Execute swap: 18-decimal token → 6-decimal token
    withdrawn, deposited = deleverage.swapCollateral(
        bob,
        vault_id,
        alpha_token.address,
        vault_id,
        charlie_token.address,
        MAX_UINT256,
        sender=governance.address
    )

    # Verify amounts withdrawn and deposited
    assert withdrawn == alpha_amount, "Should withdraw all alpha tokens"
    assert deposited == charlie_amount, "Should deposit equivalent charlie tokens"

    # Verify bob's vault balances
    final_bob_alpha = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    final_bob_charlie = simple_erc20_vault.getTotalAmountForUser(bob, charlie_token)

    assert final_bob_alpha == 0, "Bob should have no alpha left"
    assert final_bob_charlie == charlie_amount, "Bob should have charlie deposited"

    # Most important: Verify USD value is preserved despite decimal difference
    withdrawn_usd = price_desk.getUsdValue(alpha_token, withdrawn, True)
    deposited_usd = price_desk.getUsdValue(charlie_token, deposited, True)

    _test(withdrawn_usd, deposited_usd, _buffer=50)  # USD values should match within tolerance

    # Both should be approximately $1000 USD
    expected_usd = 1000 * EIGHTEEN_DECIMALS
    _test(withdrawn_usd, expected_usd, _buffer=50)
    _test(deposited_usd, expected_usd, _buffer=50)


def test_swap_different_prices(
    deleverage,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    simple_erc20_vault,
    vault_book,
    setupSwapScenario,
    price_desk,
    _test,
):
    """Test swap when assets have different prices"""
    collateral_amount = 1000 * EIGHTEEN_DECIMALS

    # Alpha: $1, Bravo: $2
    # So 1000 alpha ($1000 USD) should swap to 500 bravo ($1000 USD)
    setupSwapScenario(
        user=bob,
        withdraw_token=alpha_token,
        deposit_token=bravo_token,
        withdraw_whale=alpha_token_whale,
        deposit_whale=bravo_token_whale,
        governance=governance,
        deleverage=deleverage,
        withdraw_vault=simple_erc20_vault,
        collateral_amount=collateral_amount,
        governance_deposit_amount=1000 * EIGHTEEN_DECIMALS,  # Need enough for swap
        withdraw_price=1 * EIGHTEEN_DECIMALS,  # $1
        deposit_price=2 * EIGHTEEN_DECIMALS,   # $2
    )

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Execute swap
    withdrawn, deposited = deleverage.swapCollateral(
        bob,
        vault_id,
        alpha_token.address,
        vault_id,
        bravo_token.address,
        MAX_UINT256,
        sender=governance.address
    )

    # Should withdraw 1000 alpha
    assert withdrawn == collateral_amount

    # Should deposit ~500 bravo (half as many since bravo is 2x more expensive)
    expected_deposited = collateral_amount // 2
    _test(deposited, expected_deposited, _buffer=50)

    # Verify USD values match
    withdrawn_usd = price_desk.getUsdValue(alpha_token, withdrawn, True)
    deposited_usd = price_desk.getUsdValue(bravo_token, deposited, True)
    _test(withdrawn_usd, deposited_usd, _buffer=50)


def test_swap_return_values_correct(
    deleverage,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    simple_erc20_vault,
    vault_book,
    setupSwapScenario,
    _test,
):
    """Test that function returns correct (withdrawnAmount, depositAmount)"""
    collateral_amount = 750 * EIGHTEEN_DECIMALS
    setupSwapScenario(
        user=bob,
        withdraw_token=alpha_token,
        deposit_token=bravo_token,
        withdraw_whale=alpha_token_whale,
        deposit_whale=bravo_token_whale,
        governance=governance,
        deleverage=deleverage,
        withdraw_vault=simple_erc20_vault,
        collateral_amount=collateral_amount,
        governance_deposit_amount=collateral_amount,
    )

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Execute swap
    withdrawn, deposited = deleverage.swapCollateral(
        bob,
        vault_id,
        alpha_token.address,
        vault_id,
        bravo_token.address,
        MAX_UINT256,
        sender=governance.address
    )

    # Verify return values are exact
    assert withdrawn == collateral_amount, "Withdrawn should match collateral"
    _test(deposited, collateral_amount, _buffer=50)

    # Verify they match actual balance changes
    bob_bravo = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    assert bob_bravo == deposited, "Return value should match actual deposit"


#####################
# Permission Tests
#####################


def test_swap_governance_only_succeeds(
    deleverage,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    simple_erc20_vault,
    vault_book,
    setupSwapScenario,
    _test,
):
    """Test that governance can successfully call swapCollateral"""
    collateral_amount, _ = setupSwapScenario(
        user=bob,
        withdraw_token=alpha_token,
        deposit_token=bravo_token,
        withdraw_whale=alpha_token_whale,
        deposit_whale=bravo_token_whale,
        governance=governance,
        deleverage=deleverage,
        withdraw_vault=simple_erc20_vault,
    )

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Should succeed when called by governance
    withdrawn, deposited = deleverage.swapCollateral(
        bob,
        vault_id,
        alpha_token.address,
        vault_id,
        bravo_token.address,
        MAX_UINT256,
        sender=governance.address  # Governance is allowed
    )

    # Verify exact amounts
    assert withdrawn == collateral_amount
    _test(deposited, collateral_amount, _buffer=50)


def test_swap_user_cannot_call(
    deleverage,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    simple_erc20_vault,
    vault_book,
    setupSwapScenario,
):
    """Test that user cannot swap their own collateral"""
    setupSwapScenario(
        user=bob,
        withdraw_token=alpha_token,
        deposit_token=bravo_token,
        withdraw_whale=alpha_token_whale,
        deposit_whale=bravo_token_whale,
        governance=governance,
        deleverage=deleverage,
        withdraw_vault=simple_erc20_vault,
    )

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Bob tries to swap his own collateral - should fail
    with boa.reverts("governance only"):
        deleverage.swapCollateral(
            bob,
            vault_id,
            alpha_token.address,
            vault_id,
            bravo_token.address,
            MAX_UINT256,
            sender=bob  # User cannot call
        )


def test_swap_non_governance_fails(
    deleverage,
    bob,
    alice,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    simple_erc20_vault,
    vault_book,
    setupSwapScenario,
):
    """Test that random address cannot call swapCollateral"""
    setupSwapScenario(
        user=bob,
        withdraw_token=alpha_token,
        deposit_token=bravo_token,
        withdraw_whale=alpha_token_whale,
        deposit_whale=bravo_token_whale,
        governance=governance,
        deleverage=deleverage,
        withdraw_vault=simple_erc20_vault,
    )

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Alice (random user) tries to swap bob's collateral
    with boa.reverts("governance only"):
        deleverage.swapCollateral(
            bob,
            vault_id,
            alpha_token.address,
            vault_id,
            bravo_token.address,
            MAX_UINT256,
            sender=alice  # Random address cannot call
        )


#################
# Error Cases
#################


def test_swap_paused_contract_fails(
    deleverage,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    simple_erc20_vault,
    vault_book,
    setupSwapScenario,
    switchboard_alpha,
):
    """Test that swap fails when contract is paused"""
    setupSwapScenario(
        user=bob,
        withdraw_token=alpha_token,
        deposit_token=bravo_token,
        withdraw_whale=alpha_token_whale,
        deposit_whale=bravo_token_whale,
        governance=governance,
        deleverage=deleverage,
        withdraw_vault=simple_erc20_vault,
    )

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Pause the contract
    deleverage.pause(True, sender=switchboard_alpha.address)

    # Should fail when paused
    with boa.reverts("contract paused"):
        deleverage.swapCollateral(
            bob,
            vault_id,
            alpha_token.address,
            vault_id,
            bravo_token.address,
            MAX_UINT256,
            sender=governance.address
        )


def test_swap_empty_user_address_fails(
    deleverage,
    alpha_token,
    bravo_token,
    governance,
    vault_book,
    simple_erc20_vault,
):
    """Test that swap fails with empty user address"""
    vault_id = vault_book.getRegId(simple_erc20_vault)

    with boa.reverts("invalid assets"):
        deleverage.swapCollateral(
            "0x0000000000000000000000000000000000000000",  # Empty user address
            vault_id,
            alpha_token.address,
            vault_id,
            bravo_token.address,
            MAX_UINT256,
            sender=governance.address
        )


def test_swap_empty_withdraw_asset_fails(
    deleverage,
    bob,
    bravo_token,
    governance,
    vault_book,
    simple_erc20_vault,
):
    """Test that swap fails with empty withdraw asset"""
    vault_id = vault_book.getRegId(simple_erc20_vault)

    with boa.reverts("invalid assets"):
        deleverage.swapCollateral(
            bob,
            vault_id,
            "0x0000000000000000000000000000000000000000",  # Empty withdraw asset
            vault_id,
            bravo_token.address,
            MAX_UINT256,
            sender=governance.address
        )


def test_swap_empty_deposit_asset_fails(
    deleverage,
    bob,
    alpha_token,
    governance,
    vault_book,
    simple_erc20_vault,
):
    """Test that swap fails with empty deposit asset"""
    vault_id = vault_book.getRegId(simple_erc20_vault)

    with boa.reverts("invalid assets"):
        deleverage.swapCollateral(
            bob,
            vault_id,
            alpha_token.address,
            vault_id,
            "0x0000000000000000000000000000000000000000",  # Empty deposit asset
            MAX_UINT256,
            sender=governance.address
        )


def test_swap_zero_withdraw_vault_fails(
    deleverage,
    bob,
    alpha_token,
    bravo_token,
    governance,
    vault_book,
    simple_erc20_vault,
):
    """Test that swap fails with zero withdraw vault ID"""
    vault_id = vault_book.getRegId(simple_erc20_vault)

    with boa.reverts("invalid vault ids"):
        deleverage.swapCollateral(
            bob,
            0,  # Invalid vault ID
            alpha_token.address,
            vault_id,
            bravo_token.address,
            MAX_UINT256,
            sender=governance.address
        )


def test_swap_zero_deposit_vault_fails(
    deleverage,
    bob,
    alpha_token,
    bravo_token,
    governance,
    vault_book,
    simple_erc20_vault,
):
    """Test that swap fails with zero deposit vault ID"""
    vault_id = vault_book.getRegId(simple_erc20_vault)

    with boa.reverts("invalid vault ids"):
        deleverage.swapCollateral(
            bob,
            vault_id,
            alpha_token.address,
            0,  # Invalid vault ID
            bravo_token.address,
            MAX_UINT256,
            sender=governance.address
        )


def test_swap_invalid_withdraw_vault_fails(
    deleverage,
    bob,
    alpha_token,
    bravo_token,
    governance,
    vault_book,
    simple_erc20_vault,
):
    """Test that swap fails with invalid withdraw vault"""
    vault_id = vault_book.getRegId(simple_erc20_vault)

    with boa.reverts("invalid withdraw vault"):
        deleverage.swapCollateral(
            bob,
            9999,  # Non-existent vault ID
            alpha_token.address,
            vault_id,
            bravo_token.address,
            MAX_UINT256,
            sender=governance.address
        )


def test_swap_invalid_deposit_vault_fails(
    deleverage,
    bob,
    alpha_token,
    bravo_token,
    governance,
    vault_book,
    simple_erc20_vault,
):
    """Test that swap fails with invalid deposit vault"""
    vault_id = vault_book.getRegId(simple_erc20_vault)

    with boa.reverts("invalid deposit vault"):
        deleverage.swapCollateral(
            bob,
            vault_id,
            alpha_token.address,
            9999,  # Non-existent vault ID
            bravo_token.address,
            MAX_UINT256,
            sender=governance.address
        )


def test_swap_no_collateral_fails(
    deleverage,
    bob,
    alpha_token,
    bravo_token,
    bravo_token_whale,
    governance,
    simple_erc20_vault,
    vault_book,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
):
    """Test that swap fails when user has no collateral to withdraw"""
    # Setup assets but DON'T deposit any collateral for bob
    withdraw_terms = createDebtTerms(_ltv=50_00)
    deposit_terms = createDebtTerms(_ltv=75_00)
    setAssetConfig(alpha_token, _debtTerms=withdraw_terms)
    setAssetConfig(bravo_token, _debtTerms=deposit_terms)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)

    # Give governance some bravo tokens
    bravo_token.transfer(governance, 1000 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    bravo_token.approve(deleverage.address, 1000 * EIGHTEEN_DECIMALS, sender=governance.address)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Bob has no alpha collateral, so withdrawal should fail
    with boa.reverts():
        deleverage.swapCollateral(
            bob,
            vault_id,
            alpha_token.address,
            vault_id,
            bravo_token.address,
            MAX_UINT256,
            sender=governance.address
        )


def test_swap_insufficient_governance_tokens_fails(
    deleverage,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    governance,
    simple_erc20_vault,
    vault_book,
    setAssetConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
):
    """Test that swap fails when governance doesn't have enough deposit tokens"""
    # Setup alpha collateral for bob
    withdraw_terms = createDebtTerms(_ltv=50_00)
    deposit_terms = createDebtTerms(_ltv=75_00)
    setAssetConfig(alpha_token, _debtTerms=withdraw_terms)
    setAssetConfig(bravo_token, _debtTerms=deposit_terms)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)

    collateral_amount = 1000 * EIGHTEEN_DECIMALS
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale, simple_erc20_vault)

    # DON'T give governance any bravo tokens
    # So transferFrom will fail

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Should fail because governance can't transfer bravo tokens
    with boa.reverts("transferFrom failed"):
        deleverage.swapCollateral(
            bob,
            vault_id,
            alpha_token.address,
            vault_id,
            bravo_token.address,
            MAX_UINT256,
            sender=governance.address
        )


###############
# Edge Cases
###############


def test_swap_depletes_entire_position(
    deleverage,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    simple_erc20_vault,
    vault_book,
    setupSwapScenario,
    _test,
):
    """Test swapping entire position marks vault balance as depleted"""
    collateral_amount = 500 * EIGHTEEN_DECIMALS
    setupSwapScenario(
        user=bob,
        withdraw_token=alpha_token,
        deposit_token=bravo_token,
        withdraw_whale=alpha_token_whale,
        deposit_whale=bravo_token_whale,
        governance=governance,
        deleverage=deleverage,
        withdraw_vault=simple_erc20_vault,
        collateral_amount=collateral_amount,
        governance_deposit_amount=collateral_amount,
    )

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Swap entire position
    withdrawn, deposited = deleverage.swapCollateral(
        bob,
        vault_id,
        alpha_token.address,
        vault_id,
        bravo_token.address,
        MAX_UINT256,
        sender=governance.address
    )

    # Verify alpha position is completely depleted
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0, "Alpha position should be depleted"

    # Verify exact bravo position deposited
    bravo_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    _test(bravo_balance, collateral_amount, _buffer=50)


def test_swap_same_asset_different_vaults(
    deleverage,
    bob,
    alpha_token,
    alpha_token_whale,
    governance,
    simple_erc20_vault,
    rebase_erc20_vault,
    vault_book,
    setAssetConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
):
    """Test moving same asset from vault A to vault B"""
    # Setup alpha in both vaults
    debt_terms = createDebtTerms(_ltv=50_00)
    setAssetConfig(alpha_token, _vaultIds=[3, 4], _debtTerms=debt_terms)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    collateral_amount = 1000 * EIGHTEEN_DECIMALS

    # Bob deposits alpha in simple_erc20_vault (vault 3)
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale, simple_erc20_vault)

    # Governance has alpha for deposit
    alpha_token.transfer(governance, collateral_amount, sender=alpha_token_whale)
    alpha_token.approve(deleverage.address, collateral_amount, sender=governance.address)

    withdraw_vault_id = vault_book.getRegId(simple_erc20_vault)
    deposit_vault_id = vault_book.getRegId(rebase_erc20_vault)

    # Swap same asset between vaults
    withdrawn, deposited = deleverage.swapCollateral(
        bob,
        withdraw_vault_id,  # Vault 3
        alpha_token.address,
        deposit_vault_id,   # Vault 4
        alpha_token.address,  # Same asset!
        MAX_UINT256,
        sender=governance.address
    )

    # Verify moved from vault 3 to vault 4
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0
    assert rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token) == deposited
    assert withdrawn == deposited, "Same asset same amount"


def test_swap_very_small_amounts(
    deleverage,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    simple_erc20_vault,
    vault_book,
    setupSwapScenario,
    _test,
):
    """Test swapping dust/wei-level amounts"""
    # Use very small collateral amount (100 wei)
    dust_amount = 100
    setupSwapScenario(
        user=bob,
        withdraw_token=alpha_token,
        deposit_token=bravo_token,
        withdraw_whale=alpha_token_whale,
        deposit_whale=bravo_token_whale,
        governance=governance,
        deleverage=deleverage,
        withdraw_vault=simple_erc20_vault,
        collateral_amount=dust_amount,
        governance_deposit_amount=dust_amount,
    )

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Should handle dust amounts without reverting
    withdrawn, deposited = deleverage.swapCollateral(
        bob,
        vault_id,
        alpha_token.address,
        vault_id,
        bravo_token.address,
        MAX_UINT256,
        sender=governance.address
    )

    # Verify exact amounts
    assert withdrawn == dust_amount
    _test(deposited, dust_amount, _buffer=50)


def test_swap_handles_rounding(
    deleverage,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    simple_erc20_vault,
    vault_book,
    setupSwapScenario,
    price_desk,
):
    """Test that swap handles integer division rounding correctly"""
    # Use odd amount that doesn't divide evenly
    collateral_amount = 1001 * EIGHTEEN_DECIMALS

    setupSwapScenario(
        user=bob,
        withdraw_token=alpha_token,
        deposit_token=bravo_token,
        withdraw_whale=alpha_token_whale,
        deposit_whale=bravo_token_whale,
        governance=governance,
        deleverage=deleverage,
        withdraw_vault=simple_erc20_vault,
        collateral_amount=collateral_amount,
        governance_deposit_amount=collateral_amount,
    )

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Execute swap
    withdrawn, deposited = deleverage.swapCollateral(
        bob,
        vault_id,
        alpha_token.address,
        vault_id,
        bravo_token.address,
        MAX_UINT256,
        sender=governance.address
    )

    # Verify no significant loss due to rounding
    withdrawn_usd = price_desk.getUsdValue(alpha_token, withdrawn, True)
    deposited_usd = price_desk.getUsdValue(bravo_token, deposited, True)

    # Allow small rounding difference (< 0.01%)
    diff = abs(withdrawn_usd - deposited_usd)
    assert diff < withdrawn_usd // 10000, "Rounding loss should be minimal"


def test_swap_max_value_with_exact_balance(
    deleverage,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    simple_erc20_vault,
    vault_book,
    setupSwapScenario,
):
    """Test that max_value equals actual balance works correctly"""
    exact_amount = 777 * EIGHTEEN_DECIMALS
    setupSwapScenario(
        user=bob,
        withdraw_token=alpha_token,
        deposit_token=bravo_token,
        withdraw_whale=alpha_token_whale,
        deposit_whale=bravo_token_whale,
        governance=governance,
        deleverage=deleverage,
        withdraw_vault=simple_erc20_vault,
        collateral_amount=exact_amount,
        governance_deposit_amount=exact_amount,
    )

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Verify initial balance
    initial_balance = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    assert initial_balance == exact_amount

    # Use max_value (should withdraw exact balance)
    withdrawn, deposited = deleverage.swapCollateral(
        bob,
        vault_id,
        alpha_token.address,
        vault_id,
        bravo_token.address,
        MAX_UINT256,
        sender=governance.address
    )

    # Should withdraw exact initial balance
    assert withdrawn == exact_amount
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0


def test_swap_price_oracle_precision(
    deleverage,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    simple_erc20_vault,
    vault_book,
    setupSwapScenario,
    mock_price_source,
    price_desk,
    _test,
):
    """Test swap with non-standard price ratios maintains USD value"""
    collateral_amount = 1000 * EIGHTEEN_DECIMALS

    # Set alpha at $2.50
    alpha_price = int(2.5 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(alpha_token, alpha_price)

    # Set bravo at $0.33
    bravo_price = int(0.33 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, bravo_price)

    setupSwapScenario(
        user=bob,
        withdraw_token=alpha_token,
        deposit_token=bravo_token,
        withdraw_whale=alpha_token_whale,
        deposit_whale=bravo_token_whale,
        governance=governance,
        deleverage=deleverage,
        withdraw_vault=simple_erc20_vault,
        collateral_amount=collateral_amount,
        governance_deposit_amount=10_000 * EIGHTEEN_DECIMALS,
        withdraw_price=alpha_price,
        deposit_price=bravo_price,
    )

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Execute swap
    withdrawn, deposited = deleverage.swapCollateral(
        bob,
        vault_id,
        alpha_token.address,
        vault_id,
        bravo_token.address,
        MAX_UINT256,
        sender=governance.address
    )

    # Verify USD values match
    withdrawn_usd = price_desk.getUsdValue(alpha_token, withdrawn, True)
    deposited_usd = price_desk.getUsdValue(bravo_token, deposited, True)
    _test(withdrawn_usd, deposited_usd, _buffer=50)


#####################
# Event Validation
#####################


def test_swap_event_emitted_correct_values(
    deleverage,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    simple_erc20_vault,
    vault_book,
    setupSwapScenario,
    price_desk,
    _test,
):
    """Test that CollateralSwapped event is emitted with all correct field values"""
    collateral_amount = 1000 * EIGHTEEN_DECIMALS
    setupSwapScenario(
        user=bob,
        withdraw_token=alpha_token,
        deposit_token=bravo_token,
        withdraw_whale=alpha_token_whale,
        deposit_whale=bravo_token_whale,
        governance=governance,
        deleverage=deleverage,
        withdraw_vault=simple_erc20_vault,
        collateral_amount=collateral_amount,
        governance_deposit_amount=collateral_amount,
    )

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Execute swap
    withdrawn, deposited = deleverage.swapCollateral(
        bob,
        vault_id,
        alpha_token.address,
        vault_id,
        bravo_token.address,
        MAX_UINT256,
        sender=governance.address
    )

    # Verify event
    logs = filter_logs(deleverage, "CollateralSwapped")
    assert len(logs) == 1, "Exactly one event should be emitted"

    log = logs[0]
    assert log.user == bob, "Event user field incorrect"
    assert log.caller == governance.address, "Event caller field incorrect"
    assert log.withdrawVaultId == vault_id, "Event withdrawVaultId field incorrect"
    assert log.withdrawAsset == alpha_token.address, "Event withdrawAsset field incorrect"
    assert log.withdrawAmount == withdrawn, "Event withdrawAmount field incorrect"
    assert log.depositVaultId == vault_id, "Event depositVaultId field incorrect"
    assert log.depositAsset == bravo_token.address, "Event depositAsset field incorrect"
    assert log.depositAmount == deposited, "Event depositAmount field incorrect"

    # Verify exact USD value
    expected_usd = price_desk.getUsdValue(alpha_token, withdrawn, True)
    _test(log.usdValue, expected_usd, _buffer=50)


def test_swap_event_usd_value_matches_calculation(
    deleverage,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    simple_erc20_vault,
    vault_book,
    setupSwapScenario,
    price_desk,
    _test,
):
    """Test that event usdValue matches actual calculation"""
    setupSwapScenario(
        user=bob,
        withdraw_token=alpha_token,
        deposit_token=bravo_token,
        withdraw_whale=alpha_token_whale,
        deposit_whale=bravo_token_whale,
        governance=governance,
        deleverage=deleverage,
        withdraw_vault=simple_erc20_vault,
    )

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Execute swap
    withdrawn, deposited = deleverage.swapCollateral(
        bob,
        vault_id,
        alpha_token.address,
        vault_id,
        bravo_token.address,
        MAX_UINT256,
        sender=governance.address
    )

    # Calculate expected USD value
    expected_usd = price_desk.getUsdValue(alpha_token, withdrawn, True)

    # Get event
    logs = filter_logs(deleverage, "CollateralSwapped")
    event_usd = logs[0].usdValue

    # Event USD should match calculation (±50 bps)
    _test(event_usd, expected_usd, _buffer=50)


###########################
# Balance Verification
###########################


def test_swap_user_balance_changes(
    deleverage,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    simple_erc20_vault,
    vault_book,
    setupSwapScenario,
):
    """Test that user loses withdrawAsset and gains depositAsset"""
    collateral_amount = 1000 * EIGHTEEN_DECIMALS
    setupSwapScenario(
        user=bob,
        withdraw_token=alpha_token,
        deposit_token=bravo_token,
        withdraw_whale=alpha_token_whale,
        deposit_whale=bravo_token_whale,
        governance=governance,
        deleverage=deleverage,
        withdraw_vault=simple_erc20_vault,
        collateral_amount=collateral_amount,
        governance_deposit_amount=collateral_amount,
    )

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Record initial user vault balances
    initial_alpha = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    initial_bravo = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)

    assert initial_alpha == collateral_amount
    assert initial_bravo == 0

    # Execute swap
    withdrawn, deposited = deleverage.swapCollateral(
        bob,
        vault_id,
        alpha_token.address,
        vault_id,
        bravo_token.address,
        MAX_UINT256,
        sender=governance.address
    )

    # Verify user vault balances changed correctly
    final_alpha = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    final_bravo = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)

    assert final_alpha == 0, "User should have no alpha left"
    assert final_bravo == deposited, "User should have bravo deposited"


def test_swap_governance_balance_changes(
    deleverage,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    simple_erc20_vault,
    vault_book,
    setupSwapScenario,
):
    """Test that governance gains withdrawAsset and loses depositAsset"""
    collateral_amount = 1000 * EIGHTEEN_DECIMALS
    setupSwapScenario(
        user=bob,
        withdraw_token=alpha_token,
        deposit_token=bravo_token,
        withdraw_whale=alpha_token_whale,
        deposit_whale=bravo_token_whale,
        governance=governance,
        deleverage=deleverage,
        withdraw_vault=simple_erc20_vault,
        collateral_amount=collateral_amount,
        governance_deposit_amount=collateral_amount,
    )

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Record initial governance wallet balances
    initial_gov_alpha = alpha_token.balanceOf(governance)
    initial_gov_bravo = bravo_token.balanceOf(governance)

    # Execute swap
    withdrawn, deposited = deleverage.swapCollateral(
        bob,
        vault_id,
        alpha_token.address,
        vault_id,
        bravo_token.address,
        MAX_UINT256,
        sender=governance.address
    )

    # Verify governance wallet balances changed correctly
    final_gov_alpha = alpha_token.balanceOf(governance)
    final_gov_bravo = bravo_token.balanceOf(governance)

    assert final_gov_alpha == initial_gov_alpha + withdrawn, "Gov should receive withdrawn alpha"
    assert final_gov_bravo == initial_gov_bravo - deposited, "Gov should spend deposited bravo"


def test_swap_vault_balances_updated(
    deleverage,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    simple_erc20_vault,
    vault_book,
    setupSwapScenario,
):
    """Test that vault contract balances are updated correctly"""
    collateral_amount = 1000 * EIGHTEEN_DECIMALS
    setupSwapScenario(
        user=bob,
        withdraw_token=alpha_token,
        deposit_token=bravo_token,
        withdraw_whale=alpha_token_whale,
        deposit_whale=bravo_token_whale,
        governance=governance,
        deleverage=deleverage,
        withdraw_vault=simple_erc20_vault,
        collateral_amount=collateral_amount,
        governance_deposit_amount=collateral_amount,
    )

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Record initial vault contract balances
    initial_vault_alpha = alpha_token.balanceOf(simple_erc20_vault)
    initial_vault_bravo = bravo_token.balanceOf(simple_erc20_vault)

    # Execute swap
    withdrawn, deposited = deleverage.swapCollateral(
        bob,
        vault_id,
        alpha_token.address,
        vault_id,
        bravo_token.address,
        MAX_UINT256,
        sender=governance.address
    )

    # Verify vault contract balances updated
    final_vault_alpha = alpha_token.balanceOf(simple_erc20_vault)
    final_vault_bravo = bravo_token.balanceOf(simple_erc20_vault)

    assert final_vault_alpha == initial_vault_alpha - withdrawn, "Vault should have less alpha"
    assert final_vault_bravo == initial_vault_bravo + deposited, "Vault should have more bravo"


#####################
# Integration Tests
#####################


def test_swap_then_borrow_more(
    deleverage,
    teller,
    credit_engine,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    simple_erc20_vault,
    vault_book,
    setupSwapScenario,
):
    """Test that after swapping to higher LTV, user can borrow more"""
    collateral_amount = 1000 * EIGHTEEN_DECIMALS
    setupSwapScenario(
        user=bob,
        withdraw_token=alpha_token,
        deposit_token=bravo_token,
        withdraw_whale=alpha_token_whale,
        deposit_whale=bravo_token_whale,
        governance=governance,
        deleverage=deleverage,
        withdraw_vault=simple_erc20_vault,
        collateral_amount=collateral_amount,
        governance_deposit_amount=collateral_amount,
        withdraw_ltv=50_00,  # 50% LTV
        deposit_ltv=75_00,   # 75% LTV
    )

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Get initial max debt (with 50% LTV)
    initial_max_debt = credit_engine.getUserBorrowTerms(bob, False).totalMaxDebt

    # Execute swap to higher LTV asset
    deleverage.swapCollateral(
        bob,
        vault_id,
        alpha_token.address,
        vault_id,
        bravo_token.address,
        MAX_UINT256,
        sender=governance.address
    )

    # Get new max debt (with 75% LTV)
    new_max_debt = credit_engine.getUserBorrowTerms(bob, False).totalMaxDebt

    # Verify can borrow more now
    assert new_max_debt > initial_max_debt, "Should have higher borrowing capacity"

    # Actually borrow the additional amount
    additional_borrow = (new_max_debt - initial_max_debt) // 2
    teller.borrow(additional_borrow, bob, False, sender=bob)

    # Verify borrow succeeded
    user_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0]
    assert user_debt.amount >= additional_borrow, "Should have borrowed successfully"


def test_swap_then_withdraw_new_collateral(
    deleverage,
    teller,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    simple_erc20_vault,
    vault_book,
    setupSwapScenario,
):
    """Test that after swap, user can withdraw the new collateral"""
    collateral_amount = 1000 * EIGHTEEN_DECIMALS
    setupSwapScenario(
        user=bob,
        withdraw_token=alpha_token,
        deposit_token=bravo_token,
        withdraw_whale=alpha_token_whale,
        deposit_whale=bravo_token_whale,
        governance=governance,
        deleverage=deleverage,
        withdraw_vault=simple_erc20_vault,
        collateral_amount=collateral_amount,
        governance_deposit_amount=collateral_amount,
    )

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Execute swap
    withdrawn, deposited = deleverage.swapCollateral(
        bob,
        vault_id,
        alpha_token.address,
        vault_id,
        bravo_token.address,
        MAX_UINT256,
        sender=governance.address
    )

    # Verify bob has bravo in vault
    bravo_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    assert bravo_balance == deposited

    # Bob should be able to withdraw some bravo
    withdraw_amount = deposited // 2
    initial_bob_bravo = bravo_token.balanceOf(bob)

    teller.withdraw(bravo_token, withdraw_amount, bob, simple_erc20_vault, sender=bob)

    # Verify withdrawal succeeded
    final_bob_bravo = bravo_token.balanceOf(bob)
    assert final_bob_bravo == initial_bob_bravo + withdraw_amount, "Should have withdrawn bravo"


def test_swap_multiple_sequential(
    deleverage,
    bob,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    governance,
    simple_erc20_vault,
    vault_book,
    setAssetConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
):
    """Test multiple sequential swaps: alpha → bravo → charlie"""
    # Setup all three assets
    alpha_terms = createDebtTerms(_ltv=50_00)
    bravo_terms = createDebtTerms(_ltv=60_00)
    charlie_terms = createDebtTerms(_ltv=70_00)

    setAssetConfig(alpha_token, _debtTerms=alpha_terms)
    setAssetConfig(bravo_token, _debtTerms=bravo_terms)
    setAssetConfig(charlie_token, _debtTerms=charlie_terms)

    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, 1 * EIGHTEEN_DECIMALS)

    collateral_amount = 1000 * EIGHTEEN_DECIMALS

    # Bob starts with alpha
    performDeposit(bob, collateral_amount, alpha_token, alpha_token_whale, simple_erc20_vault)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Record initial governance balances
    initial_gov_alpha = alpha_token.balanceOf(governance)
    initial_gov_bravo = bravo_token.balanceOf(governance)

    # === First swap: alpha → bravo ===
    bravo_token.transfer(governance, collateral_amount, sender=bravo_token_whale)
    bravo_token.approve(deleverage.address, collateral_amount, sender=governance.address)

    withdrawn1, deposited1 = deleverage.swapCollateral(
        bob,
        vault_id,
        alpha_token.address,
        vault_id,
        bravo_token.address,
        MAX_UINT256,
        sender=governance.address
    )

    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == deposited1

    # === Second swap: bravo → charlie ===
    # Charlie has 6 decimals, so we need 1000 * 10^6 for $1000 worth
    charlie_amount = 1000 * 10**6  # Charlie has 6 decimals
    charlie_token.transfer(governance, charlie_amount, sender=charlie_token_whale)
    charlie_token.approve(deleverage.address, charlie_amount, sender=governance.address)

    withdrawn2, deposited2 = deleverage.swapCollateral(
        bob,
        vault_id,
        bravo_token.address,
        vault_id,
        charlie_token.address,
        MAX_UINT256,
        sender=governance.address
    )

    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == 0
    assert simple_erc20_vault.getTotalAmountForUser(bob, charlie_token) == deposited2

    # Verify governance received all withdrawn assets (check deltas)
    assert alpha_token.balanceOf(governance) == initial_gov_alpha + withdrawn1
    assert bravo_token.balanceOf(governance) == initial_gov_bravo + collateral_amount + withdrawn2 - deposited1

    # Verify final state: bob has only charlie
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == 0
    assert simple_erc20_vault.getTotalAmountForUser(bob, charlie_token) > 0
