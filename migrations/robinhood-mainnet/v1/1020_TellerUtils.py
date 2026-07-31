from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Teller Utils")

    teller_utils = migration.deploy(
        "TellerUtils",
        hq,
    )

    migration.execute(hq.startAddNewAddressToRegistry, teller_utils, "Teller Utils")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, teller_utils)) == 20

    # no mint capability needed. Underscore getters and routes fail closed --
    # DefaultsRobinHood sets underscoreRegistry to the zero address.
