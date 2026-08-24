"""Promote VaultMigrator only after RipeHq id-25 readback.

The H-06 runner that rejected this legacy API has been removed. Execution is
now gated by MigrationRunner, which refuses a history that already holds a
``current-manifest.json`` unless an explicit ``--start-timestamp`` is given.
"""

from scripts.utils import log
from scripts.utils.migration import Migration

from config.robinhood_launch import (
    VAULT_MIGRATOR_SHOULD_PAUSE,
    ZERO_ADDRESS,
)


VAULT_MIGRATOR_ID = 25
VAULT_MIGRATOR_CANDIDATE = "VaultMigratorCandidate2026082402"


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    log.h1("Verifying RipeHq slot 25 and promoting VaultMigrator")
    migration.promote_candidate(
        "VaultMigrator",
        VAULT_MIGRATOR_CANDIDATE,
        hq,
        VAULT_MIGRATOR_ID,
        expected_source_path="contracts/core/VaultMigrator.vy",
        registry_name="RipeHq",
        expected_constructor_args=(
            hq,
            VAULT_MIGRATOR_SHOULD_PAUSE,
            ZERO_ADDRESS,
        ),
    )
