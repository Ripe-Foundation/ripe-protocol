from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS

# TrainingWheels launch allowlist.
#
# P-H04-414 holds the production allowlist blocked on B-H04-ROLES. This is the
# operator-supplied list for the current run and must be re-confirmed before a
# live deployment.
WHITELIST = [
    '0xEC0870490e06a60f700b103fE9560DCeE185C2C5',
]


def migrate(migration: Migration):
    deployer = migration.account()
    blueprint = migration.blueprint()

    # Fail closed on unresolved identities rather than handing the protocol to a
    # zero address or an address inherited from another chain.
    governance = blueprint.ADDYS["GOVERNANCE"]
    assert governance != ZERO_ADDRESS  # dev: governance identity unresolved

    log.h1("Deploying Tokens")

    # NOTE: initial supplies are zero per P-H04-415/417/419. The deployer holds
    # token governance only until finishTokenSetup binds each token to RipeHq.
    green_token = migration.deploy(
        "GreenToken",
        ZERO_ADDRESS,
        deployer,
        blueprint.PARAMS["MIN_HQ_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_HQ_CHANGE_TIMELOCK"],
        blueprint.PARAMS["GREEN_INITIAL_SUPPLY"],
        deployer,
    )

    ripe_token = migration.deploy(
        "RipeToken",
        ZERO_ADDRESS,
        deployer,
        blueprint.PARAMS["MIN_HQ_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_HQ_CHANGE_TIMELOCK"],
        blueprint.PARAMS["RIPE_INITIAL_SUPPLY"],
        governance,
    )

    savings_green = migration.deploy(
        "SavingsGreen",
        green_token,
        ZERO_ADDRESS,
        deployer,
        blueprint.PARAMS["MIN_HQ_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_HQ_CHANGE_TIMELOCK"],
        blueprint.PARAMS["SAVINGS_GREEN_INITIAL_SUPPLY"],
        ZERO_ADDRESS,
    )

    log.h1("Deploying RipeHq")
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

    log.h1("Deploying Config Artifacts")

    contributor_template = migration.deploy_bp(
        "Contributor",
    )
    training_wheels = migration.deploy(
        "TrainingWheels",
        hq,
        WHITELIST,
    )
    migration.deploy(
        "DefaultsRobinHood",
        contributor_template,
        training_wheels,
        ripe_token,
        green_token,
        savings_green,
    )
