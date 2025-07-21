from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    blueprint = migration.blueprint()

    log.h1("Deploying Switchboard Delta")
    switchboard_delta = migration.deploy(
        "SwitchboardDelta",
        hq,
        migration.account(),
        blueprint.PARAMS["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
    )

    migration.execute(switchboard_delta.setActionTimeLockAfterSetup)
    migration.execute(switchboard_delta.relinquishGov)
