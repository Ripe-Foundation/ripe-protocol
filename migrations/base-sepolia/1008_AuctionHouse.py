from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Auction House")

    auction_house = migration.deploy(
        "AuctionHouse",
        hq,
    )

    migration.execute(hq.startAddNewAddressToRegistry, auction_house, "Auction House")
    assert migration.execute(hq.confirmNewAddressToRegistry, auction_house) == 8

    # auction house can mint green
    migration.execute(hq.initiateHqConfigChange, 8, True, False, False, False)
    migration.execute(hq.confirmHqConfigChange, 8)
