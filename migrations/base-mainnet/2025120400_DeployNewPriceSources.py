from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    blueprint = migration.blueprint()

    old_chainlink = migration.get_contract("ChainlinkPrices")
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
        60 * 60 * 24,  # default stale time
    )
    for asset in (old_chainlink.getPricedAssets()):
        new_feed = chainlink.feedConfig(asset)
        if new_feed.feed != ZERO_ADDRESS:
            continue
        addr = old_chainlink.feedConfig(asset)
        print(addr)
        migration.execute(chainlink.addNewPriceFeed, asset, addr.feed,
                          addr.staleTime, addr.needsEthToUsd, addr.needsBtcToUsd)
        migration.execute(chainlink.confirmNewPriceFeed, asset)

    undy_vault_prices = migration.deploy(
        "UndyVaultPrices",
        hq,
        migration.account(),
        blueprint.PARAMS["PRICE_DESK_MIN_REG_TIMELOCK"],
        blueprint.PARAMS["PRICE_DESK_MAX_REG_TIMELOCK"],
    )
    vaults = [
        '0xb33852cfd0c22647aac501a6af59bc4210a686bf',  # undy USDC
        '0x02981db1a99a14912b204437e7a2e02679b57668',  # undy ETH
        '0x3fb0fc9d3ddd543ad1b748ed2286a022f4638493',  # undy BTC
        '0x1cb8dab80f19fc5aca06c2552aecd79015008ea8',  # undy EURC
        '0x96f1a7ce331f40afe866f3b707c223e377661087'  # undy AERO
    ]
    for vault in vaults:
        print(vault)
        migration.execute(undy_vault_prices.addNewPriceFeed, vault)
        migration.execute(undy_vault_prices.confirmNewPriceFeed, vault)

    pyth = migration.deploy(
        "PythPrices",
        hq,
        migration.account(),
        blueprint.ADDYS["PYTH_NETWORK"],
        blueprint.PARAMS["PRICE_DESK_MIN_REG_TIMELOCK"],
        blueprint.PARAMS["PRICE_DESK_MAX_REG_TIMELOCK"],
    )

    redstone = migration.deploy(
        "RedStone",
        hq,
        migration.account(),
        blueprint.ADDYS['ETH'],
        blueprint.PARAMS["PRICE_DESK_MIN_REG_TIMELOCK"],
        blueprint.PARAMS["PRICE_DESK_MAX_REG_TIMELOCK"],
    )

    stork = migration.deploy(
        "StorkPrices",
        hq,
        migration.account(),
        blueprint.ADDYS["STORK_NETWORK"],
        blueprint.PARAMS["PRICE_DESK_MIN_REG_TIMELOCK"],
        blueprint.PARAMS["PRICE_DESK_MAX_REG_TIMELOCK"],
    )

    migration.execute(chainlink.relinquishGov)
    migration.execute(undy_vault_prices.relinquishGov)
    migration.execute(pyth.relinquishGov)
    migration.execute(redstone.relinquishGov)
    migration.execute(stork.relinquishGov)
