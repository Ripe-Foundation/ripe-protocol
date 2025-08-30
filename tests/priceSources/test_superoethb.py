import pytest
import boa

from config.BluePrint import YIELD_TOKENS


@pytest.base
def test_wrapped_super_oethb_price(
    wsuper_oethb_prices,
    chainlink,
    governance,
    fork,
):
    # setup chainlink feed for super oeth
    super_oeth = boa.from_etherscan(YIELD_TOKENS[fork]["SUPER_OETH"])
    assert chainlink.addNewPriceFeed(super_oeth, "0x39C6E14CdE46D4FFD9F04Ff159e7ce8eC20E10B4", 0, True, sender=governance.address)
    boa.env.time_travel(blocks=chainlink.actionTimeLock() + 1)
    assert chainlink.confirmNewPriceFeed(super_oeth, sender=governance.address)

    # get price of wrapped super oeth
    wsuper_oeth = boa.from_etherscan(YIELD_TOKENS[fork]["WRAPPED_SUPER_OETH"])
    price = wsuper_oethb_prices.getPrice(wsuper_oeth)
    assert price != 0
