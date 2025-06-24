from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import EIGHTEEN_DECIMALS


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Ledger")

    ledger = migration.deploy(
        "Ledger",
        hq,
        migration.get_contract("DefaultsBaseSepolia"),
    )

    migration.execute(hq.startAddNewAddressToRegistry, ledger, "Ledger")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, ledger)) == 4
