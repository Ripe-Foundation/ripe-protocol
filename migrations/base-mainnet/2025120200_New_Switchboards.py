from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    blueprint = migration.blueprint()

    switchboard = migration.deploy(
        "Switchboard",
        hq,
        migration.account(),
        blueprint.PARAMS["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
    )

    switchboard_alpha = migration.deploy(
        "SwitchboardAlpha",
        hq,
        migration.account(),
        blueprint.PARAMS["PRICE_DESK_MIN_STALE_TIME"],
        blueprint.PARAMS["PRICE_DESK_MAX_STALE_TIME"],
        blueprint.PARAMS["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
    )

    switchboard_bravo = migration.deploy(
        "SwitchboardBravo",
        hq,
        migration.account(),
        blueprint.PARAMS["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"]
    )

    switchboard_charlie = migration.deploy(
        "SwitchboardCharlie",
        hq,
        migration.account(),
        blueprint.PARAMS["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
    )

    switchboard_delta = migration.deploy(
        "SwitchboardDelta",
        hq,
        migration.account(),
        blueprint.PARAMS["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
    )

    switchboard_echo = migration.deploy(
        "SwitchboardEcho",
        hq,
        migration.account(),
        blueprint.PARAMS["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
    )

    migration.execute(switchboard.startAddNewAddressToRegistry, switchboard_alpha, "Switchboard Alpha")
    assert int(migration.execute(switchboard.confirmNewAddressToRegistry, switchboard_alpha)) == 1

    migration.execute(switchboard.startAddNewAddressToRegistry, switchboard_bravo, "Switchboard Bravo")
    assert int(migration.execute(switchboard.confirmNewAddressToRegistry, switchboard_bravo)) == 2

    migration.execute(switchboard.startAddNewAddressToRegistry, switchboard_charlie, "Switchboard Charlie")
    assert int(migration.execute(switchboard.confirmNewAddressToRegistry, switchboard_charlie)) == 3

    migration.execute(switchboard.startAddNewAddressToRegistry, switchboard_delta, "Switchboard Delta")
    assert int(migration.execute(switchboard.confirmNewAddressToRegistry, switchboard_delta)) == 4

    migration.execute(switchboard.startAddNewAddressToRegistry, switchboard_echo, "Switchboard Echo")
    assert int(migration.execute(switchboard.confirmNewAddressToRegistry, switchboard_echo)) == 5

    migration.execute(switchboard.relinquishGov)
    migration.execute(switchboard_alpha.relinquishGov)
    migration.execute(switchboard_bravo.relinquishGov)
    migration.execute(switchboard_charlie.relinquishGov)
    migration.execute(switchboard_delta.relinquishGov)
    migration.execute(switchboard_echo.relinquishGov)
