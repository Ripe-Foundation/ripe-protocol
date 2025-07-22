from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    blueprint = migration.blueprint()

    log.h1("Deploying Bond Room")

    migration.deploy(
        "BondRoom",
        hq,
        migration.get_address("BondBooster"),
    )

    log.h1("Deploying Switchboard Delta")
    switchboard_delta = migration.deploy(
        "SwitchboardDelta",
        hq,
        migration.account(),
        blueprint.PARAMS["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
    )

    migration.execute(
        switchboard_delta.setRipeBondConfig,
        blueprint.CORE_TOKENS['USDC'],  # _asset
        500 * 10**6,  # _amountPerEpoch
        0,  # _minRipePerUnit
        100 * 10**18,  # _maxRipePerUnit
        25_00,  # _maxRipePerUnitLockBonus
        True,  # _shouldAutoRestart
        0,  # _restartDelayBlocks
    )

    migration.execute(switchboard_delta.setActionTimeLockAfterSetup)
    migration.execute(switchboard_delta.relinquishGov)
