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

    simple_erc20_vault = migration.deploy(
        "SimpleErc20",
        hq,
    )

    rebase_erc20_vault = migration.deploy(
        "RebaseErc20",
        hq,
    )

    stability_pool = migration.deploy(
        "StabilityPool",
        hq,
    )

    migration.execute(vault_book.startAddNewAddressToRegistry, stability_pool, "Stability Pool")
    migration.execute(vault_book.confirmNewAddressToRegistry, stability_pool)

    migration.execute(vault_book.startAddNewAddressToRegistry, simple_erc20_vault, "Simple ERC20 Vault")
    migration.execute(vault_book.confirmNewAddressToRegistry, simple_erc20_vault)

    migration.execute(vault_book.startAddNewAddressToRegistry, rebase_erc20_vault, "Rebase ERC20 Vault")
    migration.execute(vault_book.confirmNewAddressToRegistry, rebase_erc20_vault)

    migration.execute(vault_book.setRegistryTimeLockAfterSetup)

    migration.execute(hq.startAddNewAddressToRegistry, vault_book, "Vault Book")
    assert migration.execute(hq.confirmNewAddressToRegistry, vault_book) == 7
