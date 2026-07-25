import os
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
    require_operation,
    resolve_rpc_reference,
    validate_fork_request,
    verify_chain_identity,
)
from scripts.utils import log
from scripts.utils.deploy_args import DeployArgs
from scripts.utils.migration_helpers import get_account, load_vyper_files
from scripts.utils.migration_runner import MigrationRunner


ROOT = Path(__file__).resolve().parents[1]

CLICK_PROMPTS = {
    "safe": {
        "prompt": "What is the safe address?",
        "default": "",
        "help": "Safe accounts are not supported by H-02.",
    },
    "environment": {
        "prompt": "Manifest namespace",
        "default": "v1",
        "help": (
            "Compatibility assertion for the profile-owned history namespace. "
            "Defaults to `v1`."
        ),
    },
    "start_timestamp": {
        "prompt": "Start timestamp",
        "default": "0",
        "help": (
            "Timestamp at which to start running migrations. Existing resume "
            "semantics are unchanged."
        ),
    },
    "single": {
        "prompt": "Is single migration?",
        "default": False,
        "help": (
            "Runs only the specified migration. If false, runs all migrations "
            "starting from the specified timestamp."
        ),
    },
    "end_timestamp": {
        "prompt": "End timestamp",
        "default": "0",
        "help": "Last migration timestamp to run.",
        "depends": {"single": False},
    },
    "account": {
        "prompt": "Deployer account name",
        "default": "DEPLOYER",
        "help": "Environment key prefix for a fork-only account.",
    },
    "is_retry": {
        "prompt": "Ignore current logs (always run transactions)?",
        "help": "Ignore previous log files.",
        "default": False,
    },
}


def param_prompt(ctx, param, value):
    param_config = CLICK_PROMPTS.get(param.name)
    if param_config is None:
        return value

    default_val = param_config.get("default")
    prompt = param_config.get("prompt")
    optional = param_config.get("optional", default_val is not None)
    if value != default_val:
        return value
    if prompt is None or (not ctx.params.get("ask") and optional):
        return value

    should_prompt = True
    depends = param_config.get("depends")
    if depends is not None:
        should_prompt = any(
            ctx.params.get(key) == expected
            for key, expected in depends.items()
        )
    if not should_prompt:
        return value

    return click.prompt(
        f"{prompt} --{param.name.replace('_', '-')}",
        default=default_val,
        hide_input=param.name == "password",
        type=param_config.get("type"),
    )


def read_chain_id(rpc_url: str) -> int | str:
    return EthereumRPC(rpc_url).fetch("eth_chainId", [])


def _require_static_assertions(profile, environment, blueprint) -> str:
    repository = profile.repository
    if repository.history_dir is None:
        raise NetworkProfileError(
            "H02_REPOSITORY_UNAVAILABLE",
            profile_id=profile.identity.profile_id,
            operation=Operation.MIGRATION_FORK,
        )
    expected_environment = repository.history_dir.name
    if environment != expected_environment:
        raise NetworkProfileError(
            "H02_HISTORY_ALIAS",
            profile_id=profile.identity.profile_id,
            operation=Operation.MIGRATION_FORK,
        )
    expected_blueprint = repository.blueprint_id
    if expected_blueprint is None:
        raise NetworkProfileError(
            "H02_REPOSITORY_UNAVAILABLE",
            profile_id=profile.identity.profile_id,
            operation=Operation.MIGRATION_FORK,
        )
    if blueprint is not None and blueprint != expected_blueprint:
        raise NetworkProfileError(
            "H02_PROFILE_INVALID",
            profile_id=profile.identity.profile_id,
            operation=Operation.MIGRATION_FORK,
        )
    return expected_blueprint


@click.command()
@click.option(
    "--ask",
    is_flag=True,
    default=False,
    help="Prompt for eligible missing parameters.",
)
@click.option(
    "--safe",
    default=CLICK_PROMPTS["safe"]["default"],
    help=CLICK_PROMPTS["safe"]["help"],
    callback=param_prompt,
)
@click.option(
    "--fork",
    is_flag=True,
    default=False,
    help="Run the existing migration runner in exploration-only fork mode.",
)
@click.option(
    "--rpc",
    default=None,
    help=(
        "Sensitive full RPC URL override. If omitted, the selected profile's "
        "named RPC_URL environment variable is used. The value is never logged."
    ),
)
@click.option(
    "--environment",
    default=CLICK_PROMPTS["environment"]["default"],
    help=CLICK_PROMPTS["environment"]["help"],
    callback=param_prompt,
)
@click.option(
    "--start-timestamp",
    "-t",
    default=CLICK_PROMPTS["start_timestamp"]["default"],
    help=CLICK_PROMPTS["start_timestamp"]["help"],
    callback=param_prompt,
)
@click.option(
    "--single",
    "-s",
    is_flag=True,
    default=CLICK_PROMPTS["single"]["default"],
    help=CLICK_PROMPTS["single"]["help"],
    callback=param_prompt,
)
@click.option(
    "--end-timestamp",
    "-e",
    default=CLICK_PROMPTS["end_timestamp"]["default"],
    help=CLICK_PROMPTS["end_timestamp"]["help"],
    callback=param_prompt,
)
@click.option(
    "--profile",
    "--chain",
    "profile_id",
    required=True,
    type=click.Choice(NETWORK_PROFILE_IDS, case_sensitive=False),
    help=(
        "Required canonical network profile. `--chain` is a deprecated "
        "equivalent spelling; it does not define a separate identity."
    ),
)
@click.option(
    "--blueprint",
    "-b",
    default=None,
    help=(
        "Optional compatibility assertion; when supplied it must equal the "
        "selected profile's blueprint."
    ),
)
@click.option(
    "--account",
    "-a",
    default=CLICK_PROMPTS["account"]["default"],
    help=CLICK_PROMPTS["account"]["help"],
    callback=param_prompt,
)
@click.option(
    "--ledger",
    default=-1,
    help="Ledger accounts are not supported by H-02.",
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
    profile_id,
    blueprint,
    account,
    ledger,
):
    """Run migrations through a validated, explicit network profile."""
    del ask
    try:
        profile = get_profile(profile_id)
        operation = (
            Operation.MIGRATION_FORK if fork else Operation.MIGRATION_LIVE
        )
        require_operation(profile, operation)

        if safe or ledger != -1:
            raise NetworkProfileError(
                "H02_ACCOUNT_BACKEND_UNAPPROVED",
                profile_id=profile.identity.profile_id,
                operation=operation,
            )
        selected_blueprint = _require_static_assertions(
            profile, environment, blueprint
        )
        validate_fork_request(
            profile,
            operation,
            evidence_mode=False,
            block_number=None,
            allow_dirty=True,
        )
        redacted_rpc = resolve_rpc_reference(
            profile, operation, os.environ, rpc
        )
        identity = verify_chain_identity(
            profile, operation, redacted_rpc, read_chain_id
        )
        sender = get_account(account, identity, operation)
        paths = repository_paths(
            profile, operation, root=ROOT, identity=identity
        )
    except NetworkProfileError as error:
        raise click.ClickException(str(error)) from None

    deploy_args = DeployArgs(
        sender,
        profile.identity.profile_id,
        ignore_logs=not is_retry,
        blueprint=selected_blueprint,
        rpc=redacted_rpc.value,
    )

    log.h1("Contract Migration")
    log.info(
        "RPC configured: "
        f"profile={profile.identity.profile_id} "
        f"reference={redacted_rpc.reference} value=<redacted>."
    )
    log.info(f"Deployer account name `{account}`.")
    log.info(f"History namespace `{paths.history_dir.relative_to(ROOT)}`.")
    log.info(f"Running migrations starting with timestamp {start_timestamp}.")
    log.info(f"Profile: {profile.identity.profile_id}.")
    log.info("Fork: exploration-only; output is not release evidence.")
    log.info("")

    vyper_files = load_vyper_files()
    log.info(f"Loaded {len(vyper_files)} Vyper files.")
    log.h2("Running migrations...")
    migrations = MigrationRunner(
        str(paths.migration_dir),
        str(paths.history_dir),
        vyper_files,
    )

    try:
        boa.deployments.set_deployments_db(
            boa.deployments.DeploymentsDB(":memory:")
        )
        with boa.fork(redacted_rpc.value, allow_dirty=True) as env:
            try:
                env.set_balance(sender.address, 10 * 10**18)
                log.h2("Fork-only deployer wallet funded with 10 ETH")
            except Exception:
                log.h2("Cannot fund fork-only deployer wallet")
            total_gas = migrations.run(
                deploy_args, start_timestamp, end_timestamp, not single
            )
    except Exception:
        raise click.ClickException(
            "H02_MIGRATION_EXECUTION_FAILED "
            f"profile={profile.identity.profile_id} "
            f"operation={operation.value} env={redacted_rpc.reference}"
        ) from None

    log.info(f"Total gas used: {total_gas}")
    log.info("Done.")
    log.info("")


if __name__ == "__main__":
    cli()
