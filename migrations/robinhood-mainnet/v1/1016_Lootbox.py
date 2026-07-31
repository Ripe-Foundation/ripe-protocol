from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    blueprint = migration.blueprint()

    log.h1("Deploying Lootbox")

    # The constructor now takes the S3 Underscore send-interval floor plus the
    # interval and both reward amounts. P-H04-306 approves the floor as 7,200
    # blocks (Base 43,200 / 6); P-H04-307 keeps the interval at zero, which
    # leaves hasUnderscoreRewards false and both reward amounts unset --
    # Underscore is absent on Robinhood.
    lootbox = migration.deploy(
        "Lootbox",
        hq,
        blueprint.PARAMS["LOOTBOX_MIN_UNDERSCORE_SEND_INTERVAL"],
        blueprint.PARAMS["LOOTBOX_UNDERSCORE_SEND_INTERVAL"],
        blueprint.PARAMS["LOOTBOX_UNDY_DEPOSIT_REWARDS_AMOUNT"],
        blueprint.PARAMS["LOOTBOX_UNDY_YIELD_BONUS_AMOUNT"],
    )

    migration.execute(hq.startAddNewAddressToRegistry, lootbox, "Lootbox")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, lootbox)) == 16

    # lootbox can mint ripe
    migration.execute(hq.initiateHqConfigChange, 16, False, True, False)
    migration.execute(hq.confirmHqConfigChange, 16)
