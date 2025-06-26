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
    switchboard_alpha = migration.deploy(
        "SwitchboardAlpha",
        hq,
        blueprint.PARAMS["PRICE_DESK_MIN_STALE_TIME"],
        blueprint.PARAMS["PRICE_DESK_MAX_STALE_TIME"],
        blueprint.PARAMS["MIN_HQ_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_HQ_CHANGE_TIMELOCK"]
    )
    migration.execute(switchboard.startAddNewAddressToRegistry, switchboard_alpha, "Switchboard Alpha")
    assert int(migration.execute(switchboard.confirmNewAddressToRegistry, switchboard_alpha)) == 1

    log.h1("Deploying Switchboard Bravo")
    switchboard_bravo = migration.deploy(
        "SwitchboardBravo",
        hq,
        blueprint.PARAMS["MIN_HQ_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_HQ_CHANGE_TIMELOCK"]
    )
    migration.execute(switchboard.startAddNewAddressToRegistry, switchboard_bravo, "Switchboard Bravo")
    assert int(migration.execute(switchboard.confirmNewAddressToRegistry, switchboard_bravo)) == 2

    log.h1("Deploying Switchboard Charlie")
    switchboard_charlie = migration.deploy(
        "SwitchboardCharlie",
        hq,
        blueprint.PARAMS["MIN_HQ_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_HQ_CHANGE_TIMELOCK"],
    )
    migration.execute(switchboard.startAddNewAddressToRegistry, switchboard_charlie, "Switchboard Charlie")
    assert int(migration.execute(switchboard.confirmNewAddressToRegistry, switchboard_charlie)) == 3

    log.h1("Deploying Switchboard Delta")
    switchboard_delta = migration.deploy(
        "SwitchboardDelta",
        hq,
        blueprint.PARAMS["MIN_HQ_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_HQ_CHANGE_TIMELOCK"],
    )
    migration.execute(switchboard.startAddNewAddressToRegistry, switchboard_delta, "Switchboard Delta")
    assert int(migration.execute(switchboard.confirmNewAddressToRegistry, switchboard_delta)) == 4

    migration.execute(hq.startAddNewAddressToRegistry, switchboard, "Switchboard")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, switchboard)) == 6

    migration.execute(hq.initiateHqConfigChange, 6, False, False, True)
    migration.execute(hq.confirmHqConfigChange, 6)
