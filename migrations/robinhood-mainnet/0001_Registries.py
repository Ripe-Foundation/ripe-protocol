from scripts.utils import log
from scripts.utils.ledger_deployment import validate_ledger_action_block_source
from scripts.utils.migration import Migration

from config.robinhood_launch import LEDGER_ACTION_BLOCK_SOURCE


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    defaults = migration.get_contract("DefaultsRobinhood")

    log.h1("Deploying Ledger")

    # The constructor stores and allowlists the source. The node-backed checks
    # below prove both the exact stored source and its live runtime behavior.
    ledger = migration.deploy(
        "Ledger",
        hq,
        defaults,
        LEDGER_ACTION_BLOCK_SOURCE,
    )
    expected_source = int(LEDGER_ACTION_BLOCK_SOURCE, 16)
    assert expected_source == 0x64, (
        "production action-block source must be ArbSys"
    )

    action_source, action_block = validate_ledger_action_block_source(
        migration,
        ledger.address,
        expected_source,
        allow_local_preview=False,
    )
    log.h2(f"Ledger ACTION_BLOCK_SOURCE: 0x{action_source:040x}")
    log.h2(f"ArbSys action block: {action_block}")

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
