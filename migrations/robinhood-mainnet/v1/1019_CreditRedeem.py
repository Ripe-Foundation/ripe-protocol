from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Credit Redeem")

    credit_redeem = migration.deploy(
        "CreditRedeem",
        hq,
    )

    migration.execute(hq.startAddNewAddressToRegistry, credit_redeem, "Credit Redeem")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, credit_redeem)) == 19

    # no mint capability needed -- no green minting or burning happens here
