from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    blueprint = migration.blueprint()

    log.h1("Deploying Teller")

    # P-H04-421: Teller launches paused. Unpausing is a separate governed step.
    teller = migration.deploy(
        "Teller",
        hq,
        blueprint.PARAMS["TELLER_SHOULD_PAUSE"],
    )

    migration.execute(hq.startAddNewAddressToRegistry, teller, "Teller")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, teller)) == 17
