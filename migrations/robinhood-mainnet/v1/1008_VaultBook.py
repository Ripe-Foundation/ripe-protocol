from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS


# Vault ids are consumed by DefaultsRobinHood.assetConfigs (1 = stability pool,
# 2 = ripe gov, 3 = simple erc20), so the registration order here is load-bearing.
#
# RebaseErc20 (canonical id 4) is omitted: it is only needed for the Stock Token
# path, which Track 8 holds blocked, and no launch asset references vault id 4.
def migrate(migration: Migration):
    blueprint = migration.blueprint()
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Vault Book")

    vault_book = migration.deploy(
        "VaultBook",
        hq,
        ZERO_ADDRESS,
        blueprint.PARAMS["VAULT_BOOK_MIN_REG_TIMELOCK"],
        blueprint.PARAMS["VAULT_BOOK_MAX_REG_TIMELOCK"],
    )

    stability_pool = migration.deploy(
        "StabilityPool",
        hq,
    )

    ripe_gov_vault = migration.deploy(
        "RipeGov",
        hq,
    )

    simple_erc20_vault = migration.deploy(
        "SimpleErc20",
        hq,
    )

    migration.execute(vault_book.startAddNewAddressToRegistry, stability_pool, "Stability Pool")
    assert int(migration.execute(vault_book.confirmNewAddressToRegistry, stability_pool)) == 1

    migration.execute(vault_book.startAddNewAddressToRegistry, ripe_gov_vault, "Ripe Gov Vault")
    assert int(migration.execute(vault_book.confirmNewAddressToRegistry, ripe_gov_vault)) == 2

    migration.execute(vault_book.startAddNewAddressToRegistry, simple_erc20_vault, "Simple ERC20 Vault")
    assert int(migration.execute(vault_book.confirmNewAddressToRegistry, simple_erc20_vault)) == 3

    migration.execute(hq.startAddNewAddressToRegistry, vault_book, "Vault Book")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, vault_book)) == 8

    # vault book can mint ripe
    migration.execute(hq.initiateHqConfigChange, 8, False, True, False)
    migration.execute(hq.confirmHqConfigChange, 8)
