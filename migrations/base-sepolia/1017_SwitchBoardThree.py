from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    blueprint = migration.blueprint()
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Switchboard Three")

    switchboard_three = migration.deploy(
        "SwitchboardThree",
        hq,
        blueprint.PARAMS["MIN_HQ_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_HQ_CHANGE_TIMELOCK"],
    )

    migration.execute(hq.startAddNewAddressToRegistry, switchboard_three, "Switchboard Three")
    assert migration.execute(hq.confirmNewAddressToRegistry, switchboard_three) == 17

    # switchboard three can modify mission control
    migration.execute(hq.initiateHqConfigChange, 17, False, False, True, True)
    migration.execute(hq.confirmHqConfigChange, 17)
