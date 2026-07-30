from scripts.utils import log
from scripts.utils.migration import Migration


# Before scheduling this migration, execute it through scripts/migrate.py on a
# pinned Base-mainnet fork and retain the MigrationRunner log. Offline/static
# constructor checks are not a substitute because the four legacy values below
# are intentionally read from the live Deleverage deployment at execution time.
def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    current_deleverage = migration.get_contract("Deleverage")

    log.h1("Deploying Auction House with Underscore safe-conversion preflight")
    migration.deploy(
        "AuctionHouse",
        hq,
    )

    log.h1("Deploying Deleverage with live legacy values and disabled payoff extras")
    migration.deploy(
        "Deleverage",
        hq,
        current_deleverage.minDeleverageBps(),
        current_deleverage.deleverageBuffer(),
        current_deleverage.deleverageCooldown(),
        current_deleverage.underscoreSafeSpreadBps(),
        10**15,  # full-payoff buffer
        100,  # overage bps
        0,  # dust threshold: disabled pending governance policy approval
        0,  # dust bps: disabled pending governance policy approval
    )
