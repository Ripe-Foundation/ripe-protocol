import os
import sys
from contextlib import ExitStack, contextmanager
import importlib
import json
from pathlib import Path

import click

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
from scripts.utils.migration_helpers import get_account, load_vyper_files
from scripts.utils.migration_runner import (
    MigrationError,
    MigrationPlanError,
    MigrationRunner,
    build_blocked_migration_report,
    report_bytes,
    validate_execution_plan_artifact,
)


ROOT = Path(__file__).resolve().parents[1]


class _LazyBoa:
    """Keep Boa entirely outside the static plan process."""

    def __init__(self):
        self._module = None

    def _load(self):
        if self._module is None:
            self._module = importlib.import_module("boa")
            importlib.import_module("boa.deployments")
        return self._module

    def __getattr__(self, name):
        return getattr(self._load(), name)


boa = _LazyBoa()

CLICK_PROMPTS = {
    "safe": {
        "prompt": "What is the safe address?",
        "default": "",
        "help": "Safe accounts are not supported.",
    },
    "environment": {
        "prompt": "Manifest namespace",
        "default": "v1",
        "help": (
            "Compatibility assertion for the profile-owned history namespace."
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
        "help": (
            "Environment key prefix for a fork-only account. Use a "
            "purpose-limited disposable key, never a live deployer key."
        ),
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
    if ctx.params.get("plan") or "--plan" in sys.argv[1:]:
        return value
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
    from boa.rpc import EthereumRPC

    return EthereumRPC(rpc_url).fetch("eth_chainId", [])


@contextmanager
def _fork_environment(profile, operation, redacted_rpc, **kwargs):
    fork_stack = ExitStack()
    body_error = None
    try:
        try:
            env = fork_stack.enter_context(
                boa.fork(redacted_rpc.value, **kwargs)
            )
        except Exception:
            raise click.ClickException(
                "H02_RPC_CONNECT_FAILED "
                f"profile={profile.identity.profile_id} "
                f"operation={operation.value} env={redacted_rpc.reference}"
            ) from None
        yield env
    except BaseException as error:
        body_error = error
        raise
    finally:
        try:
            fork_stack.close()
        except Exception:
            if body_error is None:
                raise click.ClickException(
                    "H02_FORK_TEARDOWN_FAILED "
                    f"profile={profile.identity.profile_id} "
                    f"operation={operation.value} "
                    f"env={redacted_rpc.reference}"
                ) from None
            try:
                log.error(
                    "H02_FORK_TEARDOWN_FAILED "
                    f"profile={profile.identity.profile_id} "
                    f"operation={operation.value} "
                    f"env={redacted_rpc.reference}"
                )
            except Exception:
                pass


def _resolve_sender(
    *,
    account,
    identity,
    operation,
    safe,
    ledger,
    fork,
    rpc_url,
):
    """Select the signing backend: Safe, Ledger, or a named local account.

    Restores the pre-H-02 behaviour for Base. Both hardware paths are imported
    lazily so that a missing native dependency -- `hidapi` for Ledger -- fails
    only the run that actually asked for it, instead of breaking every command
    that imports this module.

    On a fork, the hardware backend resolves the address and then hands over to
    MockAccount: forks must never prompt a device for a signature.
    """
    # NOTE: get_account is deliberately the module-level import, not a local
    # one. Re-importing it here would shadow the module attribute and break
    # every caller that patches or wraps `migrate.get_account`.
    from scripts.utils.mock_account import MockAccount

    if safe:
        if fork:
            return MockAccount(safe)
        try:
            from scripts.utils.safe_account import SafeAccount
        except ImportError as error:
            raise click.ClickException(
                f"Safe backend unavailable: {error}"
            ) from None
        return SafeAccount(safe_address=safe, rpc_url=rpc_url)

    if ledger != -1:
        try:
            from scripts.utils.ledger_account import LedgerAccount
        except ImportError as error:
            raise click.ClickException(
                "Ledger backend unavailable -- the native hidapi library is "
                f"missing. Install it (macOS: `brew install hidapi`). {error}"
            ) from None
        sender = LedgerAccount(rpc_url, ledger)
        # Resolve the address from the device, then stop touching it.
        return MockAccount(sender.address) if fork else sender

    return get_account(account, identity, operation)


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


def _require_plan_flags(
    profile,
    *,
    ask,
    safe,
    fork,
    is_retry,
    rpc,
    single,
    environment,
    start_timestamp,
    end_timestamp,
    blueprint,
    account,
    ledger,
    execution_plan,
    execution_envelope,
    execution_history_root,
) -> None:
    history = profile.repository.history_dir
    expected_environment = None if history is None else history.name
    if (
        ask
        or safe
        or fork
        or is_retry
        or rpc is not None
        or single
        or environment != expected_environment
        or start_timestamp != "0"
        or end_timestamp != "0"
        or blueprint is not None
        or account != CLICK_PROMPTS["account"]["default"]
        or ledger != -1
        or execution_plan is not None
        or execution_envelope is not None
        or execution_history_root is not None
    ):
        raise MigrationPlanError("H05_PLAN_FLAGS_INCOMPATIBLE")


def _read_public_json(path_value: str, code: str):
    path = Path(path_value)
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise MigrationPlanError(code)
    try:
        return json.loads(path.read_bytes())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise MigrationPlanError(code) from None


@click.command()
@click.option(
    "--ask",
    is_flag=True,
    default=False,
    help="Prompt for eligible optional parameters after profile selection.",
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
    "--plan",
    is_flag=True,
    default=False,
    help=(
        "Emit the deterministic blocked Robinhood migration plan without "
        "RPC, account, execution, simulation, or repository writes."
    ),
)
@click.option(
    "--preview",
    is_flag=True,
    default=False,
    help=(
        "Bind --plan to the complete prospective working tree and mark the "
        "artifact non-production and non-executable."
    ),
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
    show_default=True,
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
        "equivalent spelling; it does not define a separate identity. "
        "`local` is recognized but unsupported by this command; it is "
        "reserved for a future embedded-runtime path."
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
    help="Ledger accounts are not supported.",
    type=int,
)
@click.option(
    "--execution-plan",
    default=None,
    help=(
        "Absolute path to a clean-tree Robinhood production plan. The file is "
        "read only after profile, RPC identity, and account gates succeed."
    ),
)
@click.option(
    "--execution-envelope",
    default=None,
    help=(
        "Absolute path to the accepted public execution envelope already "
        "bound into --execution-plan."
    ),
)
@click.option(
    "--execution-history-root",
    default=None,
    help="Absolute private H-06 history directory for Robinhood execution.",
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
    execution_plan=None,
    execution_envelope=None,
    execution_history_root=None,
    plan=False,
    preview=False,
):
    """Run migrations through a validated, explicit network profile."""
    try:
        profile = get_profile(profile_id)
        if preview and not plan:
            raise MigrationPlanError("H05_PREVIEW_REQUIRES_PLAN")
        if plan:
            require_operation(profile, Operation.MIGRATION_PLAN)
            _require_plan_flags(
                profile,
                ask=ask,
                safe=safe,
                fork=fork,
                is_retry=is_retry,
                rpc=rpc,
                single=single,
                environment=environment,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                blueprint=blueprint,
                account=account,
                ledger=ledger,
                execution_plan=execution_plan,
                execution_envelope=execution_envelope,
                execution_history_root=execution_history_root,
            )
            report = build_blocked_migration_report(
                profile.identity.profile_id,
                repository_root=ROOT,
                preview=preview,
            )
            click.echo(report_bytes(report).decode("utf-8"), nl=False)
            return

        del ask
        operation = (
            Operation.MIGRATION_FORK if fork else Operation.MIGRATION_LIVE
        )
        require_operation(profile, operation)

        is_robinhood = profile.identity.profile_id.startswith("robinhood-")
        execution_values = (
            execution_plan,
            execution_envelope,
            execution_history_root,
        )
        if is_robinhood != all(value is not None for value in execution_values):
            raise MigrationPlanError("H05_EXECUTION_INPUTS_REQUIRED")
        if not is_robinhood and any(value is not None for value in execution_values):
            raise MigrationPlanError("H05_EXECUTION_PROFILE_REQUIRED")

        # The Ledger is the approved Robinhood deployer -- it is also RipeHq
        # governance until the 0900 handoff, exactly as on Base. A Safe is not:
        # the Safe RECEIVES governance at the handoff and never signs a
        # deployment transaction, so selecting it here would mean the sender is
        # not the account the plan binds as temporary governance.
        if safe and is_robinhood:
            raise NetworkProfileError(
                "H02_ACCOUNT_BACKEND_UNAPPROVED",
                profile_id=profile.identity.profile_id,
                operation=operation,
            )
        if safe and ledger != -1:
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
        sender = _resolve_sender(
            account=account,
            identity=identity,
            operation=operation,
            safe=safe,
            ledger=ledger,
            fork=fork,
            rpc_url=redacted_rpc.value,
        )
        paths = repository_paths(
            profile, operation, root=ROOT, identity=identity
        )
        robinhood_plan = None
        if is_robinhood:
            robinhood_plan = _read_public_json(
                execution_plan, "H05_EXECUTION_PLAN_FILE"
            )
            envelope = _read_public_json(
                execution_envelope, "H05_EXECUTION_ENVELOPE_FILE"
            )
            if robinhood_plan.get("execution_envelope") != envelope:
                raise MigrationPlanError("H05_EXECUTION_ENVELOPE_MISMATCH")
            validated = validate_execution_plan_artifact(
                robinhood_plan, repository_root=ROOT
            )
            if validated["profile"] != {
                "profile_id": profile.identity.profile_id,
                "base_profile_id": None,
                "expected_chain_id": identity.expected_chain_id,
            }:
                raise MigrationPlanError("H05_PLAN_PROFILE_MISMATCH")
            history_root = Path(execution_history_root)
            if not history_root.is_absolute():
                raise MigrationPlanError("H05_EXECUTION_HISTORY_ROOT")
    except (MigrationPlanError, NetworkProfileError) as error:
        raise click.ClickException(str(error)) from None

    from scripts.utils.deploy_args import DeployArgs

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
    log.info(
        "Fork: exploration-only; this run may write manifests under "
        f"`{paths.history_dir.relative_to(ROOT)}`. Do not commit or treat "
        "those outputs as release evidence."
    )
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
    except Exception:
        raise click.ClickException(
            "H02_MIGRATION_SETUP_FAILED "
            f"profile={profile.identity.profile_id} "
            f"operation={operation.value}"
        ) from None

    with _fork_environment(
        profile, operation, redacted_rpc, allow_dirty=True
    ) as env:
        if robinhood_plan is not None:
            from scripts.utils.robinhood_backends import BoaRobinhoodBackend
            from scripts.utils.robinhood_executor import install_robinhood_executor

            backend = BoaRobinhoodBackend(
                boa_module=boa,
                files=vyper_files,
                sender=sender,
                final_governance_sender=robinhood_plan[
                    "execution_envelope"
                ]["values"][
                    "input:Deployment.DP-18.roles.governance"
                ]["value"],
            )
            install_robinhood_executor(
                deploy_args,
                robinhood_plan,
                repository_root=ROOT,
                backend=backend,
                history_root=history_root,
            )
        try:
            env.set_balance(sender.address, 10 * 10**18)
            log.h2("Fork-only deployer wallet funded with 10 ETH")
        except Exception:
            log.h2("Cannot fund fork-only deployer wallet")

        try:
            total_gas = migrations.run(
                deploy_args, start_timestamp, end_timestamp, not single
            )
        except MigrationError as error:
            failure_timestamp = str(error.failure_timestamp)
            if not failure_timestamp.isdigit():
                failure_timestamp = "<invalid>"
            raise click.ClickException(
                "H02_MIGRATION_EXECUTION_FAILED "
                f"profile={profile.identity.profile_id} "
                f"operation={operation.value} "
                f"failure_timestamp={failure_timestamp}"
            ) from None
        except Exception:
            raise click.ClickException(
                "H02_MIGRATION_EXECUTION_FAILED "
                f"profile={profile.identity.profile_id} "
                f"operation={operation.value}"
            ) from None

    log.info(f"Total gas used: {total_gas}")
    log.info("Done.")
    log.info("")


if __name__ == "__main__":
    cli()
