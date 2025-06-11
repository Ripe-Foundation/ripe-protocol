from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import EIGHTEEN_DECIMALS


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Ledger")

    ledger = migration.deploy(
        "Ledger",
        hq,
        # TODO: get actual values here
        100 * (1_000_000 * EIGHTEEN_DECIMALS),  # 100 million
        100 * (1_000_000 * EIGHTEEN_DECIMALS),  # 100 million
        100 * (1_000_000 * EIGHTEEN_DECIMALS),  # 100 million
    )

    migration.execute(hq.startAddNewAddressToRegistry, ledger, "Ledger")
    assert migration.execute(hq.confirmNewAddressToRegistry, ledger) == 4
