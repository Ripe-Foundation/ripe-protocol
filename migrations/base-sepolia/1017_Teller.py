from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Teller")

    teller = migration.deploy(
        "Teller",
        hq,
    )

    migration.execute(hq.startAddNewAddressToRegistry, teller, "Teller")
    assert migration.execute(hq.confirmNewAddressToRegistry, teller) == 17
