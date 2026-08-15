"""Fail-closed gate for the deferred BlueChipYield slot-3 plan.

Robinhood's recorded active PriceDesk predates the source-isolation hardening.
This migration therefore emits no Safe calldata and performs no promotion,
deployment, or governance finalization. A separately governed replacement
migration must first install the exact hardened PriceDesk runtime and preserve
its registry state. Slot-3 activation also remains deferred until an atomic or
fresh post-timelock confirmation workflow is approved.
"""

from scripts.utils import log
from scripts.utils.migration import Migration
from scripts.utils.price_source_preflight import (
    require_active_hardened_price_desk,
    require_live_topology,
)

from config.price_source_admission import PriceSourceAdmissionError


ACTIVATION_DEFERRED = (
    "BlueChip slot-3 activation is deferred pending a governed hardened "
    "PriceDesk replacement and safe confirmation workflow"
)


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    price_desk = migration.get_contract("PriceDesk")

    # Both checks precede every manifest promotion, candidate deployment,
    # governance finalization, execution, and calldata-generation operation.
    log.h1("Binding active PriceDesk to the governed hardened runtime")
    require_active_hardened_price_desk(migration, hq, price_desk)
    log.h1("Validating the complete live PriceDesk and Curve topology")
    require_live_topology(migration, price_desk)

    # No start/confirm calldata is produced. This removes the non-atomic
    # preflight-to-confirmation race from the executable migration surface.
    raise PriceSourceAdmissionError(ACTIVATION_DEFERRED)
