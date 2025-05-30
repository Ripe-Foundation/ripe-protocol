from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import EIGHTEEN_DECIMALS


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Ledger")

    ledger = migration.deploy(
        "Ledger",
        hq,
        100 * (1_000_000 * EIGHTEEN_DECIMALS),  # 100 million
    )

    migration.execute(hq.startAddNewAddressToRegistry, ledger, "Ledger")
    migration.execute(hq.confirmNewAddressToRegistry, ledger)
