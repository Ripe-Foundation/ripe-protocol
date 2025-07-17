from scripts.utils.migration import Migration


def migrate(migration: Migration):
    sb_alpha = migration.get_contract("SwitchboardAlpha")
    sb_delta = migration.get_contract("SwitchboardDelta")

    # Set time locks after setup
    migration.execute(sb_alpha.setActionTimeLockAfterSetup)
    migration.execute(sb_delta.setActionTimeLockAfterSetup)

    migration.execute(sb_alpha.relinquishGov)
    migration.execute(sb_delta.relinquishGov)
