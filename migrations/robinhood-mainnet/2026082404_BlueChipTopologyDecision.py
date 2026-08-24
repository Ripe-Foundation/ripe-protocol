"""Record the owner-approved Robinhood BlueChip deferral without writes.

PriceDesk source IDs are chain-local. BlueChipYield is not part of the current
Robinhood launch, so it has no registry assignment and uses ID ``0`` as the
configuration sentinel. A future activation must choose its ID from the live
topology in a separately reviewed migration.
"""

from config.robinhood_launch import BLUECHIP_PRICES_ID
from scripts.utils import log
from scripts.utils.migration import Migration


INVALID_CONFIG = "BLUECHIP_PRICE_DESK_ID_MUST_REMAIN_UNASSIGNED"


def migrate(migration: Migration):
    _ = migration
    if BLUECHIP_PRICES_ID != 0:
        raise RuntimeError(INVALID_CONFIG)
    log.h1("BlueChipYield remains deferred and unassigned on Robinhood")
    log.info("\tNo deployment, PriceDesk registration, or activation calldata emitted")
