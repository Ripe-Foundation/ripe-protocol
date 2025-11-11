from scripts.utils.migration import Migration
import boa


def migrate(migration: Migration):
   hq = migration.get_contract("RipeHq")
   blueprint = migration.blueprint()
   migration.deploy(
        "wsuperOETHbPrices",
        hq,
        blueprint.YIELD_TOKENS['SUPER_OETH'],
        blueprint.YIELD_TOKENS['WRAPPED_SUPER_OETH'],
        blueprint.PARAMS["PRICE_DESK_MIN_REG_TIMELOCK"],
        blueprint.PARAMS["PRICE_DESK_MAX_REG_TIMELOCK"],
    )
   
