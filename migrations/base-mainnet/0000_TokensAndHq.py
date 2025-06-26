from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS

WHITELIST = [
    '0x9c340456e7E3450Ec254B5b82448fB60D3633F0B',
    '0x2f537C2C1D263e66733DA492414359B6B70e1269',
    '0xB13D7d316Ff8B9db9cE8CD93d4D2DfD54b7A5419',
    '0x7190081341F0e0223E237270b8479159951A5a46',
]


def migrate(migration: Migration):
    deployer = migration.account()
    blueprint = migration.blueprint()

    log.h1("Deploying Tokens")

    green_token = migration.deploy(
        "GreenToken",
        ZERO_ADDRESS,
        deployer,
        blueprint.PARAMS["MIN_HQ_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_HQ_CHANGE_TIMELOCK"],
        100 * EIGHTEEN_DECIMALS,
        deployer,
    )

    ripe_token = migration.deploy(
        "RipeToken",
        ZERO_ADDRESS,
        deployer,
        blueprint.PARAMS["MIN_HQ_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_HQ_CHANGE_TIMELOCK"],
        10_000_000 * EIGHTEEN_DECIMALS,
        blueprint.ADDYS["GOVERNANCE"],
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

    contributor_template = migration.deploy_bp(
        "Contributor",
    )
    training_wheels = migration.deploy(
        "TrainingWheels",
        hq,
        WHITELIST,
    )
    migration.deploy("DefaultsBase", contributor_template, training_wheels)
