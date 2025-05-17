import pytest
import boa

from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS, MAX_UINT256


def test_ripe_hq_and_tokens_setup(
    ripe_hq,
    green_token,
    ripe_token,
    governance,
    vault_book,
    price_desk,
    chainlink,
):
    # ripe hq tokens
    assert ripe_hq.greenToken() == green_token.address
    assert ripe_hq.ripeToken() == ripe_token.address

    # registry
    assert ripe_hq.registryChangeTimeLock() != 0
    assert ripe_hq.getNumAddrs() == 13

    # governance
    assert ripe_hq.governance() == governance.address
    assert ripe_hq.govChangeTimeLock() != 0

    # tokens
    assert ripe_token.ripeHq() == ripe_hq.address
    assert ripe_token.hqChangeTimeLock() != 0
    assert green_token.ripeHq() == ripe_hq.address
    assert green_token.hqChangeTimeLock() != 0
    
    # vault book
    assert vault_book.registryChangeTimeLock() != 0
    assert vault_book.getNumAddrs() == 3
    assert vault_book.governance() == ZERO_ADDRESS

    # price desk
    assert price_desk.registryChangeTimeLock() != 0
    assert price_desk.getNumAddrs() == 2
    assert price_desk.governance() == ZERO_ADDRESS

    # chainlink
    assert chainlink.actionTimeLock() != 0
    assert chainlink.numAssets() == 3
    assert chainlink.governance() == ZERO_ADDRESS


def test_savings_green(
    green_token,
    savings_green,
    whale,
    sally,
):
    # token
    assert savings_green.asset() == green_token.address
    assert savings_green.totalAssets() == 0

    # deposit
    amount = 1_000 * EIGHTEEN_DECIMALS
    green_token.approve(savings_green, amount, sender=whale)
    assert savings_green.deposit(amount, sender=whale) != 0

    assert savings_green.totalAssets() == amount
    assert green_token.balanceOf(savings_green) == amount
    sgreen_bal = savings_green.balanceOf(whale)
    assert sgreen_bal != 0

    # transfer sgreen to sally
    savings_green.transfer(sally, sgreen_bal, sender=whale)
    assert savings_green.balanceOf(sally) == sgreen_bal
    assert savings_green.balanceOf(whale) == 0

    # withdraw
    assert savings_green.redeem(MAX_UINT256, sender=sally) == amount
    assert savings_green.balanceOf(sally) == 0
    assert green_token.balanceOf(sally) == amount
    assert green_token.balanceOf(savings_green) == 0
