import boa.deployments
import click
import boa

from scripts.utils import log
from scripts.utils.migration_helpers import get_account, load_vyper_files
from scripts.utils.migration_runner import MigrationRunner
from scripts.utils.deploy_args import DeployArgs
from boa.environment import Env
# from scripts.utils.safe_account import SafeAccount
# from scripts.utils.ledger_account import LedgerAccount
from scripts.utils.mock_account import MockAccount
import os


MIGRATION_SCRIPTS_DIR = "./migrations"
MIGRATION_HISTORY_DIR = "./migration_history"

def _load_dotenv() -> None:
    """Read .env so the RPC and keys need not be exported by hand.

    Called from cli(), never at import: importing a module must not pull
    secrets into the process environment as a side effect, because anything
    that merely imports this file would inherit them. Running the command is
    an explicit act; importing it is not.

    override=False so a variable already in the environment wins, and an
    explicit `FOO=bar python -m scripts.migrate ...` is never silently
    overridden by .env.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(override=False)


def _rpc_from_env(chain):
    """Per-chain RPC override, e.g. ROBINHOOD_MAINNET_RPC_URL."""
    return os.environ.get(f"{chain.replace('-', '_').upper()}_RPC_URL")


def _local_account(account_name):
    """Load the deployer key from {ACCOUNT}_PRIVATE_KEY, e.g. DEPLOYER.

    scripts.utils.migration_helpers.get_account now requires a verified
    network identity for the H-02 path, so this keeps the plain key route
    without changing a helper that other callers depend on. There is no
    fallback test key: deploying from a well-known key is never what anyone
    wants, and a missing key should say so rather than pick one.
    """
    from eth_account import Account

    log.h1(f"Connecting to deployer account {account_name}")
    key = os.environ.get(f"{account_name}_PRIVATE_KEY")
    if not key:
        raise click.ClickException(
            f"{account_name}_PRIVATE_KEY is not set. Export it, put it in "
            ".env, or pass --ledger <index> to sign with a device."
        )
    account = Account.from_key(key)
    log.h2(f"Deployer account {account_name} connected")
    return account


CLICK_PROMPTS = {
    "safe": {
        "prompt": "What is the safe address?",
        "default": "",
        "help": "Safe address to use for the migration. Defaults to ``.",
    },
    "rpc": {
        "prompt": "What is the desired rpc?",
        "default": "",
        "help": "RPC url for the chain to deploy to. Defaults to ``.",
    },
    "environment": {
        "prompt": "Inform the environment name",
        "default": "v1",
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
        "help": "Blueprint to use for the migration. Defaults to ``.",
    },
    "chain": {
        "prompt": "Chain name",
        "default": "base-mainnet",
        "help": "Chain name for custom configuration on the deployment (ex: eth-mainnet, eth-sepolia, base-mainnet, base-sepolia).  Defaults to `local`",
        "type": click.Choice(["local", "base-mainnet", "base-sepolia", "eth-sepolia", "eth-mainnet", "robinhood-mainnet", "robinhood-testnet"], case_sensitive=False),

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
    "manifest": {
        "prompt": "Manifest",
        "default": "current",
        "help": "Manifest to use for the migration. Defaults to `current`.",
    },
}


# Chains whose verifier key comes from BASESCAN_API_KEY. The key is read when
# it is needed, never at import: importing this module must not require, or
# capture, a credential -- and a missing key should not stop `--help` or a
# deployment to a chain that has no explorer.
_BASESCAN_CHAINS = ("base-mainnet", "base-sepolia")


def _etherscan_api_key(chain):
    if chain not in _BASESCAN_CHAINS:
        return None
    return os.environ.get("BASESCAN_API_KEY")
ETHERSCAN_URLS = {
    "eth-mainnet": "https://api.etherscan.io/api",
    "eth-goerli": "https://api-goerli.etherscan.io/api",
    "eth-sepolia": "https://api-sepolia.etherscan.io/api",
    "base-mainnet": "https://api.basescan.org/api",
    "base-goerli": "https://api-goerli.basescan.org/api",
    "base-sepolia": "https://api-sepolia.basescan.org/api",
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

    if prompt is None or (not ctx.params.get("ask") and optional):
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
@click.option("--ask", is_flag=True, default=False, help="Shoild ask for missing parameters (Not use default values).")
@click.option(
    "--safe",
    default=CLICK_PROMPTS["safe"]["default"],
    help=CLICK_PROMPTS["safe"]["help"],
    callback=param_prompt,
)
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
    "--ledger",
    default=-1,
    help="Ledger account index to use (default: -1 = Not using Ledger)",
    type=int,
)
@click.option(
    "--is-retry",
    is_flag=True,
    default=CLICK_PROMPTS["is_retry"]["default"],
    help=CLICK_PROMPTS["is_retry"]["help"],
    callback=param_prompt,
)
def cli(
    ask,
    safe,
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
    ledger,
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

    _load_dotenv()

    final_rpc = rpc or _rpc_from_env(chain) or (
        'boa' if chain == 'local' else f"https://{chain}.g.alchemy.com/v2/{os.environ.get('WEB3_ALCHEMY_API_KEY')}")

    # A fork cannot execute ArbSys: it is a node-implemented precompile, so
    # `arbBlockNumber()` reverts and the Ledger constructor refuses to deploy.
    # Default fork runs to native so they just work, and leave live runs on
    # ArbSys -- the action block source is an IMMUTABLE constructor argument,
    # so a live run that silently picked native could not be corrected.
    if fork and not os.environ.get("RIPE_LEDGER_BLOCK_SOURCE"):
        os.environ["RIPE_LEDGER_BLOCK_SOURCE"] = "native"

    if safe != "":
        if fork:
            sender = MockAccount(safe)
        # else:
        #     sender = SafeAccount(
        #         safe_address=safe,
        #         rpc_url=final_rpc
        #     )
    elif ledger != -1:
        from scripts.utils.ledger_account import LedgerAccount

        sender = LedgerAccount(final_rpc, ledger)
        # On a fork nothing is broadcast, so resolve the address from the device
        # and then stop touching it -- a fork must never prompt for signatures.
        if fork:
            sender = MockAccount(sender.address)
    else:
        sender = _local_account(account)

    deploy_args = DeployArgs(sender, chain, ignore_logs=not is_retry, blueprint=blueprint, rpc=final_rpc)

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
    # Robinhood has no Etherscan; it uses Blockscout, and nothing here needs a
    # verifier. Only configure one for chains that actually have an entry.
    api_key = _etherscan_api_key(chain)
    if api_key and chain in ETHERSCAN_URLS:
        boa.set_etherscan(api_key=api_key, uri=ETHERSCAN_URLS[chain])

    if final_rpc == 'boa':
        with boa.set_env(Env()) as env:
            total_gas = migrations.run(
                deploy_args, start_timestamp, end_timestamp, not single)

    elif fork:
        with boa.fork(final_rpc, allow_dirty=True) as env:
            try:
                env.set_balance(sender.address, 10*10**18)
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
