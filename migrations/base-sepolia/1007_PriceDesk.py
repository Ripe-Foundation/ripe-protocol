from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import EIGHTEEN_DECIMALS


def migrate(migration: Migration):
    blueprint = migration.blueprint()
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Price Desk")

    price_desk = migration.deploy(
        "PriceDesk",
        hq,
        blueprint.ADDYS["ETH"],
        blueprint.PARAMS["PRICE_DESK_MIN_REG_TIMELOCK"],
        blueprint.PARAMS["PRICE_DESK_MAX_REG_TIMELOCK"],
    )

    # Deploy chainlink

    chainlink = migration.deploy(
        "ChainlinkPrices",
        hq,
        blueprint.PARAMS["PRICE_DESK_MIN_REG_TIMELOCK"],
        blueprint.PARAMS["PRICE_DESK_MAX_REG_TIMELOCK"],
        blueprint.ADDYS["WETH"],
        blueprint.ADDYS["ETH"],
        blueprint.ADDYS["BTC"],
        blueprint.ADDYS["CHAINLINK_ETH_USD"],
        blueprint.ADDYS["CHAINLINK_BTC_USD"],
    )

    migration.execute(chainlink.addNewPriceFeed, blueprint.CORE_TOKENS["USDC"], blueprint.ADDYS["CHAINLINK_USDC_USD"])
    migration.execute(chainlink.confirmNewPriceFeed, blueprint.CORE_TOKENS["USDC"])

    migration.execute(chainlink.addNewPriceFeed,
                      blueprint.CORE_TOKENS["CBBTC"], blueprint.ADDYS["CHAINLINK_CBBTC_USD"])
    migration.execute(chainlink.confirmNewPriceFeed, blueprint.CORE_TOKENS["CBBTC"])

    migration.execute(price_desk.startAddNewAddressToRegistry, chainlink, "Chainlink")
    assert int(migration.execute(price_desk.confirmNewAddressToRegistry, chainlink)) == 1

    # Set up Curve Prices

    curve_prices = migration.deploy(
        "CurvePrices",
        hq,
        blueprint.ADDYS["CURVE_ADDRESS_PROVIDER"],
        blueprint.PARAMS["PRICE_DESK_MIN_REG_TIMELOCK"],
        blueprint.PARAMS["PRICE_DESK_MAX_REG_TIMELOCK"],
    )
    migration.execute(price_desk.startAddNewAddressToRegistry, curve_prices, "Curve Prices")
    assert int(migration.execute(price_desk.confirmNewAddressToRegistry, curve_prices)) == 2

    # # Set up BlueChip Yield Prices

    # bluechip_yield_prices = migration.deploy(
    #     "BlueChipYieldPrices",
    #     hq,
    #     blueprint.PARAMS["PRICE_DESK_MIN_REG_TIMELOCK"],
    #     blueprint.PARAMS["PRICE_DESK_MAX_REG_TIMELOCK"],
    #     [blueprint.ADDYS["MORPHO_FACTORY"], blueprint.ADDYS["MORPHO_FACTORY_LEGACY"]],
    #     [blueprint.ADDYS["EULER_EVAULT_FACTORY"], blueprint.ADDYS["EULER_EARN_FACTORY"]],
    #     blueprint.ADDYS["FLUID_RESOLVER"],
    #     blueprint.ADDYS["COMPOUND_V3_CONFIGURATOR"],
    #     blueprint.ADDYS["MOONWELL_COMPTROLLER"],
    #     blueprint.ADDYS["AAVE_V3_ADDRESS_PROVIDER"],
    # )
    # migration.execute(price_desk.startAddNewAddressToRegistry, bluechip_yield_prices, "BlueChip Yield Prices")
    # migration.execute(price_desk.confirmNewAddressToRegistry, bluechip_yield_prices)

    # # Set up Pyth Prices

    # pyth_prices = migration.deploy(
    #     "PythPrices",
    #     hq,
    #     blueprint.ADDYS["PYTH_NETWORK"],
    #     blueprint.PARAMS["PRICE_DESK_MIN_REG_TIMELOCK"],
    #     blueprint.PARAMS["PRICE_DESK_MAX_REG_TIMELOCK"],
    # )
    # migration.execute(price_desk.startAddNewAddressToRegistry, pyth_prices, "Pyth Prices")
    # migration.execute(price_desk.confirmNewAddressToRegistry, pyth_prices)

    # # Set up Stork Prices

    # stork_prices = migration.deploy(
    #     "StorkPrices",
    #     hq,
    #     blueprint.ADDYS["STORK_NETWORK"],
    #     blueprint.PARAMS["PRICE_DESK_MIN_REG_TIMELOCK"],
    #     blueprint.PARAMS["PRICE_DESK_MAX_REG_TIMELOCK"],
    # )
    # migration.execute(price_desk.startAddNewAddressToRegistry, stork_prices, "Stork Prices")
    # migration.execute(price_desk.confirmNewAddressToRegistry, stork_prices)

    # finish registry setup
    migration.execute(hq.startAddNewAddressToRegistry, price_desk, "Price Desk")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, price_desk)) == 7
