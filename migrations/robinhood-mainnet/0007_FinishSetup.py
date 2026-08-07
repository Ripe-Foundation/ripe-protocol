from scripts.utils import log
from scripts.utils.migration import Migration

from config.robinhood_launch import GOVERNANCE


ACTION_TIMELOCK_COMPONENTS = (
    "SwitchboardAlpha",
    "SwitchboardBravo",
    "SwitchboardCharlie",
    "SwitchboardDelta",
    "SwitchboardEcho",
    "ChainlinkPrices",
    "CurvePrices",
    "HumanResources",
)

REGISTRY_TIMELOCK_COMPONENTS = (
    "Switchboard",
    "PriceDesk",
    "VaultBook",
    "RipeHq",
)


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    log.h1("Setting time locks after setup")

    for name in ACTION_TIMELOCK_COMPONENTS:
        component = migration.get_contract(name)
        assert int(component.actionTimeLock()) == 0, f"{name} timelock already set"
        selected = int(component.minActionTimeLock())
        assert selected != 0, f"{name} minimum timelock is zero"
        assert migration.execute(component.setActionTimeLockAfterSetup, selected)
        actual = int(component.actionTimeLock())
        assert actual == selected, f"{name} timelock readback mismatch"
        log.h2(f"{name}: actionTimeLock 0 -> {actual}")

    for name in REGISTRY_TIMELOCK_COMPONENTS:
        registry = migration.get_contract(name)
        assert int(registry.registryChangeTimeLock()) == 0, f"{name} timelock already set"
        selected = int(registry.minRegistryTimeLock())
        assert selected != 0, f"{name} minimum timelock is zero"
        assert migration.execute(registry.setRegistryTimeLockAfterSetup, selected)
        actual = int(registry.registryChangeTimeLock())
        assert actual == selected, f"{name} timelock readback mismatch"
        log.h2(f"{name}: registryChangeTimeLock 0 -> {actual}")

    log.h1("Handing governance to the Safe")

    # Irreversible. After this the deployer governs nothing: the departments
    # were constructed holding zero local governance, so RipeHq is the only
    # authority that moves, and it moves once.
    assert migration.execute(hq.finishRipeHqSetup, GOVERNANCE)
