from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS

from config.robinhood_launch import (
    GOVERNANCE,
    SGREEN_SUPPLY_RECIPIENT,
    TRAINING_WHEELS_ALLOWLIST,
    approved,
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
        approved("Deployment.DP-05.timelocks.TokenHq.minTimeLock"),
        approved("Deployment.DP-05.timelocks.TokenHq.maxTimeLock"),
        approved("Deployment.DP-19.supply.GREEN.amount"),
        deployer,
    )

    ripe_token = migration.deploy(
        "RipeToken",
        ZERO_ADDRESS,
        deployer,
        approved("Deployment.DP-05.timelocks.TokenHq.minTimeLock"),
        approved("Deployment.DP-05.timelocks.TokenHq.maxTimeLock"),
        approved("Deployment.DP-19.supply.RIPE.amount"),
        GOVERNANCE,
    )

    savings_green = migration.deploy(
        "SavingsGreen",
        green_token,
        ZERO_ADDRESS,
        deployer,
        approved("Deployment.DP-05.timelocks.TokenHq.minTimeLock"),
        approved("Deployment.DP-05.timelocks.TokenHq.maxTimeLock"),
        approved("Deployment.DP-19.supply.SGREEN.amount"),
        SGREEN_SUPPLY_RECIPIENT,
    )

    log.h1("Deploying RipeHq")

    hq = migration.deploy(
        "RipeHq",
        green_token,
        savings_green,
        ripe_token,
        deployer,
        approved("Deployment.DP-05.timelocks.RipeHq.minTimeLock"),
        approved("Deployment.DP-05.timelocks.RipeHq.maxTimeLock"),
        approved("Deployment.DP-05.timelocks.AddressRegistry.minDelay"),
        approved("Deployment.DP-05.timelocks.AddressRegistry.maxDelay"),
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
        address("STEAKHOUSE_USDG_VAULT"),
    )
