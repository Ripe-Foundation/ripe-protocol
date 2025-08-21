from scripts.utils.migration import Migration
import boa


def migrate(migration: Migration):
   hq = migration.get_contract("RipeHq")
   aero_prices = migration.deploy(
        "AeroRipePrices",
        hq,
        migration.account(),
        migration.get_address("RipePoolAero"),
        migration.get_address("RipeToken"),
        migration.blueprint().PARAMS["PRICE_DESK_MIN_REG_TIMELOCK"],
        migration.blueprint().PARAMS["PRICE_DESK_MAX_REG_TIMELOCK"],
   )
   migration.execute(aero_prices.setActionTimeLockAfterSetup)
   migration.execute(aero_prices.relinquishGov)
   



