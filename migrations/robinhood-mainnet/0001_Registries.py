from scripts.utils import log
from scripts.utils.migration import Migration

from config.robinhood_launch import LEDGER_ACTION_BLOCK_SOURCE


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    defaults = migration.get_contract("DefaultsRobinhood")

    log.h1("Deploying Ledger")

    # LEDGER_ACTION_BLOCK_SOURCE is ArbSys: on this L2 `block.number` is the L1
    # ancestor estimate and repeats across child blocks. The constructor calls
    # arbBlockNumber() and reverts if it cannot decode the result, so a wrong
    # value fails here rather than silently weakening the one-action-per-block
    # guard.
    ledger = migration.deploy(
        "Ledger",
        hq,
        defaults,
        LEDGER_ACTION_BLOCK_SOURCE,
    )
    migration.execute(hq.startAddNewAddressToRegistry, ledger, "Ledger")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, ledger)) == 4

    log.h1("Deploying MissionControl")

    mission_control = migration.deploy(
        "MissionControl",
        hq,
        defaults,
    )
    migration.execute(
        hq.startAddNewAddressToRegistry, mission_control, "MissionControl"
    )
    assert int(
        migration.execute(hq.confirmNewAddressToRegistry, mission_control)
    ) == 5
