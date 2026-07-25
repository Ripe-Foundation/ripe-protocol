from __future__ import annotations

import ast
import os
import socket
import subprocess
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests

from config.network_profiles import (
    NetworkProfileError,
    Operation,
    RedactedRpc,
    VerifiedNetworkIdentity,
    get_profile,
    resolve_rpc_reference,
    verify_chain_identity,
)
from scripts import console, migrate, verify
from scripts.utils import migration_helpers
from scripts.utils.migration_runner import MigrationError


ROOT = Path(__file__).resolve().parents[2]
PYTHON = Path(__import__("sys").executable)
RELEVANT_ENV = (
    "BASESCAN_API_KEY",
    "ETHERSCAN_API_KEY",
    "WEB3_ALCHEMY_API_KEY",
    "BASE_MAINNET_RPC_URL",
    "BASE_SEPOLIA_RPC_URL",
    "ROBINHOOD_MAINNET_RPC_URL",
    "ROBINHOOD_TESTNET_RPC_URL",
    "DEPLOYER_PRIVATE_KEY",
    "TEST_PRIVATE_KEY",
)
_PUBLIC_ANVIL_TEST_KEY = (
    "0x"
    "ac0974bec39a17e36ba4a6b4d238ff944"
    "bacb478cbed5efcae784d7bf4f2ff80"
)
_SENSITIVE_RPC = (
    "https://synthetic-user:synthetic-password@rpc.invalid.example/"
    "path-token?api_key=query-token#fragment-token"
)


@pytest.fixture(scope="session")
def ripe_hq():
    yield None


@pytest.fixture(autouse=True)
def isolated_environment_and_network(monkeypatch):
    for name in RELEVANT_ENV:
        monkeypatch.delenv(name, raising=False)

    def blocked(*args, **kwargs):
        raise AssertionError("external networking is disabled")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(requests.sessions.Session, "request", blocked)


class SpyEnvironment(dict):
    def __init__(self, values=()):
        super().__init__(values)
        self.accesses = []

    def __getitem__(self, name):
        self.accesses.append(name)
        return super().__getitem__(name)


def _child_environment():
    return {
        "PATH": os.defpath,
        "PYTHONPATH": str(ROOT),
    }


def _run_child(*args):
    return subprocess.run(
        [str(PYTHON), *args],
        cwd=ROOT,
        env=_child_environment(),
        capture_output=True,
        text=True,
        check=False,
    )


def _verified(profile_id, operation):
    profile = get_profile(profile_id)
    assert profile.identity.chain_id is not None
    return VerifiedNetworkIdentity(
        profile_id,
        operation,
        profile.identity.chain_id,
        profile.identity.chain_id,
    )


def _call_migrate(**overrides):
    values = {
        "ask": False,
        "safe": "",
        "fork": True,
        "is_retry": False,
        "rpc": "https://rpc.invalid.example",
        "single": False,
        "environment": "v1",
        "start_timestamp": "0",
        "end_timestamp": "0",
        "profile_id": "base-mainnet",
        "blueprint": None,
        "account": "DEPLOYER",
        "ledger": -1,
    }
    values.update(overrides)
    return migrate.cli.callback(**values)


def _prepare_migration_execution(monkeypatch, run):
    sender = SimpleNamespace(
        address="0x0000000000000000000000000000000000000001"
    )
    monkeypatch.setattr(migrate, "read_chain_id", lambda value: 8453)
    monkeypatch.setattr(migrate, "get_account", lambda *args: sender)
    monkeypatch.setattr(migrate, "load_vyper_files", lambda: {})
    monkeypatch.setattr(
        migrate,
        "MigrationRunner",
        lambda *args: SimpleNamespace(run=run),
    )
    monkeypatch.setattr(
        migrate.boa.deployments,
        "DeploymentsDB",
        lambda *args: object(),
    )
    monkeypatch.setattr(
        migrate.boa.deployments,
        "set_deployments_db",
        lambda *args: None,
    )

    @contextmanager
    def fake_fork(rpc_url, **kwargs):
        assert rpc_url == _SENSITIVE_RPC
        yield SimpleNamespace(set_balance=lambda *args: None)

    monkeypatch.setattr(migrate.boa, "fork", fake_fork)


@pytest.mark.parametrize(
    "module",
    (
        "config.network_profiles",
        "scripts.migrate",
        "scripts.console",
        "scripts.verify",
        "scripts.utils.migration_helpers",
    ),
)
def test_h02_modules_import_without_relevant_env(module):
    result = _run_child("-c", f"import {module}")
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "module",
    ("scripts.migrate", "scripts.console", "scripts.verify"),
)
def test_cli_help_without_relevant_env(module):
    result = _run_child("-m", module, "--help")
    assert result.returncode == 0, result.stderr
    assert "--profile" in result.stdout
    assert "[required]" in result.stdout


def test_rpc_env_read_only_for_required_operation():
    blocked_environment = SpyEnvironment(
        {"ROBINHOOD_MAINNET_RPC_URL": "https://rpc.invalid.example"}
    )
    with pytest.raises(NetworkProfileError, match="H02_OPERATION_BLOCKED"):
        resolve_rpc_reference(
            get_profile("robinhood-mainnet"),
            Operation.MIGRATION_LIVE,
            blocked_environment,
        )
    assert blocked_environment.accesses == []

    required_environment = SpyEnvironment(
        {"BASE_MAINNET_RPC_URL": "https://rpc.invalid.example"}
    )
    rpc = resolve_rpc_reference(
        get_profile("base-mainnet"),
        Operation.MIGRATION_FORK,
        required_environment,
    )
    assert required_environment.accesses == ["BASE_MAINNET_RPC_URL"]
    assert rpc.reference == "BASE_MAINNET_RPC_URL"


def test_missing_rpc_env_fails_lazily():
    environment = SpyEnvironment()
    with pytest.raises(NetworkProfileError, match="H02_RPC_ENV_MISSING"):
        resolve_rpc_reference(
            get_profile("base-mainnet"),
            Operation.MIGRATION_FORK,
            environment,
        )
    assert environment.accesses == ["BASE_MAINNET_RPC_URL"]


def test_missing_private_key_never_uses_public_fallback(monkeypatch):
    calls = []
    monkeypatch.setattr(
        migration_helpers.Account,
        "from_key",
        lambda value: calls.append(value),
    )
    with pytest.raises(NetworkProfileError, match="H02_PRIVATE_KEY_MISSING"):
        migration_helpers.get_account(
            "DEPLOYER",
            _verified("base-mainnet", Operation.MIGRATION_FORK),
            Operation.MIGRATION_FORK,
            environ=SpyEnvironment(),
        )
    assert calls == []


def test_public_local_key_is_test_only():
    occurrences = []
    # This scanner intentionally searches for the one contiguous production
    # hazard; this test's fixture is split so it cannot itself satisfy the scan.
    for directory in (ROOT / "config", ROOT / "scripts", ROOT / "tests"):
        for path in directory.rglob("*.py"):
            if _PUBLIC_ANVIL_TEST_KEY in path.read_text():
                occurrences.append(path.relative_to(ROOT))
    assert occurrences == [Path("tests/tokens/test_signatures.py")]

    for directory in (ROOT / "config", ROOT / "scripts"):
        for path in directory.rglob("*.py"):
            tree = ast.parse(path.read_text(), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    assert "tests.deployment.test_secret_handling" not in (
                        ast.unparse(node)
                    )


def test_explicit_local_test_key_requires_local_runtime(monkeypatch):
    loaded = []
    monkeypatch.setattr(
        migration_helpers.Account,
        "from_key",
        lambda value: loaded.append(value) or object(),
    )
    local_identity = VerifiedNetworkIdentity(
        "local", Operation.LOCAL_RUNTIME, 31337, 31337
    )
    account = migration_helpers.get_account(
        "LOCAL_TEST",
        local_identity,
        Operation.LOCAL_RUNTIME,
        private_key=_PUBLIC_ANVIL_TEST_KEY,
        local_test_only=True,
    )
    assert account is not None
    assert loaded == [_PUBLIC_ANVIL_TEST_KEY]


@pytest.mark.parametrize(
    ("identity", "operation", "error_code"),
    (
        (
            VerifiedNetworkIdentity(
                "base-mainnet", Operation.MIGRATION_FORK, 8453, 8453
            ),
            Operation.MIGRATION_FORK,
            "H02_ACCOUNT_BACKEND_UNAPPROVED",
        ),
        (
            VerifiedNetworkIdentity(
                "base-mainnet", Operation.MIGRATION_LIVE, 8453, 8453
            ),
            Operation.MIGRATION_LIVE,
            "H02_OPERATION_BLOCKED",
        ),
    ),
)
def test_injected_local_test_account_rejected_for_live_or_fork(
    identity, operation, error_code, monkeypatch
):
    calls = []
    monkeypatch.setattr(
        migration_helpers.Account,
        "from_key",
        lambda value: calls.append(value),
    )
    with pytest.raises(NetworkProfileError, match=error_code):
        migration_helpers.get_account(
            "LOCAL_TEST",
            identity,
            operation,
            private_key=_PUBLIC_ANVIL_TEST_KEY,
            local_test_only=True,
        )
    assert calls == []


def test_wrong_chain_prevents_private_key_mapping_access(monkeypatch):
    events = []
    monkeypatch.setattr(
        migrate, "read_chain_id", lambda value: events.append("chain") or 1
    )
    monkeypatch.setattr(
        migrate,
        "get_account",
        lambda *args, **kwargs: events.append("account"),
    )
    monkeypatch.setattr(
        migrate,
        "repository_paths",
        lambda *args, **kwargs: events.append("history"),
    )
    with pytest.raises(Exception) as captured:
        _call_migrate()
    assert "H02_CHAIN_ID_MISMATCH" in str(captured.value)
    assert events == ["chain"]


@pytest.mark.parametrize(
    ("identity", "operation", "error_code"),
    (
        (
            VerifiedNetworkIdentity(
                "base-mainnet", Operation.MIGRATION_FORK, 8453, 1
            ),
            Operation.MIGRATION_FORK,
            "H02_CHAIN_ID_MISMATCH",
        ),
        (
            VerifiedNetworkIdentity(
                "base-mainnet", Operation.MIGRATION_FORK, 1, 1
            ),
            Operation.MIGRATION_FORK,
            "H02_CHAIN_ID_MISMATCH",
        ),
        (
            VerifiedNetworkIdentity(
                "unknown-profile", Operation.MIGRATION_FORK, 1, 1
            ),
            Operation.MIGRATION_FORK,
            "H02_PROFILE_UNKNOWN",
        ),
        (
            VerifiedNetworkIdentity(
                "robinhood-mainnet",
                Operation.MIGRATION_FORK,
                4663,
                4663,
            ),
            Operation.MIGRATION_FORK,
            "H02_OPERATION_BLOCKED",
        ),
        (
            VerifiedNetworkIdentity(
                "base-mainnet",
                Operation.REPOSITORY_READ,
                8453,
                8453,
            ),
            Operation.REPOSITORY_READ,
            "H02_ACCOUNT_BACKEND_UNAPPROVED",
        ),
    ),
)
def test_account_identity_validation_precedes_key_access(
    identity, operation, error_code, monkeypatch
):
    environment = SpyEnvironment({"DEPLOYER_PRIVATE_KEY": "not-read"})
    account_calls = []
    monkeypatch.setattr(
        migration_helpers.Account,
        "from_key",
        lambda value: account_calls.append(value),
    )

    with pytest.raises(NetworkProfileError, match=error_code):
        migration_helpers.get_account(
            "DEPLOYER",
            identity,
            operation,
            environ=environment,
        )

    assert environment.accesses == []
    assert account_calls == []


def test_console_wrong_chain_prevents_manifest_and_fork(monkeypatch):
    events = []
    monkeypatch.setattr(
        console, "read_chain_id", lambda value: events.append("chain") or 1
    )
    monkeypatch.setattr(
        console,
        "Console",
        lambda *args, **kwargs: events.append("manifest"),
    )
    monkeypatch.setattr(
        console.boa,
        "fork",
        lambda *args, **kwargs: events.append("fork"),
    )
    with pytest.raises(Exception) as captured:
        console.main.callback(
            "base-mainnet",
            None,
            None,
            "https://rpc.invalid.example",
            "",
            None,
            False,
        )
    assert "H02_CHAIN_ID_MISMATCH" in str(captured.value)
    assert events == ["chain"]


def test_rpc_components_never_appear_in_logs_exceptions_or_repr():
    profile = get_profile("base-mainnet")
    operation = Operation.MIGRATION_FORK
    rpc = RedactedRpc(_SENSITIVE_RPC, "base-mainnet", operation, "--rpc")

    with pytest.raises(NetworkProfileError) as captured:
        verify_chain_identity(
            profile,
            operation,
            rpc,
            lambda value: (_ for _ in ()).throw(RuntimeError(value)),
        )
    rendered = f"{rpc} {rpc!r} {captured.value} {captured.value!r}"
    for component in (
        _SENSITIVE_RPC,
        "synthetic-user",
        "synthetic-password",
        "path-token",
        "query-token",
        "fragment-token",
    ):
        assert component not in rendered


def test_user_supplied_rpc_is_fully_redacted(monkeypatch):
    monkeypatch.setattr(migrate, "read_chain_id", lambda value: 1)
    with pytest.raises(Exception) as captured:
        _call_migrate(rpc=_SENSITIVE_RPC)
    rendered = f"{captured.value} {captured.value!r}"
    for component in (
        _SENSITIVE_RPC,
        "synthetic-user",
        "synthetic-password",
        "path-token",
        "query-token",
        "fragment-token",
    ):
        assert component not in rendered


def test_successful_migration_log_path_fully_redacts_rpc(monkeypatch, capsys):
    _prepare_migration_execution(
        monkeypatch,
        lambda *args: 123,
    )
    _call_migrate(rpc=_SENSITIVE_RPC)

    rendered = capsys.readouterr().out
    assert "value=<redacted>" in rendered
    assert "may write manifests under" in rendered
    for component in (
        _SENSITIVE_RPC,
        "synthetic-user",
        "synthetic-password",
        "path-token",
        "query-token",
        "fragment-token",
    ):
        assert component not in rendered


def test_migration_failure_preserves_sanitized_resume_timestamp(monkeypatch):
    def fail(*args):
        raise MigrationError("1712345678")

    _prepare_migration_execution(monkeypatch, fail)
    with pytest.raises(Exception) as captured:
        _call_migrate(rpc=_SENSITIVE_RPC)
    rendered = str(captured.value)
    assert "H02_MIGRATION_EXECUTION_FAILED" in rendered
    assert "failure_timestamp=1712345678" in rendered
    assert _SENSITIVE_RPC not in rendered


def test_explorer_key_is_not_read_at_import_or_help():
    for module in ("scripts.migrate", "scripts.console", "scripts.verify"):
        result = _run_child("-m", module, "--help")
        assert result.returncode == 0, result.stderr
        assert "KeyError" not in result.stderr


def test_unsupported_verifier_does_not_read_key(monkeypatch):
    environment = SpyEnvironment(
        {"ETHERSCAN_API_KEY": "synthetic-explorer-value"}
    )
    monkeypatch.setattr(os, "environ", environment)
    with pytest.raises(Exception) as captured:
        verify.cli.callback("base-mainnet", None, "current")
    rendered = f"{captured.value} {captured.value!r}"
    assert "H02_VERIFIER_BLOCKED" in rendered
    assert environment.accesses == []


def test_process_environment_is_not_dumped_or_persisted(
    monkeypatch, tmp_path, capsys
):
    marker = "synthetic-process-environment-marker"
    monkeypatch.setenv("H02_UNRELATED_MARKER", marker)
    monkeypatch.setattr(migrate, "read_chain_id", lambda value: 1)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(Exception) as captured:
        _call_migrate()
    rendered = capsys.readouterr().out + str(captured.value)
    assert marker not in rendered
    for path in tmp_path.rglob("*"):
        if path.is_file():
            assert marker not in path.read_text(errors="ignore")


def test_dotenv_is_not_loaded_by_h02_modules():
    result = _run_child(
        "-c",
        (
            "import dotenv\n"
            "def fail(*args, **kwargs):\n"
            "    raise AssertionError('dotenv loader called')\n"
            "dotenv.load_dotenv = fail\n"
            "import config.network_profiles\n"
            "import scripts.migrate\n"
            "import scripts.console\n"
            "import scripts.verify\n"
            "import scripts.utils.migration_helpers\n"
        ),
    )
    assert result.returncode == 0, result.stderr


def test_console_session_error_is_not_mislabeled_as_rpc_failure(monkeypatch):
    monkeypatch.setattr(console, "read_chain_id", lambda value: 8453)
    fake_console = SimpleNamespace(
        _profile_id="base-mainnet",
        _mode="local exploration",
        _manifest={},
        c=object(),
    )
    monkeypatch.setattr(console, "Console", lambda *args: fake_console)

    @contextmanager
    def fake_fork(rpc_url, **kwargs):
        yield SimpleNamespace()

    monkeypatch.setattr(console.boa, "fork", fake_fork)

    import IPython

    def fail_session(*args, **kwargs):
        raise RuntimeError("synthetic session failure")

    monkeypatch.setattr(IPython, "embed", fail_session)
    with pytest.raises(
        RuntimeError, match="synthetic session failure"
    ) as error:
        console.main.callback(
            "base-mainnet",
            None,
            None,
            "https://rpc.invalid.example",
            "",
            None,
            False,
        )
    assert "H02_RPC_CONNECT_FAILED" not in str(error.value)


@pytest.mark.parametrize(
    "backend_values",
    ({"safe": "synthetic-safe"}, {"ledger": 0}),
)
def test_safe_and_ledger_reject_before_secret_access(
    backend_values, monkeypatch
):
    events = []
    monkeypatch.setattr(
        migrate, "read_chain_id", lambda value: events.append("chain")
    )
    monkeypatch.setattr(
        migrate,
        "get_account",
        lambda *args, **kwargs: events.append("account"),
    )
    with pytest.raises(Exception) as captured:
        _call_migrate(rpc=None, **backend_values)
    assert "H02_ACCOUNT_BACKEND_UNAPPROVED" in str(captured.value)
    assert events == []
