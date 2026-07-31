from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS


# NOTE on temp gov: every contract below is deployed with NO local governance.
#
# LocalGov.__init__ asserts `_initialGov != hqGov`, and during a fresh deploy
# RipeHq governance IS the deployer -- so passing the deployer here reverts.
# Deploying with ZERO_ADDRESS is also the safer posture: RipeHq governance is
# the sole governor from block zero, the deployer still configures everything
# through it, and there is no dangling local gov left to relinquish.
def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    blueprint = migration.blueprint()

    log.h1("Deploying Switchboard")

    switchboard = migration.deploy(
        "Switchboard",
        hq,
        ZERO_ADDRESS,
        blueprint.PARAMS["RIPE_HQ_MIN_REG_TIMELOCK"],
        blueprint.PARAMS["RIPE_HQ_MAX_REG_TIMELOCK"],
    )

    log.h1("Deploying Switchboard Alpha")
    switchboard_alpha = migration.deploy(
        "SwitchboardAlpha",
        hq,
        ZERO_ADDRESS,
        blueprint.PARAMS["PRICE_DESK_MIN_STALE_TIME"],
        blueprint.PARAMS["PRICE_DESK_MAX_STALE_TIME"],
        blueprint.PARAMS["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
    )
    migration.execute(switchboard.startAddNewAddressToRegistry, switchboard_alpha, "Switchboard Alpha")
    assert int(migration.execute(switchboard.confirmNewAddressToRegistry, switchboard_alpha)) == 1

    log.h1("Deploying Switchboard Bravo")
    switchboard_bravo = migration.deploy(
        "SwitchboardBravo",
        hq,
        ZERO_ADDRESS,
        blueprint.PARAMS["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
    )
    migration.execute(switchboard.startAddNewAddressToRegistry, switchboard_bravo, "Switchboard Bravo")
    assert int(migration.execute(switchboard.confirmNewAddressToRegistry, switchboard_bravo)) == 2

    log.h1("Deploying Switchboard Charlie")
    switchboard_charlie = migration.deploy(
        "SwitchboardCharlie",
        hq,
        ZERO_ADDRESS,
        blueprint.PARAMS["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
    )
    migration.execute(switchboard.startAddNewAddressToRegistry, switchboard_charlie, "Switchboard Charlie")
    assert int(migration.execute(switchboard.confirmNewAddressToRegistry, switchboard_charlie)) == 3

    log.h1("Deploying Switchboard Delta")
    switchboard_delta = migration.deploy(
        "SwitchboardDelta",
        hq,
        ZERO_ADDRESS,
        blueprint.PARAMS["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
    )
    migration.execute(switchboard.startAddNewAddressToRegistry, switchboard_delta, "Switchboard Delta")
    assert int(migration.execute(switchboard.confirmNewAddressToRegistry, switchboard_delta)) == 4

    log.h1("Deploying Switchboard Echo")
    switchboard_echo = migration.deploy(
        "SwitchboardEcho",
        hq,
        ZERO_ADDRESS,
        blueprint.PARAMS["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
    )
    migration.execute(switchboard.startAddNewAddressToRegistry, switchboard_echo, "Switchboard Echo")
    assert int(migration.execute(switchboard.confirmNewAddressToRegistry, switchboard_echo)) == 5

    migration.execute(hq.startAddNewAddressToRegistry, switchboard, "Switchboard")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, switchboard)) == 6

    # switchboard can set token blacklist
    migration.execute(hq.initiateHqConfigChange, 6, False, False, True)
    migration.execute(hq.confirmHqConfigChange, 6)
