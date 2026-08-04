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
    address,
    approved,
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
        approved("Deployment.DP-05.timelocks.AddressRegistry.minDelay"),
        approved("Deployment.DP-05.timelocks.AddressRegistry.maxDelay"),
    )

    log.h1("Deploying ChainlinkPrices")

    chainlink = migration.deploy(
        "ChainlinkPrices",
        hq,
        ZERO_ADDRESS,
        approved("Deployment.DP-05.timelocks.Chainlink.minTimeLock"),
        approved("Deployment.DP-05.timelocks.Chainlink.maxTimeLock"),
        address("WETH"),
        address("NATIVE_ETH_SENTINEL"),
        address("BTC_SENTINEL"),
        approved("Deployment.DP-23.external.chainlink.ethUsdFeed"),
        approved("Deployment.DP-23.external.chainlink.btcUsdFeed"),
        approved("Deployment.DP-17.staleWindows.chainlinkDefault"),
    )

    # USDG prices through Chainlink only. Every other price route depends on
    # this being live, including the GREEN pool route and the SteakHouse vault.
    usdg = address("USDG")
    migration.execute(
        chainlink.addNewPriceFeed,
        usdg,
        approved("Deployment.DP-23.external.chainlink.usdgUsdFeed"),
        approved("Deployment.DP-17.staleWindows.usdgCeiling"),
        False,
        False,
    )
    migration.execute(chainlink.confirmNewPriceFeed, usdg)

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

    # PriceDesk ids 1 and 2. CurvePrices MUST be id 2: Teller, Endaoment and
    # CreditEngine all hard-code CURVE_PRICES_ID = 2.
    migration.execute(price_desk.startAddNewAddressToRegistry, chainlink, "ChainlinkPrices")
    assert int(migration.execute(price_desk.confirmNewAddressToRegistry, chainlink)) == 1
    migration.execute(price_desk.startAddNewAddressToRegistry, curve_prices, "CurvePrices")
    assert int(migration.execute(price_desk.confirmNewAddressToRegistry, curve_prices)) == 2

    # PriceDesk must be registered in RipeHq before any feed is added: the price
    # sources resolve PriceDesk through RipeHq when validating a new feed.
    migration.execute(hq.startAddNewAddressToRegistry, price_desk, "PriceDesk")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, price_desk)) == 7

    log.h1("Deploying BlueChipYieldPrices")

    # Only Morpho V2 exists on Robinhood; the other six registries are zero and
    # fail closed, because Vyper checks extcodesize before an external call.
    blue_chip = migration.deploy(
        "BlueChipYieldPrices",
        hq,
        ZERO_ADDRESS,
        approved("Deployment.DP-05.timelocks.Chainlink.minTimeLock"),
        approved("Deployment.DP-05.timelocks.Chainlink.maxTimeLock"),
        BLUECHIP_MORPHO_FACTORIES,
        BLUECHIP_EULER_FACTORIES,
        BLUECHIP_FLUID_RESOLVER,
        BLUECHIP_COMPOUND_CONFIGURATOR,
        BLUECHIP_MOONWELL_COMPTROLLER,
        BLUECHIP_AAVE_PROVIDER,
        approved("Deployment.DP-23.external.blueChipYield.morphoV2Factory"),
    )
    migration.execute(
        price_desk.startAddNewAddressToRegistry, blue_chip, "BlueChipYieldPrices"
    )
    assert int(
        migration.execute(price_desk.confirmNewAddressToRegistry, blue_chip)
    ) == 3
