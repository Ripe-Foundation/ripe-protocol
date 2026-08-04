from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS

from config.robinhood_launch import (
    BLUECHIP_AAVE_PROVIDER,
    BLUECHIP_COMPOUND_CONFIGURATOR,
    BLUECHIP_EULER_FACTORIES,
    BLUECHIP_FLUID_RESOLVER,
    BLUECHIP_MOONWELL_COMPTROLLER,
    BLUECHIP_MORPHO_FACTORIES,
    PRICE_CHANGE_MAX_TIMELOCK,
    PRICE_CHANGE_MIN_TIMELOCK,
    PRICE_MAX_TIMELOCK,
    PRICE_MIN_TIMELOCK,
    REGISTRY_MAX_DELAY,
    REGISTRY_MIN_DELAY,
    STALE_WINDOW_DEFAULT,
    STALE_WINDOW_USDG,
    address,
)


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    green_token = migration.get_contract("GreenToken")
    savings_green = migration.get_contract("SavingsGreen")

    log.h1("Deploying PriceDesk")

    price_desk = migration.deploy(
        "PriceDesk",
        hq,
        ZERO_ADDRESS,
        address("NATIVE_ETH_SENTINEL"),
        REGISTRY_MIN_DELAY,
        REGISTRY_MAX_DELAY,
    )

    log.h1("Deploying ChainlinkPrices")

    chainlink = migration.deploy(
        "ChainlinkPrices",
        hq,
        ZERO_ADDRESS,
        PRICE_MIN_TIMELOCK,
        PRICE_MAX_TIMELOCK,
        address("WETH"),
        address("NATIVE_ETH_SENTINEL"),
        address("BTC_SENTINEL"),
        address("CHAINLINK_ETH_USD"),
        address("CHAINLINK_BTC_USD"),
        STALE_WINDOW_DEFAULT,
    )

    # USDG prices through Chainlink only. Every other price route depends on
    # this being live, including the GREEN pool route and the SteakHouse vault.
    usdg = address("USDG")
    migration.execute(
        chainlink.addNewPriceFeed,
        usdg,
        address("CHAINLINK_USDG_USD"),
        STALE_WINDOW_USDG,
        False,
        False,
    )
    migration.execute(chainlink.confirmNewPriceFeed, usdg)

    # PriceDesk ids 1 and 2. CurvePrices MUST be id 2: Teller, Endaoment and
    # CreditEngine all hard-code CURVE_PRICES_ID = 2.
    migration.execute(price_desk.startAddNewAddressToRegistry, chainlink, "ChainlinkPrices")
    assert int(migration.execute(price_desk.confirmNewAddressToRegistry, chainlink)) == 1

    log.h1("Deploying CurvePrices")
    curve_prices = migration.deploy(
        "CurvePrices",
        hq,
        ZERO_ADDRESS,
        address("CURVE_ADDRESS_PROVIDER"),
        green_token,
        savings_green,
        PRICE_CHANGE_MIN_TIMELOCK,
        PRICE_CHANGE_MAX_TIMELOCK,
    )
    migration.execute(price_desk.startAddNewAddressToRegistry, curve_prices, "CurvePrices")
    assert int(migration.execute(price_desk.confirmNewAddressToRegistry, curve_prices)) == 2

    # PriceDesk must be registered in RipeHq before any feed is added: the price
    # sources resolve PriceDesk through RipeHq when validating a new feed.
    migration.execute(hq.startAddNewAddressToRegistry, price_desk, "PriceDesk")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, price_desk)) == 7

    # log.h1("Deploying BlueChipYieldPrices")

    # # Only Morpho V2 exists on Robinhood; the other six registries are zero and
    # # fail closed, because Vyper checks extcodesize before an external call.
    # blue_chip = migration.deploy(
    #     "BlueChipYieldPrices",
    #     hq,
    #     ZERO_ADDRESS,
    #     PRICE_MIN_TIMELOCK,
    #     PRICE_MAX_TIMELOCK,
    #     BLUECHIP_MORPHO_FACTORIES,
    #     BLUECHIP_EULER_FACTORIES,
    #     BLUECHIP_FLUID_RESOLVER,
    #     BLUECHIP_COMPOUND_CONFIGURATOR,
    #     BLUECHIP_MOONWELL_COMPTROLLER,
    #     BLUECHIP_AAVE_PROVIDER,
    #     address("MORPHO_V2_FACTORY"),
    # )
    # migration.execute(
    #     price_desk.startAddNewAddressToRegistry, blue_chip, "BlueChipYieldPrices"
    # )
    # assert int(
    #     migration.execute(price_desk.confirmNewAddressToRegistry, blue_chip)
    # ) == 3
