from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    switchboard_alpha = migration.deploy(
        "SwitchboardAlpha",
        hq,
        migration.account(),
        migration.blueprint().PARAMS["PRICE_DESK_MIN_STALE_TIME"],
        migration.blueprint().PARAMS["PRICE_DESK_MAX_STALE_TIME"],
        migration.blueprint().PARAMS["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        migration.blueprint().PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
    )

    switchboard_charlie = migration.deploy(
        "SwitchboardCharlie",
        hq,
        migration.account(),
        migration.blueprint().PARAMS["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        migration.blueprint().PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
    )

    switchboard_echo = migration.deploy(
        "SwitchboardEcho",
        hq,
        migration.account(),
        migration.blueprint().PARAMS["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        migration.blueprint().PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
    )

    auction_house = migration.deploy(
        "AuctionHouse",
        hq,
    )

    bond_room = migration.deploy(
        "BondRoom",
        hq,
        migration.get_address("BondBooster"),
    )

    credit_engine = migration.deploy(
        "CreditEngine",
        hq,
    )

    deleverage = migration.deploy(
        "Deleverage",
        hq,
    )

    endaoment = migration.deploy(
        "Endaoment",
        hq,
        migration.blueprint().ADDYS["WETH"],
        migration.blueprint().ADDYS["ETH"],
    )

    endaoment_funds = migration.deploy(
        "EndaomentFunds",
        hq,
    )

    endaoment_psm = migration.deploy(
        "EndaomentPSM",
        hq,
        43_200,  # 1 day in blocks
        0,  # mint fee
        100_000 * 10**18,  # max interval mint
        0,  # redeem fee
        100_000 * 10**18,  # max interval redeem
        migration.blueprint().CORE_TOKENS["USDC"],
        13,  # usdc yield lego id
        '0xb33852cfd0c22647AAC501a6Af59Bc4210a686Bf',  # usdc yield vault token
    )

    lootbox = migration.deploy(
        "Lootbox",
        hq,
        43_200,  # 1 day in blocks
        100 * 10**18,  # deposit rewards amount
        100 * 10**18,  # yield bonus amount
    )

    pyth_prices = migration.deploy(
        "PythPrices",
        hq,
        migration.account(),
        migration.blueprint().ADDYS["PYTH_NETWORK"],
        migration.blueprint().PARAMS["PRICE_DESK_MIN_REG_TIMELOCK"],
        migration.blueprint().PARAMS["PRICE_DESK_MAX_REG_TIMELOCK"],
    )

    stork_prices = migration.deploy(
        "StorkPrices",
        hq,
        migration.account(),
        migration.blueprint().ADDYS["STORK_NETWORK"],
        migration.blueprint().PARAMS["PRICE_DESK_MIN_REG_TIMELOCK"],
        migration.blueprint().PARAMS["PRICE_DESK_MAX_REG_TIMELOCK"],
    )
