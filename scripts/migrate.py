import boa.deployments
import click
import boa

from scripts.utils import log
from scripts.utils.migration_helpers import get_account, load_vyper_files
from scripts.utils.migration_runner import MigrationRunner
from scripts.utils.deploy_args import DeployArgs

from boa.environment import Env
import os

MIGRATION_SCRIPTS_DIR = "./migrations"
MIGRATION_HISTORY_DIR = "./migration_history"


CLICK_PROMPTS = {
    "rpc": {
        "prompt": "What is the desired rpc?",
        "default": "",
        "help": "RPC url for the chain to deploy to. Defaults to ``.",
    },
    "environment": {
        "prompt": "Inform the environment name",
        "default": "dev",
        "help": f"Environment of manifests that are written and read by migration scripts to pass state from previous migrations. Defaults to `dev`.",
    },
    "start_timestamp": {
        "prompt": "Start timestamp",
        "default": "0",
        "help": "Timestamp at which to start running migrations. If none is provided, the timestamp of the first manifest is used.",
    },
    "single": {
        "prompt": "Is single migration?",
        "default": False,
        "help": "Runs only the specified migration. If false, runs all the migrations starting from the specified timestamp."
    },
    "end_timestamp": {
        "prompt": "End timestamp",
        "default": "0",
        "help": "Last timestamp migration that will run. If none is provided, the timestamp of the most recent manifest is used.",
        "depends": {
            "single": False
        }
    },
    "blueprint": {
        "prompt": "Blueprint",
        "default": "base",
        "help": "Blueprint to use for the migration. Defaults to `base`.",
    },
    "chain": {
        "prompt": "Chain name",
        "default": "local",
        "help": "Chain name for custom configuration on the deployment (ex: eth-mainnet, eth-sepolia, base-mainnet, base-sepolia).  Defaults to `local`",
        "type": click.Choice(["local", "base-mainnet", "base-sepolia", "eth-sepolia", "eth-mainnet", "base-mainnet", "base-sepolia"], case_sensitive=False),

    },
    "account": {
        "prompt": "Deployer account name",
        "default": "DEPLOYER",
        "help": "Account name for deployment. Defaults to `DEPLOYER`"
    },
    "is_retry": {
        "prompt": "Ignore current logs (always run transactions)?",
        "help": "Ignore previous log files",
        "default": False,
    },
}


def param_prompt(ctx, param, value):
    param_config = CLICK_PROMPTS[param.name]
    is_configured_param = not (param_config is None)

    if not is_configured_param:
        return value

    default_val = None if "default" not in param_config.keys(
    ) else param_config["default"]
    prompt = None if "prompt" not in param_config.keys(
    ) else param_config["prompt"]
    optional = not default_val is None if "optional" not in param_config.keys(
    ) else param_config["optional"]

    if value != default_val:
        return value

    if prompt is None or (ctx.params.get("silent") and optional):
        return value

    should_prompt = True

    depends = None if "depends" not in param_config.keys(
    ) else param_config["depends"]

    if not (depends is None):
        should_prompt = False
        for key in param_config["depends"].keys():
            dependency_val = ctx.params.get(key)
            if dependency_val == param_config["depends"][key]:
                should_prompt = True
                break

    if not should_prompt:
        return value

    type = None if "type" not in param_config.keys() else param_config["type"]

    value = click.prompt(
        f"{prompt} --{param.name.replace('_', '-')}",
        default=default_val,
        hide_input=param.name == "password",
        type=type,
    )

    return value


@click.command()
@click.option("--silent", is_flag=True, default=False, help="Run command without prompts.")
@click.option("--fork", is_flag=True, default=False, help="Declare that the migration is running on a fork.")
@click.option(
    "--rpc",
    default=CLICK_PROMPTS["rpc"]["default"],
    help=CLICK_PROMPTS["rpc"]["help"],
    callback=param_prompt,
)
@click.option(
    "--environment",
    default=CLICK_PROMPTS["environment"]["default"],
    help=CLICK_PROMPTS["environment"]["help"],
    callback=param_prompt,
)
@click.option(
    "--start-timestamp", "-t",
    default=CLICK_PROMPTS["start_timestamp"]["default"],
    help=CLICK_PROMPTS["start_timestamp"]["help"],
    callback=param_prompt,
)
@click.option(
    "--single", "-s",
    is_flag=True,
    default=CLICK_PROMPTS["single"]["default"],
    help=CLICK_PROMPTS["single"]["help"],
    callback=param_prompt,
)
@click.option(
    "--end-timestamp", "-e",
    default=CLICK_PROMPTS["end_timestamp"]["default"],
    help=CLICK_PROMPTS["end_timestamp"]["help"],
    callback=param_prompt,
)
@click.option(
    "--chain", "-f",
    default=CLICK_PROMPTS["chain"]["default"],
    help=CLICK_PROMPTS["chain"]["help"],
    callback=param_prompt,
)
@click.option(
    "--blueprint", "-b",
    default=CLICK_PROMPTS["blueprint"]["default"],
    help=CLICK_PROMPTS["blueprint"]["help"],
    callback=param_prompt,
)
@click.option(
    "--account", "-a",
    default=CLICK_PROMPTS["account"]["default"],
    help=CLICK_PROMPTS["account"]["help"],
    callback=param_prompt,
)
@click.option(
    "--is-retry",
    is_flag=True,
    default=CLICK_PROMPTS["is_retry"]["default"],
    help=CLICK_PROMPTS["is_retry"]["help"],
    callback=param_prompt,
)
def cli(
    silent,
    fork,
    is_retry,
    rpc,
    single,
    environment,
    start_timestamp,
    end_timestamp,
    chain,
    blueprint,
    account,
):
    """
    Deploys the protocol by running migration scripts.

    Migrations scripts are located in the `./migrations` directory.
    Migration script filenames are prefixed with a numeric timestamp
    that is used to set the order in which the scripts are run, and
    to determine which scripts to continue from in future migrations.

    Each migration script returns an object that is stored in a JSON
    manifest file in the directory specified by `--environment`. The
    manifest filename includes the timestamp of the migration that
    created it. Future migrations resume from the first migration
    script with a timestamp greater than that of the most recent
    manifest file.

    The contents of the most recent manifest file are parsed into an
    object and passed to the `migrate` function of the next migration
    script. This enables each migration script to access data from
    previous migrations, such as the addresses of deployed contracts.

    Different history directories should be used to record the
    manifests for different networks/environments,
    under a subfolder named with the network ID, e.g.,
    `.migration_history/network-219183`.
    """

    final_rpc = rpc if rpc else (
        'boa' if chain == 'local' else f"https://{chain}.g.alchemy.com/v2/{os.environ.get('WEB3_ALCHEMY_API_KEY')}")

    sender = get_account(account)

    deploy_args = DeployArgs(sender, chain, ignore_logs=not is_retry, blueprint=blueprint)

    log.h1("Contract Migration")
    log.info(f"Connected to rpc `{final_rpc}`.")
    log.info(f"Deployer account `{sender.address}`.")
    log.info(f"Manifests are stored in `{environment}`.")
    log.info(f"Deployment arguments: {deploy_args}")
    log.info(f"Running migrations starting with timestamp {start_timestamp}.")
    log.info(f"Chain: {chain}.")
    log.info(f"Fork: {fork}.")
    log.info("")
    vyper_files = load_vyper_files()
    log.info(f"Loaded {len(vyper_files)} Vyper files.")
    log.h2("Running migrations...")

    migrations = MigrationRunner(
        f"{MIGRATION_SCRIPTS_DIR}/{chain}",
        f"{MIGRATION_HISTORY_DIR}/{chain}/{environment}",
        vyper_files
    )

    boa.deployments.set_deployments_db(boa.deployments.DeploymentsDB(":memory:"))
    if final_rpc == 'boa':
        with boa.set_env(Env()) as env:
            total_gas = migrations.run(
                deploy_args, start_timestamp, end_timestamp, not single)

    elif fork:
        with boa.fork(final_rpc, allow_dirty=True) as env:
            try:
                env.set_balance(account.address, 10*10**18)
                log.h2('Deployer wallet funded with 10 ETH')
            except:
                log.h2('Cannot fund deployer wallet')
            total_gas = migrations.run(
                deploy_args, start_timestamp, end_timestamp, not single)
    else:
        with boa.set_network_env(final_rpc) as env:
            env.add_account(sender)
            total_gas = migrations.run(
                deploy_args, start_timestamp, end_timestamp, not single)

    log.info(f'Total gas used: {total_gas}')

    log.info("Done.")
    log.info("")


if __name__ == "__main__":
    cli()
