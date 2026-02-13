from scripts.utils.migration import Migration
import boa


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    blueprint = migration.blueprint()

    vvv = "0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf"

    oweth = migration.deploy(
        "wsuperOETHbPrices",
        hq,
        blueprint.YIELD_TOKENS["MOONWELL_CBETH"],
        blueprint.YIELD_TOKENS['SUPER_OETH'],
        blueprint.YIELD_TOKENS['WRAPPED_SUPER_OETH'],
        vvv,
        blueprint.PARAMS["PRICE_DESK_MIN_REG_TIMELOCK"],
        blueprint.PARAMS["PRICE_DESK_MAX_REG_TIMELOCK"],
    )
