from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    blueprint = migration.blueprint()
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Vault Book")

    vault_book = migration.deploy(
        "VaultBook",
        hq,
        migration.account(),
        blueprint.PARAMS["VAULT_BOOK_MIN_REG_TIMELOCK"],
        blueprint.PARAMS["VAULT_BOOK_MAX_REG_TIMELOCK"],
    )

    stability_pool = migration.get_contract("StabilityPool")
    ripe_gov_vault = migration.get_contract("RipeGov")
    simple_erc20_vault = migration.get_contract("SimpleErc20")
    rebase_erc20_vault = migration.get_contract("RebaseErc20")

    migration.execute(vault_book.startAddNewAddressToRegistry, stability_pool, "Stability Pool")
    assert int(migration.execute(vault_book.confirmNewAddressToRegistry, stability_pool)) == 1

    migration.execute(vault_book.startAddNewAddressToRegistry, ripe_gov_vault, "Ripe Gov Vault")
    assert int(migration.execute(vault_book.confirmNewAddressToRegistry, ripe_gov_vault)) == 2

    migration.execute(vault_book.startAddNewAddressToRegistry, simple_erc20_vault, "Simple ERC20 Vault")
    assert int(migration.execute(vault_book.confirmNewAddressToRegistry, simple_erc20_vault)) == 3

    migration.execute(vault_book.startAddNewAddressToRegistry, rebase_erc20_vault, "Rebase ERC20 Vault")
    assert int(migration.execute(vault_book.confirmNewAddressToRegistry, rebase_erc20_vault)) == 4
