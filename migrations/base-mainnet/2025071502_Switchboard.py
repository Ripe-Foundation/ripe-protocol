from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    blueprint = migration.blueprint()

    log.h1("Deploying Switchboard")

    switchboard = migration.deploy(
        "Switchboard",
        hq,
        migration.account(),
        blueprint.PARAMS["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
    )

    log.h1("Deploying Switchboard Alpha")
    switchboard_alpha = migration.deploy(
        "SwitchboardAlpha",
        hq,
        migration.account(),
        blueprint.PARAMS["PRICE_DESK_MIN_STALE_TIME"],
        blueprint.PARAMS["PRICE_DESK_MAX_STALE_TIME"],
        blueprint.PARAMS["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"]
    )

    migration.execute(switchboard_alpha.setUnderscoreRegistry, ZERO_ADDRESS)
    migration.execute(
        switchboard_alpha.setGlobalDebtLimits,
        10 * EIGHTEEN_DECIMALS,  # per user debt limit
        1000 * EIGHTEEN_DECIMALS,  # global debt limit
        1 * EIGHTEEN_DECIMALS,  # min debt amount
        100  # num allowed borrowers
    )

    migration.execute(switchboard.startAddNewAddressToRegistry, switchboard_alpha, "Switchboard Alpha")
    assert int(migration.execute(switchboard.confirmNewAddressToRegistry, switchboard_alpha)) == 1

    log.h1("Deploying Switchboard Bravo")
    switchboard_bravo = migration.deploy(
        "SwitchboardBravo",
        hq,
        migration.account(),
        blueprint.PARAMS["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"]
    )
    migration.execute(switchboard.startAddNewAddressToRegistry, switchboard_bravo, "Switchboard Bravo")
    assert int(migration.execute(switchboard.confirmNewAddressToRegistry, switchboard_bravo)) == 2

    log.h1("Deploying Switchboard Charlie")
    switchboard_charlie = migration.deploy(
        "SwitchboardCharlie",
        hq,
        migration.account(),
        3_600,  # 2 hours
        blueprint.PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
    )
    migration.execute(switchboard.startAddNewAddressToRegistry, switchboard_charlie, "Switchboard Charlie")
    assert int(migration.execute(switchboard.confirmNewAddressToRegistry, switchboard_charlie)) == 3

    log.h1("Deploying Switchboard Delta")
    switchboard_delta = migration.deploy(
        "SwitchboardDelta",
        hq,
        migration.account(),
        blueprint.PARAMS["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
    )
    migration.execute(switchboard.startAddNewAddressToRegistry, switchboard_delta, "Switchboard Delta")
    assert int(migration.execute(switchboard.confirmNewAddressToRegistry, switchboard_delta)) == 4
