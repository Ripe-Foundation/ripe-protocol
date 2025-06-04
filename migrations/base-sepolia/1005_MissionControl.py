from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Mission Control")

    mission_control = migration.deploy(
        "MissionControl",
        hq,
    )

    migration.execute(hq.startAddNewAddressToRegistry, mission_control, "Mission Control")
    assert migration.execute(hq.confirmNewAddressToRegistry, mission_control) == 5
