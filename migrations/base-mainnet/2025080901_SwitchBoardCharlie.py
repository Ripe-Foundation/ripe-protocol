from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import EIGHTEEN_DECIMALS


def migrate(migration: Migration):
    switchboard_charlie = migration.deploy(
        "SwitchboardCharlie",
        migration.get_contract("RipeHq"),
        migration.account(),
        3_600,  # 2 hours
        migration.blueprint().PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
    )

    migration.execute(switchboard_charlie.setActionTimeLockAfterSetup)
    migration.execute(switchboard_charlie.relinquishGov)
