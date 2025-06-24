from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    blueprint = migration.blueprint()

    log.h1("Deploying Human Resources")

    human_resources = migration.deploy(
        "HumanResources",
        hq,
        blueprint.PARAMS["MIN_HQ_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_HQ_CHANGE_TIMELOCK"],
    )

    migration.execute(hq.startAddNewAddressToRegistry, human_resources, "Human Resources")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, human_resources)) == 15

    migration.execute(hq.initiateHqConfigChange, 15, False, True, False)
    migration.execute(hq.confirmHqConfigChange, 15)
