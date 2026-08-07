from scripts.utils import log
from scripts.utils.migration import Migration

from config.robinhood_launch import (
    PRICE_CHANGE_MAX_TIMELOCK,
    PRICE_CHANGE_MIN_TIMELOCK,
    ZERO_ADDRESS,
    RIPE_WETH_POOL,
)


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    ripe_token = migration.get_contract("RipeToken")

    log.h1("Deploying UniswapV2Prices")

    # Unlike every other Robinhood contract, this one takes the deployer as
    # tempGov instead of ZERO_ADDRESS. Governance has already moved to the
    # Safe, so a contract with no local governance could not have its snapshot
    # config set without a Safe transaction. The deployer holds local gov only
    # long enough to configure the feed, then gives it up below.
    migration.deploy(
        "UniswapV2Prices",
        hq,
        ZERO_ADDRESS,
        RIPE_WETH_POOL,
        ripe_token,
        PRICE_CHANGE_MIN_TIMELOCK,
        PRICE_CHANGE_MAX_TIMELOCK,
    )
