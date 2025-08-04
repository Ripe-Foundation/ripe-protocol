from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Teller")

    migration.deploy(
        "Teller",
        hq,
        True,
    )
