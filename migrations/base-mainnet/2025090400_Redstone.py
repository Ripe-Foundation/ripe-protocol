from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS

def migrate(migration: Migration):
   hq = migration.get_contract("RipeHq")
   blueprint = migration.blueprint()
   redstone = migration.deploy(
        "RedStone",
        hq,
        migration.account(),
        blueprint.ADDYS['ETH'],
        blueprint.PARAMS["PRICE_DESK_MIN_REG_TIMELOCK"],
        blueprint.PARAMS["PRICE_DESK_MAX_REG_TIMELOCK"],
    )
   migration.execute(redstone.setActionTimeLockAfterSetup)
   migration.execute(redstone.relinquishGov)