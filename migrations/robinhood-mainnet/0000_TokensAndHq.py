from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS

from config.robinhood_launch import (
    GOVERNANCE,
    GREEN_INITIAL_SUPPLY,
    REGISTRY_MAX_DELAY,
    REGISTRY_MIN_DELAY,
    RIPE_HQ_MAX_TIMELOCK,
    RIPE_HQ_MIN_TIMELOCK,
    RIPE_INITIAL_SUPPLY,
    SGREEN_INITIAL_SUPPLY,
    SGREEN_SUPPLY_RECIPIENT,
    TOKEN_HQ_MAX_TIMELOCK,
    TOKEN_HQ_MIN_TIMELOCK,
    TRAINING_WHEELS_ALLOWLIST,
    address,
)


def migrate(migration: Migration):
    deployer = migration.account()

    log.h1("Deploying Tokens")

    # The deployer is initial governance on all three tokens and on RipeHq, and
    # stays governance until the handoff in the final migration -- same as Base.
    # GREEN is minted to the deployer because the deployer seeds the pool later.
    green_token = migration.deploy(
        "GreenToken",
        ZERO_ADDRESS,
        deployer,
        TOKEN_HQ_MIN_TIMELOCK,
        TOKEN_HQ_MAX_TIMELOCK,
        GREEN_INITIAL_SUPPLY,
        deployer,
    )

    ripe_token = migration.deploy(
        "RipeToken",
        ZERO_ADDRESS,
        deployer,
        TOKEN_HQ_MIN_TIMELOCK,
        TOKEN_HQ_MAX_TIMELOCK,
        RIPE_INITIAL_SUPPLY,
        GOVERNANCE,
    )

    savings_green = migration.deploy(
        "SavingsGreen",
        green_token,
        ZERO_ADDRESS,
        deployer,
        TOKEN_HQ_MIN_TIMELOCK,
        TOKEN_HQ_MAX_TIMELOCK,
        SGREEN_INITIAL_SUPPLY,
        SGREEN_SUPPLY_RECIPIENT,
    )

    log.h1("Deploying RipeHq")

    hq = migration.deploy(
        "RipeHq",
        green_token,
        savings_green,
        ripe_token,
        deployer,
        RIPE_HQ_MIN_TIMELOCK,
        RIPE_HQ_MAX_TIMELOCK,
        REGISTRY_MIN_DELAY,
        REGISTRY_MAX_DELAY,
    )

    # Registry ids 1-3 are assigned in this exact order by AddressRegistry.
    migration.execute(green_token.finishTokenSetup, hq)
    migration.execute(ripe_token.finishTokenSetup, hq)
    migration.execute(savings_green.finishTokenSetup, hq)

    log.h1("Deploying Defaults")

    # A blueprint: initcode that Contributor clones are created from, never a
    # live contract. Base deploys it the same way.
    contributor_template = migration.deploy_bp("Contributor")

    training_wheels = migration.deploy(
        "TrainingWheels",
        hq,
        TRAINING_WHEELS_ALLOWLIST,
    )

    migration.deploy(
        "DefaultsRobinhood",
        contributor_template,
        training_wheels,
        ripe_token,
        green_token,
        savings_green,
        address("USDG"),
        address("WETH"),
    )
