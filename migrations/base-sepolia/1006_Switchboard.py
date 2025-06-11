from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    blueprint = migration.blueprint()

    log.h1("Deploying Switchboard")

    switchboard = migration.deploy(
        "Switchboard",
        hq,
        blueprint.PARAMS["MIN_HQ_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_HQ_CHANGE_TIMELOCK"],
    )

    log.h1("Deploying Switchboard Alpha")
    switchboard_one = migration.deploy(
        "SwitchboardAlpha",
        hq,
        blueprint.PARAMS["PRICE_DESK_MIN_STALE_TIME"],
        blueprint.PARAMS["PRICE_DESK_MAX_STALE_TIME"],
        blueprint.PARAMS["MIN_HQ_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_HQ_CHANGE_TIMELOCK"]
    )
    migration.execute(switchboard.startAddNewAddressToRegistry, switchboard_one, "Switchboard Alpha")
    assert migration.execute(switchboard.confirmNewAddressToRegistry, switchboard_one) == 1

    log.h1("Deploying Switchboard Bravo")
    switchboard_two = migration.deploy(
        "SwitchboardBravo",
        hq,
        blueprint.PARAMS["MIN_HQ_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_HQ_CHANGE_TIMELOCK"]
    )
    migration.execute(switchboard.startAddNewAddressToRegistry, switchboard_two, "Switchboard Bravo")
    assert migration.execute(switchboard.confirmNewAddressToRegistry, switchboard_two) == 2

    log.h1("Deploying Switchboard Charlie")
    switchboard_three = migration.deploy(
        "SwitchboardCharlie",
        hq,
        blueprint.PARAMS["MIN_HQ_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_HQ_CHANGE_TIMELOCK"],
    )
    migration.execute(switchboard.startAddNewAddressToRegistry, switchboard_three, "Switchboard Charlie")
    assert migration.execute(switchboard.confirmNewAddressToRegistry, switchboard_three) == 3

    log.h1("Deploying Switchboard Delta")
    switchboard_four = migration.deploy(
        "SwitchboardDelta",
        hq,
        blueprint.PARAMS["MIN_HQ_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_HQ_CHANGE_TIMELOCK"],
    )
    migration.execute(switchboard.startAddNewAddressToRegistry, switchboard_four, "Switchboard Delta")
    assert migration.execute(switchboard.confirmNewAddressToRegistry, switchboard_four) == 4

    migration.execute(hq.startAddNewAddressToRegistry, switchboard, "Switchboard")
    assert migration.execute(hq.confirmNewAddressToRegistry, switchboard) == 6

    migration.execute(hq.initiateHqConfigChange, 6, False, False, True)
    migration.execute(hq.confirmHqConfigChange, 6)
