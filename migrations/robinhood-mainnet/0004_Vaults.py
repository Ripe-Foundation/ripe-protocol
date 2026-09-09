from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS

from config.robinhood_launch import REGISTRY_MAX_DELAY, REGISTRY_MIN_DELAY


# MissionControl and the Base deployment bind these two semantic ids.
STABILITY_POOL_VAULT_ID = 1
RIPE_GOV_VAULT_ID = 2

# VaultBook ids 1-3, in this exact order.
VAULTS = ("StabilityPool", "RipeGov", "SimpleErc20")


def _verify_vault_bindings(
    vault_book,
    mission_control,
    stability_pool,
    ripe_gov,
    savings_green,
):
    assert int(vault_book.getRegId(stability_pool)) == STABILITY_POOL_VAULT_ID
    assert int(vault_book.getRegId(ripe_gov)) == RIPE_GOV_VAULT_ID
    assert vault_book.getAddr(STABILITY_POOL_VAULT_ID) == stability_pool.address
    assert vault_book.getAddr(RIPE_GOV_VAULT_ID) == ripe_gov.address

    # Type/capability probes make a swapped registration fail even when both
    # addresses are otherwise valid Vault implementations.
    stability_pool.totalClaimableBalances(savings_green)
    assert not stability_pool.isPaused(), "StabilityPool unexpectedly paused"
    ripe_gov.totalGovPoints()
    assert not ripe_gov.isPaused(), "RipeGov unexpectedly paused"

    assert int(mission_control.preferredStabVaultId()) == STABILITY_POOL_VAULT_ID
    assert mission_control.isStabVaultId(STABILITY_POOL_VAULT_ID)
    assert int(mission_control.coreRipeGovVaultId()) == RIPE_GOV_VAULT_ID


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying VaultBook")

    vault_book = migration.deploy(
        "VaultBook",
        hq,
        ZERO_ADDRESS,
        REGISTRY_MIN_DELAY,
        REGISTRY_MAX_DELAY,
    )

    for index, name in enumerate(VAULTS, start=1):
        log.h2(f"Deploying {name}")
        vault = migration.deploy(name, hq)
        migration.execute(vault_book.startAddNewAddressToRegistry, vault, name)
        assert int(
            migration.execute(vault_book.confirmNewAddressToRegistry, vault)
        ) == index

    stability_pool = migration.get_contract("StabilityPool")
    ripe_gov = migration.get_contract("RipeGov")
    mission_control = migration.get_contract("MissionControl")
    savings_green = migration.get_contract("SavingsGreen")

    _verify_vault_bindings(
        vault_book,
        mission_control,
        stability_pool,
        ripe_gov,
        savings_green,
    )

    migration.execute(hq.startAddNewAddressToRegistry, vault_book, "VaultBook")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, vault_book)) == 8
