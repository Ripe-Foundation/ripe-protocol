"""Replay-safe deployment shape for the RIPE/WETH monitoring contract.

Editing this historical module does not prove or mutate the current on-chain
instance. The stripped monitor has no local governance, timelock, snapshot, or
price-feed state. A deployment must bind the exact RIPE/WETH pair and the four
constructor identities before it can replace an older monitoring instance.
"""

from scripts.utils import log
from scripts.utils.migration import Migration

from config.robinhood_launch import (
    RIPE_WETH_POOL,
    address,
)


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    ripe_token = migration.get_contract("RipeToken")

    log.h1("Deploying UniswapV2Prices")

    # PriceSource remains an inert compatibility shell. The source also exposes
    # constructor-bound RIPE views and a generic stateless offchain monitoring
    # view; editing this source does not authorize execution of this module.
    uniswap = migration.deploy(
        "UniswapV2Prices",
        hq,
        RIPE_WETH_POOL,
        ripe_token,
        address("WETH"),
    )

    assert uniswap.isMonitoringOnly()
    assert uniswap.RIPE_HQ() == hq.address
    assert uniswap.RIPE_WETH_POOL() == RIPE_WETH_POOL
    assert uniswap.RIPE_TOKEN() == ripe_token.address
    assert uniswap.WETH_TOKEN() == address("WETH")
    assert uniswap.getPriceAndHasFeed(ripe_token.address) == (0, False)
