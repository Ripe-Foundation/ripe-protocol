from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    blueprint = migration.blueprint()

    log.h1("Deploying Switchboard Alpha")
    switchboard_alpha = migration.deploy(
        "SwitchboardAlpha",
        hq,
        migration.account(),
        blueprint.PARAMS["PRICE_DESK_MIN_STALE_TIME"],
        blueprint.PARAMS["PRICE_DESK_MAX_STALE_TIME"],
        blueprint.PARAMS["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"]
    )

    migration.execute(
        switchboard_alpha.setRipeAvailableForBonds,
        100_000 * 10 ** 18
    )
    migration.execute(
        switchboard_alpha.setRipePerBlock,
        25 * 10 ** 14
    )
    migration.execute(
        switchboard_alpha.setRipeRewardsAllocs,
        10_00,  # _borrowersAlloc
        90_00,  # _stakersAlloc
        0,  # _votersAlloc
        0,  # _genDepositorsAlloc
    )
    migration.execute(
        switchboard_alpha.setAutoStakeParams,
        90_00,  # _autoStakeRatio
        50_00,  # _autoStakeDurationRatio
        10 * 10 ** 18  # _stabPoolRipePerDollarClaimed
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
        blueprint.CORE_TOKENS["USDC"],
        500 * 10 ** 6,  # _amountPerEpoch
        0,  # _minRipePerUnit
        100 * 10 ** 18,  # _maxRipePerUnit
        25_00,  # _maxRipePerUnitLockBonus
        False,  # _shouldAutoRestart
        0  # _restartDelayBlocks
    )
    migration.execute(
        switchboard_delta.setRipeBondEpochLength,
        21_600  # 12 hours
    )
    migration.execute(switchboard_delta.setStartEpochAtBlock)
