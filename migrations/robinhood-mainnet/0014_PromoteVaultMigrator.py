"""Promote VaultMigrator only after RipeHq id-25 readback.

The H-06 Robinhood runner intentionally rejects this legacy API. Convert this
postcondition to a typed ``MIGRATION_STAGE`` action before execution.
"""

from scripts.utils import log
from scripts.utils.migration import Migration


VAULT_MIGRATOR_ID = 25
VAULT_MIGRATOR_CANDIDATE = "VaultMigratorCandidate0013"


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    log.h1("Verifying RipeHq slot 25 and promoting VaultMigrator")
    migration.promote_candidate(
        "VaultMigrator",
        VAULT_MIGRATOR_CANDIDATE,
        hq,
        VAULT_MIGRATOR_ID,
    )
