from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS


# Before scheduling this migration, execute it through scripts/migrate.py on the
# same pinned Base-mainnet fork as the preceding core-contract migration and
# retain the MigrationRunner log with the review evidence.
def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    blueprint = migration.blueprint()

    # Keep this deployment separate from the core-contract migration so the
    # governance surface and four new parameter ceilings receive their own review.
    #
    # Deploy with no local governance: RipeHq governance is the sole governor from
    # block zero, so there is no handoff and nothing to relinquish. Taking local gov
    # here would leave the deployer EOA able to initiate and execute config actions
    # in the same block, since actionTimeLock is 0 on a fresh deploy. Registration
    # in RipeHq and all configuration transactions are done separately from the Safe.
    log.h1("Deploying Switchboard Delta for Deleverage configuration")
    migration.deploy(
        "SwitchboardDelta",
        hq,
        ZERO_ADDRESS,
        blueprint.PARAMS["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
    )
