"""Stage a zero-delay VaultBook containing only the currently registered vaults."""

from scripts.utils import log
from scripts.utils.migration import Migration

ZERO = "0x" + "00" * 20
HQ = "0x6162df1b329e157479f8f1407e888260e0ec3d2b"


def address(value):
    return str(getattr(value, "address", value)).lower()


def migrate(migration: Migration):
    assert migration.chain() == "base-mainnet"
    hq = migration.get_contract("RipeHq")
    assert address(hq) == HQ
    active = [hq.getAddr(i) for i in range(1, int(hq.numAddrs()))]
    old = migration.get_contract("VaultBook", hq.getAddr(8))

    log.h1("1. Read the five existing vaults, preserving IDs and descriptions")
    assert old.numAddrs() == 6, "review changed live vault topology"
    rows = [tuple(old.addrInfo(i)) for i in range(1, 6)]
    for i, row in enumerate(rows, 1):
        assert address(row[0]) != ZERO and old.getRegId(row[0]) == i
        assert old.isValidRegId(i)
    pool = migration.get_contract("StabilityPool", rows[0][0])
    assert address(pool.getRipeHq()) == address(hq)

    log.h1("2. Deploy VaultBook with the current StabilityPool compatibility binding")
    book = migration.deploy(
        "VaultBook", hq.address, migration.account(),
        old.minRegistryTimeLock(), old.maxRegistryTimeLock(), pool.address,
        label="VaultBookBaseDepartments20260921",
    )
    for i, row in enumerate(rows, 1):
        migration.execute(book.startAddNewAddressToRegistry, row[0], row[3])
        migration.execute(book.confirmNewAddressToRegistry, row[0])
        assert address(book.getAddr(i)) == address(row[0])
        assert book.getRegId(row[0]) == i and book.isValidRegId(i)
        assert book.addrInfo(i)[3] == row[3]

    log.h1("3. Relinquish setup governance without enabling a timelock")
    migration.execute(book.relinquishGov)
    assert address(book.governance()) == ZERO
    assert book.registryChangeTimeLock() == 0
    assert book.numAddrs() == 6 and book.getNumAddrs() == 5
    assert address(book.LEGACY_POOL()) == address(pool)
    assert book.hasStabilityPoolInterface(pool.address, pool.vaultAssets(1), ZERO)
    assert [hq.getAddr(i) for i in range(1, int(hq.numAddrs()))] == active
    assert [tuple(old.addrInfo(i)) for i in range(1, 6)] == rows
    log.info(f"STAGED VaultBook (HQ slot 8): {book.address}")
    log.info("Existing vaults 1-5 retained. No new vaults, HQ proposals, or funds movements.")
