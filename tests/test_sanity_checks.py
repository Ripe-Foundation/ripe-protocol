import pytest
import boa

from constants import ZERO_ADDRESS


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

