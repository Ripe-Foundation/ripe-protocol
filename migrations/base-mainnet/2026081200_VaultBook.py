from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    blueprint = migration.blueprint()
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Vault Book")

    old_vb = migration.get_contract("VaultBook", '0xB758e30C14825519b895Fd9928d5d8748A71a944')

    vault_book = migration.deploy(
        "VaultBook",
        hq,
        migration.account(),
        blueprint.PARAMS["VAULT_BOOK_MIN_REG_TIMELOCK"],
        blueprint.PARAMS["VAULT_BOOK_MAX_REG_TIMELOCK"],
    )

    for i in range(1, old_vb.numAddrs()):
        addr = old_vb.addrInfo(i)
        cur_addr = vault_book.addrInfo(i)
        if cur_addr.addr != addr.addr or cur_addr.description != addr.description:
            print(f"Adding {addr.addr}, {addr.description} to vault book registry")
            if (vault_book.pendingNewAddr(addr.addr).initiatedBlock == 0):
                migration.execute(vault_book.startAddNewAddressToRegistry, addr.addr, addr.description)
            migration.execute(vault_book.confirmNewAddressToRegistry, addr.addr)

    vault_book.relinquishGov()
