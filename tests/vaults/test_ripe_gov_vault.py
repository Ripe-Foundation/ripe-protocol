import pytest
import boa

from constants import EIGHTEEN_DECIMALS


def test_ripe_gov_vault_initial_deposit(
    ripe_gov_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    _test,
):
    """Test initial deposit and share calculation"""
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(ripe_gov_vault, deposit_amount, sender=alpha_token_whale)
    
    # First deposit should create 1:1 shares
    deposited = ripe_gov_vault.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)
    assert deposited == deposit_amount

    # Check shares and amounts
    amount = ripe_gov_vault.getTotalAmountForUser(bob, alpha_token)
    _test(deposit_amount, amount)  # Amount should be close to deposit_amount
