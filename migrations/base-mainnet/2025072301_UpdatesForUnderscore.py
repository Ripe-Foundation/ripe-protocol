from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    blueprint = migration.blueprint()

    price_desk = migration.deploy(
        "PriceDesk",
        hq,
        migration.account(),
        blueprint.ADDYS["ETH"],
        blueprint.PARAMS["PRICE_DESK_MIN_REG_TIMELOCK"],
        blueprint.PARAMS["PRICE_DESK_MAX_REG_TIMELOCK"],
    )

    # Set up Chainlink Prices

    chainlink = migration.deploy(
        "ChainlinkPrices",
        hq,
        migration.account(),
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

    migration.execute(
        chainlink.addNewPriceFeed,
        blueprint.CORE_TOKENS["CBBTC"],
        blueprint.ADDYS["CHAINLINK_CBBTC_USD"]
    )
    migration.execute(chainlink.confirmNewPriceFeed, blueprint.CORE_TOKENS["CBBTC"])

    migration.execute(chainlink.addNewPriceFeed, blueprint.CORE_TOKENS["USOL"], blueprint.ADDYS["CHAINLINK_SOL_USD"])
    migration.execute(chainlink.confirmNewPriceFeed, blueprint.CORE_TOKENS["USOL"])

    migration.execute(
        chainlink.addNewPriceFeed,
        blueprint.CORE_TOKENS["CBDOGE"],
        blueprint.ADDYS["CHAINLINK_DOGE_USD"]
    )
    migration.execute(chainlink.confirmNewPriceFeed, blueprint.CORE_TOKENS["CBDOGE"])

    # Set up Pyth Prices

    pyth_prices = migration.deploy(
        "PythPrices",
        hq,
        migration.account(),
        blueprint.ADDYS["PYTH_NETWORK"],
        blueprint.PARAMS["PRICE_DESK_MIN_REG_TIMELOCK"],
        blueprint.PARAMS["PRICE_DESK_MAX_REG_TIMELOCK"],
    )

    # Set up Stork Prices

    stork_prices = migration.deploy(
        "StorkPrices",
        hq,
        migration.account(),
        blueprint.ADDYS["STORK_NETWORK"],
        blueprint.PARAMS["PRICE_DESK_MIN_REG_TIMELOCK"],
        blueprint.PARAMS["PRICE_DESK_MAX_REG_TIMELOCK"],
    )

    # Set price sources

    migration.execute(price_desk.startAddNewAddressToRegistry, chainlink, "Chainlink")
    assert int(migration.execute(price_desk.confirmNewAddressToRegistry, chainlink)) == 1

    curve_prices = migration.get_contract("CurvePrices")
    migration.execute(price_desk.startAddNewAddressToRegistry, curve_prices, "Curve Prices")
    assert int(migration.execute(price_desk.confirmNewAddressToRegistry, curve_prices)) == 2

    bluechip_yield_prices = migration.get_contract("BlueChipYieldPrices")
    migration.execute(price_desk.startAddNewAddressToRegistry, bluechip_yield_prices, "BlueChip Yield Prices")
    assert int(migration.execute(price_desk.confirmNewAddressToRegistry, bluechip_yield_prices)) == 3

    migration.execute(price_desk.startAddNewAddressToRegistry, pyth_prices, "Pyth Prices")
    assert int(migration.execute(price_desk.confirmNewAddressToRegistry, pyth_prices)) == 4

    migration.execute(price_desk.startAddNewAddressToRegistry, stork_prices, "Stork Prices")
    assert int(migration.execute(price_desk.confirmNewAddressToRegistry, stork_prices)) == 5

    switchboard_alpha = migration.deploy(
        "SwitchboardAlpha",
        hq,
        migration.account(),
        blueprint.PARAMS["PRICE_DESK_MIN_STALE_TIME"],
        blueprint.PARAMS["PRICE_DESK_MAX_STALE_TIME"],
        blueprint.PARAMS["MIN_HQ_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_HQ_CHANGE_TIMELOCK"]
    )

    migration.execute(switchboard_alpha.setUnderscoreRegistry, blueprint.ADDYS["UNDERSCORE_REGISTRY"])
    migration.execute(
        switchboard_alpha.setPriorityStabVaults,
        [
            (1, migration.get_address("GreenPool")),
            (1, migration.get_address("SavingsGreen"))
        ]
    )
    migration.execute(
        switchboard_alpha.setPriorityLiqAssetVaults,
        [
            (3, blueprint.CORE_TOKENS["USDC"]),
            (3, blueprint.CORE_TOKENS["CBBTC"]),
            (3, blueprint.CORE_TOKENS["WETH"]),
            (3, blueprint.CORE_TOKENS["USOL"]),
            (3, blueprint.CORE_TOKENS["CBDOGE"]),
        ]
    )
    migration.execute(
        switchboard_alpha.setPriorityPriceSourceIds,
        [1, 3, 4, 5, 2]
    )

    # Set time locks after setup
    migration.execute(switchboard_alpha.setActionTimeLockAfterSetup)
    migration.execute(switchboard_alpha.relinquishGov)

    migration.execute(chainlink.setActionTimeLockAfterSetup)
    migration.execute(chainlink.relinquishGov)

    migration.execute(pyth_prices.setActionTimeLockAfterSetup)
    migration.execute(pyth_prices.relinquishGov)

    migration.execute(stork_prices.setActionTimeLockAfterSetup)
    migration.execute(stork_prices.relinquishGov)

    migration.execute(price_desk.setRegistryTimeLockAfterSetup)
    migration.execute(price_desk.relinquishGov)

    teller = migration.deploy(
        "Teller",
        hq,
        True,
    )

    endaoment = migration.deploy(
        "Endaoment",
        hq,
        blueprint.ADDYS["WETH"],
        blueprint.ADDYS["ETH"],
    )
