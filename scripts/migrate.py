from pathlib import Path

import boa
import boa.deployments
import click
from boa.rpc import EthereumRPC

from config.network_profiles import (
    NETWORK_PROFILE_IDS,
    NetworkProfileError,
    Operation,
    get_profile,
    repository_paths,
    resolve_rpc_reference,
    validate_fork_request,
    validate_verified_identity,
    verify_chain_identity,
)
from scripts.utils import log
from scripts.utils.migration_helpers import get_account, load_vyper_files
from scripts.utils.migration_runner import MigrationRunner
from scripts.utils.deploy_args import DeployArgs
from scripts.utils.mock_account import MockAccount
import os


ROOT = Path(__file__).resolve().parents[1]


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


def read_chain_id(rpc_url: str) -> int | str:
    """Read the identity directly from the selected endpoint before signing."""
    return EthereumRPC(rpc_url).fetch("eth_chainId", [])


def _require_backend(profile, operation, identity, backend_id):
    """Validate a signer choice before constructing or touching the signer."""
    validate_verified_identity(
        profile, operation, identity, require_account=True
    )
    if (
        operation is Operation.MIGRATION_LIVE
        and backend_id not in profile.live_account_backend_ids
    ):
        raise NetworkProfileError(
            "H02_ACCOUNT_BACKEND_UNAPPROVED",
            profile_id=profile.identity.profile_id,
            operation=operation,
        )


CLICK_PROMPTS = {
    "safe": {
        "prompt": "What is the safe address?",
        "default": "",
        "help": (
            "Fork-only Safe address to impersonate. Live Safe proposal "
            "submission is not implemented and fails closed."
        ),
    },
    "rpc": {
        "prompt": "What is the desired rpc?",
        "default": None,
        "help": (
            "Sensitive RPC URL override. If omitted, use the selected "
            "profile's named RPC environment variable."
        ),
    },
    "environment": {
        "prompt": "Inform the environment name",
        "default": None,
        "help": (
            "Optional compatibility assertion; it must equal the "
            "profile-owned history namespace."
        ),
    },
    "start_timestamp": {
        "prompt": "Start timestamp",
        "default": None,
        "help": (
            "Explicit first migration timestamp. If omitted, resume strictly "
            "after the latest numeric manifest checkpoint."
        ),
    },
    "single": {
        "prompt": "Is single migration?",
        "default": False,
        "help": "Runs only the specified migration. If false, runs all the migrations starting from the specified timestamp."
    },
    "end_timestamp": {
        "prompt": "End timestamp",
        "default": None,
        "help": "Optional last migration timestamp (inclusive).",
        "depends": {
            "single": False
        }
    },
    "blueprint": {
        "prompt": "Blueprint",
        "default": None,
        "help": (
            "Optional compatibility assertion. The profile-owned blueprint "
            "is always used."
        ),
    },
    "chain": {
        "prompt": "Network profile",
        "default": "base-mainnet",
        "help": "Canonical network profile. Defaults to `base-mainnet`.",
        "type": click.Choice(NETWORK_PROFILE_IDS, case_sensitive=False),

    },
    "account": {
        "prompt": "Deployer account name",
        "default": "DEPLOYER",
        "help": "Account name for deployment. Defaults to `DEPLOYER`"
    },
    "is_retry": {
        "prompt": "Force replay despite prior transaction logs?",
        "help": (
            "Dangerous explicit replay mode: ignore the selected migration's "
            "transaction log and execute its calls again."
        ),
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
_BASESCAN_CHAINS = ("base-mainnet", "base-sepolia", "robinhood-testnet")


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
    "robinhood-testnet": "https://api-sepolia.basescan.org/api",
}


def param_prompt(ctx, param, value):
    config_name = "chain" if param.name == "profile_id" else param.name
    param_config = CLICK_PROMPTS[config_name]
    is_configured_param = not (param_config is None)

    if not is_configured_param:
        return value

    default_val = None if "default" not in param_config.keys(
    ) else param_config["default"]
    prompt = None if "prompt" not in param_config.keys(
    ) else param_config["prompt"]
    optional = not default_val is None if "optional" not in param_config.keys(
    ) else param_config["optional"]

    if value != default_val or not ctx.params.get("ask"):
        return value

    if prompt is None:
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
@click.option("--fork", is_flag=True, default=False, help="Run against a local fork of the profile RPC.")
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
    "--profile", "--chain", "profile_id",
    default=CLICK_PROMPTS["chain"]["default"],
    type=click.Choice(NETWORK_PROFILE_IDS, case_sensitive=False),
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
    "--force-replay", "--is-retry", "is_retry",
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
    profile_id,
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

    operation = (
        Operation.MIGRATION_FORK if fork else Operation.MIGRATION_LIVE
    )
    try:
        profile = get_profile(profile_id)
        if profile.identity.profile_id.startswith("robinhood-"):
            from config.robinhood_launch import (
                validate_deployment_external_facts,
            )

            try:
                validate_deployment_external_facts()
            except ValueError:
                raise NetworkProfileError(
                    "H02_EXTERNAL_FACTS_UNVERIFIED",
                    profile_id=profile.identity.profile_id,
                    operation=operation,
                ) from None
        redacted_rpc = resolve_rpc_reference(
            profile, operation, os.environ, rpc
        )
        identity = verify_chain_identity(
            profile, operation, redacted_rpc, read_chain_id
        )
        if fork:
            validate_fork_request(
                profile,
                operation,
                evidence_mode=False,
                block_number=None,
                allow_dirty=True,
            )
        paths = repository_paths(
            profile, operation, root=ROOT, identity=identity
        )
        if environment is not None and environment != paths.history_dir.name:
            raise NetworkProfileError(
                "H02_HISTORY_ALIAS",
                profile_id=profile.identity.profile_id,
                operation=operation,
            )
        selected_blueprint = profile.repository.blueprint_id
        if selected_blueprint is None or (
            blueprint is not None and blueprint != selected_blueprint
        ):
            raise NetworkProfileError(
                "H02_PROFILE_INVALID",
                profile_id=profile.identity.profile_id,
                operation=operation,
            )
    except NetworkProfileError as error:
        raise click.ClickException(str(error)) from None

    final_rpc = redacted_rpc.value

    # A fork cannot execute ArbSys: it is a node-implemented precompile, so
    # `arbBlockNumber()` reverts and the Ledger constructor refuses to deploy.
    # Default fork runs to native so they just work, and leave live runs on
    # ArbSys -- the action block source is an IMMUTABLE constructor argument,
    # so a live run that silently picked native could not be corrected.
    if fork and not os.environ.get("RIPE_LEDGER_BLOCK_SOURCE"):
        os.environ["RIPE_LEDGER_BLOCK_SOURCE"] = "native"

    try:
        if safe and ledger != -1:
            raise NetworkProfileError(
                "H02_ACCOUNT_BACKEND_UNAPPROVED",
                profile_id=profile.identity.profile_id,
                operation=operation,
            )
        if safe:
            _require_backend(profile, operation, identity, "safe")
            if not fork:
                # SafeAccount is intentionally not used here: its proposal
                # path is not qualified as a live signer/backend.
                raise NetworkProfileError(
                    "H02_ACCOUNT_BACKEND_UNAPPROVED",
                    profile_id=profile.identity.profile_id,
                    operation=operation,
                )
            sender = MockAccount(safe)
        elif ledger != -1:
            _require_backend(profile, operation, identity, "ledger")
            from scripts.utils.ledger_account import LedgerAccount

            sender = LedgerAccount(final_rpc, ledger)
            if fork:
                sender = MockAccount(sender.address)
        else:
            _require_backend(
                profile, operation, identity, "env-private-key"
            )
            sender = get_account(account, identity, operation)
    except NetworkProfileError as error:
        raise click.ClickException(str(error)) from None

    # Normal operation resumes/skips from the selected migration log. Replaying
    # prior calls is possible only through the explicit dangerous flag.
    deploy_args = DeployArgs(
        sender,
        profile.identity.profile_id,
        ignore_logs=is_retry,
        blueprint=selected_blueprint,
        rpc=final_rpc,
        local_preview=fork,
    )

    log.h1("Contract Migration")
    # The RPC value is never logged, not even redacted: the reference is what
    # an operator needs, and a URL in scrollback or CI output is a key in
    # scrollback or CI output.
    log.info(
        "RPC configured for profile "
        f"`{profile.identity.profile_id}` from `{redacted_rpc.reference}`."
    )
    log.info(f"Deployer account `{sender.address}`.")
    log.info(
        "Manifests are stored in the profile-owned history namespace "
        f"`{paths.history_dir.relative_to(ROOT)}`."
    )
    log.info(f"Deployment arguments: {deploy_args}")
    log.info(
        "Migration start: "
        + (str(start_timestamp) if start_timestamp is not None else "auto-resume")
        + "."
    )
    log.info(f"Profile: {profile.identity.profile_id}.")
    log.info(f"Verified chain id: {identity.observed_chain_id}.")
    log.info(f"Fork: {fork}.")
    log.info("")
    vyper_files = load_vyper_files()
    log.info(f"Loaded {len(vyper_files)} Vyper files.")
    log.h2("Running migrations...")

    migrations = MigrationRunner(
        str(paths.migration_dir),
        str(paths.history_dir),
        vyper_files
    )

    boa.deployments.set_deployments_db(boa.deployments.DeploymentsDB(":memory:"))
    # Robinhood has no Etherscan; it uses Blockscout, and nothing here needs a
    # verifier. Only configure one for chains that actually have an entry.
    api_key = _etherscan_api_key(profile.identity.profile_id)
    if api_key and profile.identity.profile_id in ETHERSCAN_URLS:
        boa.set_etherscan(
            api_key=api_key,
            uri=ETHERSCAN_URLS[profile.identity.profile_id],
        )

    if fork:
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
            # Disable boa's transaction tracer. It probes the node with a
            # dummy `debug_traceTransaction` on first use, which providers can
            # be slow enough to time out -- and that probe runs AFTER the
            # transaction has broadcast, so a deployment that actually
            # succeeded raises before it is written to the log and manifest.
            # The next run then has no idea it already happened and deploys a
            # second copy. Traces only improve error messages; losing the
            # record of a live deployment is the worse failure.
            #
            # boa catches HTTPError and RPCError there but not
            # requests.ReadTimeout, so suppress_debug_tt() alone is not
            # enough: `_tracer` is a cached_property, and seeding it skips
            # the probe entirely.
            env._tracer = None
            env.suppress_debug_tt()
            total_gas = migrations.run(
                deploy_args, start_timestamp, end_timestamp, not single)

    log.info(f'Total gas used: {total_gas}')

    log.info("Done.")
    log.info("")


if __name__ == "__main__":
    cli()
