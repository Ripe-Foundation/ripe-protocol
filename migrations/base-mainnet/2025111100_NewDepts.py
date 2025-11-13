from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS


def migrate(migration: Migration):

    blueprint = migration.blueprint()

    hq = migration.get_contract("RipeHq")

    switchboard_alpha = migration.deploy(
        "SwitchboardAlpha",
        hq,
        migration.account(),
        blueprint.PARAMS["PRICE_DESK_MIN_STALE_TIME"],
        blueprint.PARAMS["PRICE_DESK_MAX_STALE_TIME"],
        3_600,  # 2 hours
        blueprint.PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
    )
    migration.execute(switchboard_alpha.setActionTimeLockAfterSetup)
    migration.execute(switchboard_alpha.relinquishGov)

    switchboard_delta = migration.deploy(
        "SwitchboardDelta",
        hq,
        migration.account(),
        3_600,  # 2 hours
        blueprint.PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
    )
    migration.execute(switchboard_delta.setActionTimeLockAfterSetup)
    migration.execute(switchboard_delta.relinquishGov)

    auction_house = migration.deploy(
        "AuctionHouse",
        hq,
    )
    credit_engine = migration.deploy(
        "CreditEngine",
        hq,
    )
    credit_redeem = migration.deploy(
        "CreditRedeem",
        hq,
    )
    deleverage = migration.deploy(
        "Deleverage",
        hq,
    )
    teller = migration.deploy(
        "Teller",
        hq,
        True,
    )
    teller_utils = migration.deploy(
        "TellerUtils",
        hq,
    )
