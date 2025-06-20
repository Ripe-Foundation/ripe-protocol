from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS


def migrate(migration: Migration):
    deployer = migration.account()
    blueprint = migration.blueprint()

    log.h1("Deploying Tokens")

    migration.deploy("DefaultsBaseSepolia")

    green_token = migration.deploy(
        "GreenToken",
        ZERO_ADDRESS,
        deployer,
        blueprint.PARAMS["MIN_HQ_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_HQ_CHANGE_TIMELOCK"],
        1_000 * EIGHTEEN_DECIMALS,
        deployer,
    )

    ripe_token = migration.deploy(
        "RipeToken",
        ZERO_ADDRESS,
        deployer,
        blueprint.PARAMS["MIN_HQ_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_HQ_CHANGE_TIMELOCK"],
        1_000_000 * EIGHTEEN_DECIMALS,
        deployer,
    )
    savings_green = migration.deploy(
        "SavingsGreen",
        green_token,
        ZERO_ADDRESS,
        deployer,
        blueprint.PARAMS["MIN_HQ_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_HQ_CHANGE_TIMELOCK"],
        0,
        ZERO_ADDRESS,
    )

    log.h1("Deploying RipeHQ")
    hq = migration.deploy(
        "RipeHq",
        green_token,
        savings_green,
        ripe_token,
        deployer,
        blueprint.PARAMS["RIPE_HQ_MIN_GOV_TIMELOCK"],
        blueprint.PARAMS["RIPE_HQ_MAX_GOV_TIMELOCK"],
        blueprint.PARAMS["RIPE_HQ_MIN_REG_TIMELOCK"],
        blueprint.PARAMS["RIPE_HQ_MAX_REG_TIMELOCK"],
    )

    migration.execute(green_token.finishTokenSetup, hq)
    migration.execute(ripe_token.finishTokenSetup, hq)
    migration.execute(savings_green.finishTokenSetup, hq)
