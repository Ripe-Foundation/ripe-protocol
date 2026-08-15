"""Fail-closed promotion gate for the deferred BlueChipYield slot-3 plan.

This step intentionally cannot promote BlueChip. It independently repeats the
active PriceDesk runtime and complete live-topology checks, then stops. A
future activation package must prove the hardened runtime, atomically bind the
slot/resulting ID or run a fresh approved confirmation preflight, and define
rollback before this promotion path can be restored.
"""

from scripts.utils import log
from scripts.utils.migration import Migration
from scripts.utils.price_source_preflight import (
    require_active_hardened_price_desk,
    require_live_topology,
)

from config.price_source_admission import PriceSourceAdmissionError


ACTIVATION_DEFERRED = (
    "BlueChip slot-3 promotion is deferred pending an approved activation "
    "and rollback workflow"
)


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    price_desk = migration.get_contract("PriceDesk")

    log.h1("Rebinding active PriceDesk before deferred slot-3 promotion")
    require_active_hardened_price_desk(migration, hq, price_desk)
    require_live_topology(migration, price_desk)

    # No canonical manifest promotion occurs in this deferred migration.
    raise PriceSourceAdmissionError(ACTIVATION_DEFERRED)
