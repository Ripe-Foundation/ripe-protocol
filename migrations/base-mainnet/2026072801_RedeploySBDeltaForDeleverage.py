from scripts.utils import log
from scripts.utils.migration import Migration


# Before scheduling this migration, execute it through scripts/migrate.py on the
# same pinned Base-mainnet fork as the preceding core-contract migration and
# retain the MigrationRunner log with the review evidence.
def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    blueprint = migration.blueprint()

    # Keep this deployment separate from the core-contract migration so the
    # governance surface and four new parameter ceilings receive their own review.
    # Governance handoff and configuration transactions are executed separately
    # from the Safe; this migration only deploys the contract.
    log.h1("Deploying Switchboard Delta for Deleverage configuration")
    migration.deploy(
        "SwitchboardDelta",
        hq,
        migration.account(),
        blueprint.PARAMS["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
    )
