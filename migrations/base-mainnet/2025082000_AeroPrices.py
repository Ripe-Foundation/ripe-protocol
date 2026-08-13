"""Deploy the standalone RIPE/Aerodrome monitoring contract.

This monitor is not registered in PriceDesk and does not replace or disable the
legacy slot-6 source. A completed historical checkpoint will not rerun this
file, so an actual live deployment requires a future numbered migration or
equivalent deployment operation. Retirement remains a separate frontend-first
step.
"""

from scripts.utils.migration import Migration


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    ripe_weth_pool = migration.get_address("RipePoolAero")
    ripe_token = migration.get_address("RipeToken")
    weth_token = migration.blueprint().CORE_TOKENS["WETH"]

    aero_monitor = migration.deploy(
        "AeroRipePrices",
        hq,
        ripe_weth_pool,
        ripe_token,
        weth_token,
    )

    assert aero_monitor.isMonitoringOnly()
    assert aero_monitor.RIPE_HQ() == hq.address
    assert aero_monitor.RIPE_WETH_POOL() == ripe_weth_pool
    assert aero_monitor.RIPE_TOKEN() == ripe_token
    assert aero_monitor.WETH_TOKEN() == weth_token
    assert aero_monitor.getPriceAndHasFeed(ripe_token) == (0, False)
