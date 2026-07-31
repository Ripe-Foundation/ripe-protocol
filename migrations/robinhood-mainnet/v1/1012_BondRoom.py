from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    blueprint = migration.blueprint()

    log.h1("Deploying Bond Room")

    # P-H04-426/427/428. The previous value here was Base's `43_200 * 30 * 6`,
    # which is 6 months only at Base's 2s cadence; minLockDuration is denominated
    # in `block.number`, which advances every ~12s on Robinhood.
    bond_booster = migration.deploy(
        "BondBooster",
        hq,
        blueprint.PARAMS["BOND_BOOSTER_MAX_BOOST_RATIO"],
        blueprint.PARAMS["BOND_BOOSTER_MAX_UNITS"],
        blueprint.PARAMS["BOND_BOOSTER_MIN_LOCK_DURATION"],
    )

    bond_room = migration.deploy(
        "BondRoom",
        hq,
        bond_booster,
    )
    migration.execute(hq.startAddNewAddressToRegistry, bond_room, "Bond Room")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, bond_room)) == 12

    # bond room can mint ripe. The bond program itself stays disabled --
    # DefaultsRobinHood sets canBond = False.
    migration.execute(hq.initiateHqConfigChange, 12, False, True, False)
    migration.execute(hq.confirmHqConfigChange, 12)
