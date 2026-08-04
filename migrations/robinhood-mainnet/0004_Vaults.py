from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS

from config.robinhood_launch import approved

# VaultBook ids 1-3, in this exact order.
VAULTS = ("StabilityPool", "RipeGov", "SimpleErc20")


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying VaultBook")

    vault_book = migration.deploy(
        "VaultBook",
        hq,
        ZERO_ADDRESS,
        approved("Deployment.DP-05.timelocks.AddressRegistry.minDelay"),
        approved("Deployment.DP-05.timelocks.AddressRegistry.maxDelay"),
    )

    for index, name in enumerate(VAULTS, start=1):
        log.h2(f"Deploying {name}")
        vault = migration.deploy(name, hq)
        migration.execute(vault_book.startAddNewAddressToRegistry, vault, name)
        assert int(
            migration.execute(vault_book.confirmNewAddressToRegistry, vault)
        ) == index

    migration.execute(hq.startAddNewAddressToRegistry, vault_book, "VaultBook")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, vault_book)) == 8
