from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import EIGHTEEN_DECIMALS


def migrate(migration: Migration):
    deployer = migration.account()
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

    migration.execute(hq.startAddNewAddressToRegistry, price_desk, "Price Desk")
    assert migration.execute(hq.confirmNewAddressToRegistry, price_desk) == 7

    # Set up chainlink feeds

    mock_usdc_feed = migration.deploy(
        "MockChainlinkFeed",
        1*EIGHTEEN_DECIMALS,
        deployer,
        label="MockUsdcFeed",
    )
    mock_btc_feed = migration.deploy(
        "MockChainlinkFeed",
        100_000*EIGHTEEN_DECIMALS,
        deployer,
        label="MockBtcFeed",
    )
    mock_weth_feed = migration.deploy(
        "MockChainlinkFeed",
        2_500*EIGHTEEN_DECIMALS,
        deployer,
        label="MockEthFeed",
    )

    # Deploy chainlink

    chainlink = migration.deploy(
        "Chainlink",
        hq,
        blueprint.PARAMS["PRICE_DESK_MIN_REG_TIMELOCK"],
        blueprint.PARAMS["PRICE_DESK_MAX_REG_TIMELOCK"],
        blueprint.ADDYS["WETH"],
        blueprint.ADDYS["ETH"],
        blueprint.ADDYS["BTC"],
        mock_weth_feed.address,
        mock_btc_feed.address,
    )

    migration.execute(chainlink.addNewPriceFeed, blueprint.ADDYS["USDC"], mock_usdc_feed.address)
    migration.execute(chainlink.confirmNewPriceFeed, blueprint.ADDYS["USDC"])

    migration.execute(chainlink.addNewPriceFeed, blueprint.ADDYS["CBBTC"], mock_btc_feed.address)
    migration.execute(chainlink.confirmNewPriceFeed, blueprint.ADDYS["CBBTC"])

    migration.execute(chainlink.setActionTimeLockAfterSetup)

    migration.execute(price_desk.startAddNewAddressToRegistry, chainlink, "Chainlink")
    migration.execute(price_desk.confirmNewAddressToRegistry, chainlink)

    # Set up Curve Prices

    curve_prices = migration.deploy(
        "CurvePrices",
        hq,
        blueprint.ADDYS["CURVE_ADDRESS_PROVIDER"],
        blueprint.PARAMS["PRICE_DESK_MIN_REG_TIMELOCK"],
        blueprint.PARAMS["PRICE_DESK_MAX_REG_TIMELOCK"],
    )
    migration.execute(price_desk.startAddNewAddressToRegistry, curve_prices, "Curve Prices")
    migration.execute(price_desk.confirmNewAddressToRegistry, curve_prices)

    # Add Green Prices
    green_token = migration.get_address("GreenToken")
    green_pool = migration.get_address("GreenPoool")
    migration.execute(curve_prices.addNewPriceFeed, green_token, green_pool)
    migration.execute(curve_prices.confirmNewPriceFeed, green_token)
    migration.execute(curve_prices.addNewPriceFeed, green_pool, green_pool)
    migration.execute(curve_prices.confirmNewPriceFeed, green_pool)

    # Add Ripe Prices
    ripe_token = migration.get_address("RipeToken")
    ripe_pool = migration.get_address("RipePoool")
    migration.execute(curve_prices.addNewPriceFeed, ripe_token, ripe_pool)
    migration.execute(curve_prices.confirmNewPriceFeed, ripe_token)
    migration.execute(curve_prices.addNewPriceFeed, ripe_pool, ripe_pool)
    migration.execute(curve_prices.confirmNewPriceFeed, ripe_pool)

    mock_s_green_price = migration.deploy(
        "MockSGreenPrice",
        migration.get_address("SavingsGreen"),
    )

    migration.execute(price_desk.startAddNewAddressToRegistry, mock_s_green_price, "Mock SavingsGreen Price")
    migration.execute(price_desk.confirmNewAddressToRegistry, mock_s_green_price)

    # finish registry setup
    migration.execute(price_desk.setRegistryTimeLockAfterSetup)
