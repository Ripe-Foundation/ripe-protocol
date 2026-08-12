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

    # The source implements PriceSource only as an inert compatibility shell.
    # Its only functional methods are explicitly named RIPE monitoring views.
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
