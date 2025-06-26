from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Ledger")

    ledger = migration.deploy(
        "Ledger",
        hq,
        migration.get_contract("DefaultsBase"),
    )

    migration.execute(hq.startAddNewAddressToRegistry, ledger, "Ledger")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, ledger)) == 4
