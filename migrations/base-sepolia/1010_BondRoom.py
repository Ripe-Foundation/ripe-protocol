from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Bond Room")

    bond_room = migration.deploy(
        "BondRoom",
        hq,
    )

    migration.execute(hq.startAddNewAddressToRegistry, bond_room, "Bond Room")
    assert migration.execute(hq.confirmNewAddressToRegistry, bond_room) == 10
