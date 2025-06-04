from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    blueprint = migration.blueprint()
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Switchboard Two")

    switchboard_two = migration.deploy(
        "SwitchboardTwo",
        hq,
        blueprint.PARAMS["MIN_HQ_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_HQ_CHANGE_TIMELOCK"],
    )

    migration.execute(hq.startAddNewAddressToRegistry, switchboard_two, "Switchboard Two")
    assert migration.execute(hq.confirmNewAddressToRegistry, switchboard_two) == 16

    # switchboard two can modify mission control
    migration.execute(hq.initiateHqConfigChange, 16, False, False, True, True)
    migration.execute(hq.confirmHqConfigChange, 16)
