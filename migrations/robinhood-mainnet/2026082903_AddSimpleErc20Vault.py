"""Deploy and register a second SimpleErc20 vault on Robinhood.

This is additive: VaultBook id 3 and the canonical ``SimpleErc20`` manifest
record remain untouched. The new vault is stored as ``SimpleErc20Secondary``
and the migration prints the two governance calls that register it as id 4.
"""

from scripts.utils import log
from scripts.utils.migration import Migration


RIPE_HQ = "0xD4e82AE1De673bba3B53386A2D2C630AE6630940"
VAULT_BOOK = "0x559E53F42b68b4995732Dba4aF300796761DBC19"
CURRENT_SIMPLE_ERC20 = "0x4F89C94636995eF20d40d5592bA2585348bE6D53"

CURRENT_SIMPLE_ERC20_ID = 3
NEW_SIMPLE_ERC20_ID = 4
NEW_VAULT_LABEL = "SimpleErc20Secondary"
NEW_VAULT_DESCRIPTION = "SimpleErc20 2"


def migrate(migration: Migration):
    log.h1("1. Checking the current VaultBook")

    hq = migration.get_contract("RipeHq", RIPE_HQ)
    vault_book = migration.get_contract("VaultBook", VAULT_BOOK)

    assert address(hq.getAddr(8)) == address(vault_book)
    assert int(vault_book.registryChangeTimeLock()) == 0
    assert int(vault_book.numAddrs()) == NEW_SIMPLE_ERC20_ID
    assert address(vault_book.getAddr(CURRENT_SIMPLE_ERC20_ID)) == address(
        CURRENT_SIMPLE_ERC20
    )
    log.h1("2. Deploying the additional SimpleErc20 vault")

    new_vault = migration.deploy(
        "SimpleErc20",
        hq,
        label=NEW_VAULT_LABEL,
    )

    assert address(new_vault) != address(CURRENT_SIMPLE_ERC20)
    assert int(vault_book.getRegId(new_vault)) == 0

    log.h1("3. VaultBook registration for the Safe")
    log.info(f'const vaultBook = c.Ripe_RH_VaultBook.at("{VAULT_BOOK}")')
    log.info("")
    log.info(
        f'await vaultBook.startAddNewAddressToRegistry("{new_vault.address}", '
        f'"{NEW_VAULT_DESCRIPTION}")'
    )
    log.info(
        f'await vaultBook.confirmNewAddressToRegistry("{new_vault.address}")'
    )
    log.info("")
    log.info(
        f"// Expected: id {NEW_SIMPLE_ERC20_ID}; existing id "
        f"{CURRENT_SIMPLE_ERC20_ID} is unchanged."
    )


def address(value):
    return str(getattr(value, "address", value)).lower()
