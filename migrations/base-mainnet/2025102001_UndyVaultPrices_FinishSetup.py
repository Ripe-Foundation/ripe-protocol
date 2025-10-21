from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS


def migrate(migration: Migration):

    undy_vault_prices = migration.get_contract("UndyVaultPrices")

    migration.execute(undy_vault_prices.setActionTimeLockAfterSetup)
    migration.execute(undy_vault_prices.relinquishGov)
