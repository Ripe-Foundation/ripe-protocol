from scripts.utils.migration import Migration
import boa


def migrate(migration: Migration):
   hq = migration.get_contract("RipeHq")
   migration.deploy(
        "Teller",
        hq,
        True,
        migration.blueprint().PARAMS["CURVE_PRICES_ID"],
    )
   migration.deploy(
        "CreditEngine",
        hq,
        migration.blueprint().PARAMS["CURVE_PRICES_ID"],
    )
