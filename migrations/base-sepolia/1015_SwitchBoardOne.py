from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    blueprint = migration.blueprint()
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Switchboard One")

    switchboard_one = migration.deploy(
        "SwitchboardOne",
        hq,
        blueprint.PARAMS["PRICE_DESK_MIN_STALE_TIME"],
        blueprint.PARAMS["PRICE_DESK_MAX_STALE_TIME"],
        blueprint.PARAMS["MIN_HQ_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_HQ_CHANGE_TIMELOCK"]
    )

    migration.execute(hq.startAddNewAddressToRegistry, switchboard_one, "Switchboard One")
    assert migration.execute(hq.confirmNewAddressToRegistry, switchboard_one) == 15

    # switchboard one can set token blacklists and modify mission control
    migration.execute(hq.initiateHqConfigChange, 15, False, False, True, True)
    migration.execute(hq.confirmHqConfigChange, 15)
