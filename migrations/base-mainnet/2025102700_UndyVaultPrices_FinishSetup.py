from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS


def migrate(migration: Migration):

    blueprint = migration.blueprint()
    undy_vault_prices = migration.get_contract("UndyVaultPrices")

    migration.execute(
        undy_vault_prices.addNewPriceFeed,
        blueprint.YIELD_TOKENS["UNDY_AERO"]
    )
    migration.execute(undy_vault_prices.confirmNewPriceFeed, blueprint.YIELD_TOKENS["UNDY_AERO"])

    migration.execute(
        undy_vault_prices.addNewPriceFeed,
        blueprint.YIELD_TOKENS["UNDY_EURC"]
    )
    migration.execute(undy_vault_prices.confirmNewPriceFeed, blueprint.YIELD_TOKENS["UNDY_EURC"])

    migration.execute(undy_vault_prices.setActionTimeLockAfterSetup)
    migration.execute(undy_vault_prices.relinquishGov)
