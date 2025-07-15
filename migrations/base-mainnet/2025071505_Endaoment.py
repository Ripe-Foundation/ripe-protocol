from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Endaoment")

    migration.deploy(
        "Endaoment",
        hq,
        migration.blueprint().ADDYS["WETH"],
        migration.blueprint().ADDYS["ETH"],
    )
