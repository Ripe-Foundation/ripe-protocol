from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    blueprint = migration.blueprint()

    deleverage = migration.deploy(
        "Deleverage",
        hq,
    )

    switchboard_delta = migration.deploy(
        "SwitchboardDelta",
        hq,
        ZERO_ADDRESS,
        blueprint.PARAMS["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
    )

    cur_undy_prices = migration.get_contract("UndyVaultPrices", "0x05d1b76544Ec15702C6F1bc087F0BD6Da23E90B0")

    undy_vault_prices = migration.deploy(
        "UndyVaultPrices",
        hq,
        migration.account(),
        blueprint.PARAMS["PRICE_DESK_MIN_REG_TIMELOCK"],
        blueprint.PARAMS["PRICE_DESK_MAX_REG_TIMELOCK"],
    )

    for vault in cur_undy_prices.getPricedAssets():
        print(vault)
        migration.execute(undy_vault_prices.addNewPriceFeed, vault)
        migration.execute(undy_vault_prices.confirmNewPriceFeed, vault)

    migration.execute(undy_vault_prices.relinquishGov)
