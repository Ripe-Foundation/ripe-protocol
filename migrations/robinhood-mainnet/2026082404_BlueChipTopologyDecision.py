"""Record the owner-approved Robinhood BlueChip deferral without writes.

PriceDesk source IDs are chain-local. BlueChipYield is not part of the current
Robinhood launch, so it has no registry assignment and uses ID ``0`` as the
configuration sentinel. After the required PR #206 replacement history, slot 3
contains the authenticated monitoring-only UniswapV2Prices generation. This
read-only checkpoint exact-matches that slot and registry cursor and revalidates
the live inert surface rather than treating BlueChip's deferral as proof that
the slot is empty. It is deliberately a composed-history checkpoint, not a
greenfield replay assumption. A future BlueChip activation must choose its ID
from the then-live topology in a separately reviewed migration.
"""

from config.robinhood_launch import BLUECHIP_PRICES_ID
from scripts.utils import log
from scripts.utils.migration import Migration


INVALID_CONFIG = "BLUECHIP_PRICE_DESK_ID_MUST_REMAIN_UNASSIGNED"
INVALID_TOPOLOGY = "BLUECHIP_DEFERRED_PRICE_DESK_TOPOLOGY_MISMATCH"
EXPECTED_NEXT_PRICE_SOURCE_ID = 4
UNISWAP_MONITOR_ID = 3


def _as_address(value):
    return str(getattr(value, "address", value)).lower()


def migrate(migration: Migration):
    if BLUECHIP_PRICES_ID != 0:
        raise RuntimeError(INVALID_CONFIG)

    price_desk = migration.get_contract("PriceDesk")
    uniswap_monitor = migration.get_address("UniswapV2Prices")
    if int(price_desk.numAddrs()) != EXPECTED_NEXT_PRICE_SOURCE_ID:
        raise RuntimeError(f"{INVALID_TOPOLOGY}: next registry id")
    if _as_address(price_desk.getAddr(UNISWAP_MONITOR_ID)) != _as_address(
        uniswap_monitor
    ):
        raise RuntimeError(f"{INVALID_TOPOLOGY}: slot 3")
    if int(price_desk.getRegId(uniswap_monitor)) != UNISWAP_MONITOR_ID:
        raise RuntimeError(f"{INVALID_TOPOLOGY}: reverse registration")

    uniswap_contract = migration.get_contract("UniswapV2Prices")
    ripe_token = migration.get_address("RipeToken")
    if _as_address(uniswap_contract) != _as_address(uniswap_monitor):
        raise RuntimeError(f"{INVALID_TOPOLOGY}: canonical monitor")
    if not bool(uniswap_contract.isMonitoringOnly()):
        raise RuntimeError(f"{INVALID_TOPOLOGY}: monitoring marker")
    if tuple(uniswap_contract.getPriceAndHasFeed(ripe_token)) != (0, False):
        raise RuntimeError(f"{INVALID_TOPOLOGY}: inert price surface")

    log.h1("BlueChipYield remains deferred and unassigned on Robinhood")
    log.info("\tPriceDesk slot 3 is the authenticated inert UniswapV2Prices monitor")
    log.info("\tNo deployment, PriceDesk registration, or activation calldata emitted")
