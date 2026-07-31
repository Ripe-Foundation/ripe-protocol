from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    blueprint = migration.blueprint()

    log.h1("Deploying Human Resources")

    human_resources = migration.deploy(
        "HumanResources",
        hq,
        blueprint.PARAMS["HR_MIN_CONFIG_TIMELOCK"],
        blueprint.PARAMS["HR_MAX_CONFIG_TIMELOCK"],
    )

    migration.execute(hq.startAddNewAddressToRegistry, human_resources, "Human Resources")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, human_resources)) == 15

    # HR is registered to hold canonical id 15 but stays inactive: no RIPE mint
    # capability while there are no contributors. DefaultsRobinHood sets
    # maxCompensation = 0, so no vesting agreement can be created either.
    # Grant canMintRipe here only if active HR is approved.
    migration.execute(hq.initiateHqConfigChange, 15, False, False, False)
    migration.execute(hq.confirmHqConfigChange, 15)
