from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Endaoment")

    endaoment = migration.deploy(
        "Endaoment",
        hq,
    )

    migration.execute(hq.startAddNewAddressToRegistry, endaoment, "Endaoment")
    assert migration.execute(hq.confirmNewAddressToRegistry, endaoment) == 12
