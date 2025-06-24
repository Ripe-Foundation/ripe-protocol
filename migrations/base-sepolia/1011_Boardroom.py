from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Boardroom")

    boardroom = migration.deploy(
        "Boardroom",
        hq,
    )

    migration.execute(hq.startAddNewAddressToRegistry, boardroom, "Boardroom")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, boardroom)) == 11
