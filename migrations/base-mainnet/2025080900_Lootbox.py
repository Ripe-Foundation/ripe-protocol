from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import EIGHTEEN_DECIMALS


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    migration.deploy(
        "Lootbox",
        hq,
    )
