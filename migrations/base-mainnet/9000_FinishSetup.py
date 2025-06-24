from scripts.utils.migration import Migration


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    assert migration.execute(hq.setRegistryTimeLockAfterSetup)
    assert migration.execute(hq.finishRipeHqSetup, migration.blueprint().ADDYS["GOVERNANCE"])
