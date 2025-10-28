from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Underscore Vault")

    underscore_vault = migration.deploy(
        "SimpleErc20",
        hq,
        label="Underscore Vault",
    )
