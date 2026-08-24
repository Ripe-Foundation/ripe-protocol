"""Block BlueChip activation until the live PriceDesk topology is resolved.

Live Robinhood already uses PriceDesk slot 3 for UniswapV2Prices, while
SwitchboardAlpha treats slot 4 as Pyth. Appending BlueChip at either position
would silently bind the wrong ABI to a hard-coded source ID. Governance must
first choose and implement a coherent registry/consumer topology; this stage
must not deploy or emit activation calldata before that owner decision lands.
"""

from scripts.utils.migration import Migration


BLOCKER = "BLUECHIP_PRICE_DESK_TOPOLOGY_OWNER_DECISION_REQUIRED"


def migrate(migration: Migration):
    price_desk = migration.get_contract("PriceDesk")
    next_id = int(price_desk.numAddrs())
    slot_3 = str(price_desk.getAddr(3))
    slot_4 = str(price_desk.getAddr(4))
    raise RuntimeError(
        f"{BLOCKER}: next id {next_id}; slot 3 {slot_3} is selected for "
        f"BlueChip by the blueprint but is occupied live; slot 4 {slot_4} is "
        "hard-coded as Pyth by SwitchboardAlpha"
    )
