"""Replay-safe deployment shape for the already-deployed monitoring contract.

Editing this historical module does not prove or mutate the current on-chain
instance. Operators must bind its deployed runtime and read back its local
governance and action timelock independently; an older tempGov-zero deployment
must be finalized through RipeHq governance rather than described as if this
corrected flow had already run.
"""

from scripts.utils import log
from scripts.utils.migration import Migration

from config.robinhood_launch import (
    PRICE_CHANGE_MAX_TIMELOCK,
    PRICE_CHANGE_MIN_TIMELOCK,
    RIPE_WETH_POOL,
    ZERO_ADDRESS,
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
    uniswap = migration.deploy(
        "UniswapV2Prices",
        hq,
        migration.account(),
        RIPE_WETH_POOL,
        ripe_token,
        PRICE_CHANGE_MIN_TIMELOCK,
        PRICE_CHANGE_MAX_TIMELOCK,
    )

    # This contract is deliberately deployed for direct monitoring only. It is
    # never added to PriceDesk, so the standard price-source interface cannot
    # become a protocol valuation route. Finalize the configuration timelock
    # while the deployer still holds temporary local governance, verify the
    # readback, then irreversibly fall back to RipeHq governance.
    assert int(uniswap.actionTimeLock()) == 0
    selected = int(uniswap.minActionTimeLock())
    assert selected == PRICE_CHANGE_MIN_TIMELOCK and selected != 0
    migration.execute(uniswap.setActionTimeLockAfterSetup, selected)
    assert int(uniswap.actionTimeLock()) == selected
    migration.execute(uniswap.relinquishGov)
    assert uniswap.governance() == ZERO_ADDRESS
