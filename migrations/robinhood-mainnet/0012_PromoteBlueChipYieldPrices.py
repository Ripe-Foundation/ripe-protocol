"""Static plan to promote BlueChip only after PriceDesk slot-3 readback.

The H-06 Robinhood runner intentionally rejects this legacy API. Convert this
postcondition to a typed ``MIGRATION_STAGE`` action before execution.
"""

from scripts.utils import log
from scripts.utils.migration import Migration


BLUECHIP_CANDIDATE = "BlueChipYieldPricesCandidate0011"


def migrate(migration: Migration):
    price_desk = migration.get_contract("PriceDesk")
    log.h1("Verifying PriceDesk slot 3 and promoting BlueChipYieldPrices")
    migration.promote_candidate(
        "BlueChipYieldPrices",
        BLUECHIP_CANDIDATE,
        price_desk,
        3,
    )
