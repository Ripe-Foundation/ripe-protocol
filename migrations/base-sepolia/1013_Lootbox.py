from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Lootbox")

    lootbox = migration.deploy(
        "Lootbox",
        hq,
    )

    migration.execute(hq.startAddNewAddressToRegistry, lootbox, "Lootbox")
    assert migration.execute(hq.confirmNewAddressToRegistry, lootbox) == 13

    # lootbox can mint ripe
    migration.execute(hq.initiateHqConfigChange, 13, False, True, False, False)
    migration.execute(hq.confirmHqConfigChange, 13)
