from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Credit Engine")

    credit_engine = migration.deploy(
        "CreditEngine",
        hq,
    )

    migration.execute(hq.startAddNewAddressToRegistry, credit_engine, "Credit Engine")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, credit_engine)) == 13

    # credit engine can mint green
    migration.execute(hq.initiateHqConfigChange, 13, True, False, False)
    migration.execute(hq.confirmHqConfigChange, 13)
