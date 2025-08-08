from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import EIGHTEEN_DECIMALS


def migrate(migration: Migration):
    blueprint = migration.blueprint()
    hq = migration.get_contract("RipeHq")

    # Set up Curve Prices

    curve_prices = migration.deploy(
        "CurvePrices",
        hq,
        migration.account(),
        blueprint.ADDYS["CURVE_ADDRESS_PROVIDER"],
        migration.get_address("GreenToken"),
        migration.get_address("SavingsGreen"),
        blueprint.PARAMS["PRICE_DESK_MIN_REG_TIMELOCK"],
        blueprint.PARAMS["PRICE_DESK_MAX_REG_TIMELOCK"],
    )

    green_token = migration.get_address("GreenToken")
    green_pool = migration.get_address("GreenPool")
    migration.execute(curve_prices.addNewPriceFeed, green_token, green_pool)
    migration.execute(curve_prices.confirmNewPriceFeed, green_token)
    migration.execute(curve_prices.addNewPriceFeed, green_pool, green_pool)
    migration.execute(curve_prices.confirmNewPriceFeed, green_pool)

    action_id = migration.execute(
        curve_prices.setGreenRefPoolConfig,
        green_pool,
        10,  # _maxNumSnapshots
        60_00,  # _dangerTrigger
        43_200,  # ONE DAY
        75_00,  # _stabilizerAdjustWeight
        5_000_000 * EIGHTEEN_DECIMALS,  # _stabilizerMaxPoolDebt
    )
    assert bool(migration.execute(curve_prices.confirmGreenRefPoolConfig, action_id))

    migration.execute(curve_prices.setActionTimeLockAfterSetup)
    migration.execute(curve_prices.relinquishGov)
