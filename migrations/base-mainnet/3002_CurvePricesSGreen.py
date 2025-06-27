from scripts.utils.migration import Migration


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    blueprint = migration.blueprint()
    migration.deploy(
        "CurvePrices",
        hq,
        blueprint.ADDYS["CURVE_ADDRESS_PROVIDER"],
        migration.get_address("GreenToken"),
        migration.get_address("SavingsGreen"),
        blueprint.PARAMS["PRICE_DESK_MIN_REG_TIMELOCK"],
        blueprint.PARAMS["PRICE_DESK_MAX_REG_TIMELOCK"],
    )
