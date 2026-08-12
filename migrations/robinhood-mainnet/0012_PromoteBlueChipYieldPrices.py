"""Static plan to promote BlueChip only after PriceDesk slot-3 readback.

The H-06 Robinhood runner intentionally rejects this legacy API. Convert this
postcondition to a typed ``MIGRATION_STAGE`` action before execution.
"""

from scripts.utils import log
from scripts.utils.migration import Migration

from config.robinhood_launch import (
    BLUECHIP_AAVE_PROVIDER,
    BLUECHIP_COMPOUND_CONFIGURATOR,
    BLUECHIP_EULER_FACTORIES,
    BLUECHIP_FLUID_RESOLVER,
    BLUECHIP_MOONWELL_COMPTROLLER,
    BLUECHIP_MORPHO_FACTORIES,
    PRICE_CHANGE_MAX_TIMELOCK,
    PRICE_CHANGE_MIN_TIMELOCK,
    address,
)


BLUECHIP_CANDIDATE = "BlueChipYieldPricesCandidate0011"


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    price_desk = migration.get_contract("PriceDesk")
    log.h1("Verifying PriceDesk slot 3 and promoting BlueChipYieldPrices")
    migration.promote_candidate(
        "BlueChipYieldPrices",
        BLUECHIP_CANDIDATE,
        price_desk,
        3,
        expected_source_path="contracts/priceSources/BlueChipYieldPrices.vy",
        registry_name="PriceDesk",
        expected_constructor_args=(
            hq,
            migration.account(),
            PRICE_CHANGE_MIN_TIMELOCK,
            PRICE_CHANGE_MAX_TIMELOCK,
            BLUECHIP_MORPHO_FACTORIES,
            BLUECHIP_EULER_FACTORIES,
            BLUECHIP_FLUID_RESOLVER,
            BLUECHIP_COMPOUND_CONFIGURATOR,
            BLUECHIP_MOONWELL_COMPTROLLER,
            BLUECHIP_AAVE_PROVIDER,
            address("MORPHO_V2_FACTORY"),
        ),
    )
