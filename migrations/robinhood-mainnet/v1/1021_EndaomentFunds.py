from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Endaoment Funds")

    endaoment_funds = migration.deploy(
        "EndaomentFunds",
        hq,
    )

    migration.execute(hq.startAddNewAddressToRegistry, endaoment_funds, "Endaoment Funds")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, endaoment_funds)) == 21

    # local custody only -- no mint capability, no external or yield destinations
