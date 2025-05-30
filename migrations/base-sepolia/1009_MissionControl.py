from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    blueprint = migration.blueprint()
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Mission Control")

    mission_control_data = migration.deploy(
        "MissionControlData",
        hq,
    )

    mission_control = migration.deploy(
        "MissionControl",
        hq,
        mission_control_data,
        blueprint.PARAMS["PRICE_DESK_MIN_STALE_TIME"],
        blueprint.PARAMS["PRICE_DESK_MAX_STALE_TIME"],
    )

    migration.execute(hq.startAddNewAddressToRegistry, mission_control, "Mission Control")
    migration.execute(hq.confirmNewAddressToRegistry, mission_control)

    # mission control can set token blacklists
    migration.execute(hq.initiateHqConfigChange, 9, False, False, True)
    migration.execute(hq.confirmHqConfigChange, 9)
