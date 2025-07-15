from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import EIGHTEEN_DECIMALS


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Bond Room")

    bond_booster = migration.deploy(
        "BondBooster",
        hq,
        1000 * EIGHTEEN_DECIMALS,  # _maxBoost
        100,                        # _maxUnits
    )

    migration.deploy(
        "BondRoom",
        hq,
        bond_booster,
    )
