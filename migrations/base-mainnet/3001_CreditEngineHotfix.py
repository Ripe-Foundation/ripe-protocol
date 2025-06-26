from scripts.utils.migration import Migration


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    migration.deploy(
        "CreditEngine",
        hq,
    )
