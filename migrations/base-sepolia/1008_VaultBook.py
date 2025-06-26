from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    blueprint = migration.blueprint()
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Vault Book")

    vault_book = migration.deploy(
        "VaultBook",
        hq,
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

    rebase_erc20_vault = migration.deploy(
        "RebaseErc20",
        hq,
    )

    migration.execute(vault_book.startAddNewAddressToRegistry, stability_pool, "Stability Pool")
    assert int(migration.execute(vault_book.confirmNewAddressToRegistry, stability_pool)) == 1

    migration.execute(vault_book.startAddNewAddressToRegistry, ripe_gov_vault, "Ripe Gov Vault")
    assert int(migration.execute(vault_book.confirmNewAddressToRegistry, ripe_gov_vault)) == 2

    migration.execute(vault_book.startAddNewAddressToRegistry, simple_erc20_vault, "Simple ERC20 Vault")
    assert int(migration.execute(vault_book.confirmNewAddressToRegistry, simple_erc20_vault)) == 3

    migration.execute(vault_book.startAddNewAddressToRegistry, rebase_erc20_vault, "Rebase ERC20 Vault")
    assert int(migration.execute(vault_book.confirmNewAddressToRegistry, rebase_erc20_vault)) == 4

    migration.execute(hq.startAddNewAddressToRegistry, vault_book, "Vault Book")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, vault_book)) == 8

    migration.execute(hq.initiateHqConfigChange, 8, False, True, False)
    migration.execute(hq.confirmHqConfigChange, 8)
