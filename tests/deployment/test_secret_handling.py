from __future__ import annotations

import ast
import os
import socket
import subprocess
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import eth_account
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

    def __contains__(self, name):
        self.accesses.append(name)
        return super().__contains__(name)

    def get(self, name, default=None):
        self.accesses.append(name)
        return super().get(name, default)

    def setdefault(self, name, default=None):
        self.accesses.append(name)
        return super().setdefault(name, default)

    def copy(self):
        self.accesses.append("<copy>")
        return super().copy()


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


def test_spy_environment_records_common_read_paths():
    environment = SpyEnvironment({"KEY": "value"})
    assert environment["KEY"] == "value"
    assert environment.get("KEY") == "value"
    assert "KEY" in environment
    assert environment.setdefault("OTHER", "default") == "default"
    assert environment.copy()["KEY"] == "value"
    assert environment.accesses == [
        "KEY",
        "KEY",
        "KEY",
        "OTHER",
        "<copy>",
    ]


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


def test_rpc_env_read_only_for_required_operation():
    blocked_environment = SpyEnvironment(
        {"ROBINHOOD_MAINNET_RPC_URL": "https://rpc.invalid.example"}
    )
    with pytest.raises(NetworkProfileError, match="H02_OPERATION_BLOCKED"):
        resolve_rpc_reference(
            get_profile("robinhood-mainnet"),
            # MIGRATION_LIVE is owner-approved now; CONSOLE_EVIDENCE is the
            # remaining blocked operation that still requires RPC.
            Operation.CONSOLE_EVIDENCE,
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


@pytest.mark.parametrize("explicit_rpc", ("", "not-a-valid-rpc"))
def test_invalid_explicit_rpc_never_reads_environment(explicit_rpc):
    environment = SpyEnvironment(
        {"BASE_MAINNET_RPC_URL": "https://fallback.invalid.example"}
    )
    with pytest.raises(NetworkProfileError, match="H02_RPC_INVALID"):
        resolve_rpc_reference(
            get_profile("base-mainnet"),
            Operation.MIGRATION_FORK,
            environment,
            explicit_rpc=explicit_rpc,
        )
    assert environment.accesses == []


def test_missing_rpc_env_fails_lazily():
    environment = SpyEnvironment()
    with pytest.raises(NetworkProfileError, match="H02_RPC_ENV_MISSING"):
        resolve_rpc_reference(
            get_profile("base-mainnet"),
            Operation.MIGRATION_FORK,
            environment,
        )
    assert environment.accesses == ["BASE_MAINNET_RPC_URL"]


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


def test_execute_transaction_failure_never_logs_exception_text(capsys):
    failure_text = f"synthetic provider failure {_SENSITIVE_RPC}"

    def fail():
        raise RuntimeError(failure_text)

    result = migration_helpers.execute_transaction(fail, no_retry=True)
    rendered = capsys.readouterr().out

    assert result is None
    assert "H02_TRANSACTION_FAILED" in rendered
    assert failure_text not in rendered
    assert "synthetic provider failure" not in rendered
    for component in (
        _SENSITIVE_RPC,
        "synthetic-user",
        "synthetic-password",
        "path-token",
        "query-token",
        "fragment-token",
    ):
        assert component not in rendered


def test_explorer_key_is_not_read_at_import_or_help():
    for module in ("scripts.migrate", "scripts.console", "scripts.verify"):
        result = _run_child("-m", module, "--help")
        assert result.returncode == 0, result.stderr
        assert "KeyError" not in result.stderr


@pytest.mark.parametrize(
    ("environment_name", "chain", "expected"),
    (
        # Unset chain: the shape a scripted run takes when it drops the option.
        ("base-mainnet", None, "Unknown chain"),
        # Robinhood has committed manifests, so this route gets far enough to
        # matter -- it must still refuse before the explorer key is read. A
        # known chain without a provider is a different failure from an
        # unknown one, and reports differently.
        (
            "v1",
            "robinhood-mainnet",
            "has no Etherscan-family verifier configured",
        ),
    ),
)
def test_unsupported_verifier_does_not_read_key(
    environment_name, chain, expected, monkeypatch
):
    environment = SpyEnvironment(
        {"ETHERSCAN_API_KEY": "synthetic-explorer-value"}
    )
    monkeypatch.setattr(os, "environ", environment)
    with pytest.raises(Exception) as captured:
        verify.cli.callback(environment_name, chain, "current")
    rendered = f"{captured.value} {captured.value!r}"
    assert expected in rendered
    assert environment.accesses == []


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

    IPython = pytest.importorskip("IPython")

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


# Safe and Ledger are approved backends for Base on their own, so neither is
# rejected in isolation any more. Requesting BOTH is still unapproved, and it is
# rejected on the same path with the same code -- which is what this test is
# actually about: an unapproved backend never reaches a chain read or a secret.


# --- _local_account -------------------------------------------------------
#
# ab3100d removed the H-02 `migration_helpers.get_account`, which had the only
# direct missing-key coverage. `scripts.migrate._local_account` is now the
# normal private-key loader on the live deploy path and had none of its own.

# Well formed (any in-range 32 bytes is a real key), used with a faked loader.
_WELL_FORMED_TEST_KEY = "0x" + "ab" * 31 + "cd"
# Genuinely malformed: wrong length and non-hex, so eth_account rejects it.
_MALFORMED_TEST_KEY = "0xnot-a-real-private-key-value"


def test_local_account_missing_key_raises_before_reading_the_key(monkeypatch):
    loaded = []
    monkeypatch.setattr(
        eth_account.Account, "from_key", lambda value: loaded.append(value)
    )
    monkeypatch.delenv("DEPLOYER_PRIVATE_KEY", raising=False)

    with pytest.raises(migrate.click.ClickException) as captured:
        migrate._local_account("DEPLOYER")

    assert "DEPLOYER_PRIVATE_KEY is not set" in str(captured.value)
    # The loader must not be reached at all when the key is absent.
    assert loaded == []


def test_local_account_has_no_well_known_key_fallback(monkeypatch):
    monkeypatch.delenv("DEPLOYER_PRIVATE_KEY", raising=False)

    with pytest.raises(migrate.click.ClickException) as captured:
        migrate._local_account("DEPLOYER")

    rendered = f"{captured.value} {captured.value!r}"
    assert _PUBLIC_ANVIL_TEST_KEY not in rendered
    assert "0x" not in rendered.replace("0x0", "")


def test_local_account_invalid_key_never_appears_in_the_failure(monkeypatch):
    monkeypatch.setenv("DEPLOYER_PRIVATE_KEY", _MALFORMED_TEST_KEY)

    with pytest.raises(Exception) as captured:
        migrate._local_account("DEPLOYER")

    rendered = f"{captured.value} {captured.value!r} {captured.traceback}"
    assert _MALFORMED_TEST_KEY not in rendered
    assert _MALFORMED_TEST_KEY[2:] not in rendered


def test_local_account_loads_a_valid_key(monkeypatch):
    seen = []

    def fake_from_key(value):
        seen.append(value)
        return SimpleNamespace(address="0x" + "5" * 40)

    monkeypatch.setattr(eth_account.Account, "from_key", fake_from_key)
    monkeypatch.setenv("DEPLOYER_PRIVATE_KEY", _WELL_FORMED_TEST_KEY)

    account = migrate._local_account("DEPLOYER")

    assert account.address == "0x" + "5" * 40
    assert seen == [_WELL_FORMED_TEST_KEY]


def test_local_account_reads_only_the_named_account_variable(monkeypatch):
    monkeypatch.delenv("TREASURY_PRIVATE_KEY", raising=False)
    monkeypatch.setenv("DEPLOYER_PRIVATE_KEY", _WELL_FORMED_TEST_KEY)

    with pytest.raises(migrate.click.ClickException) as captured:
        migrate._local_account("TREASURY")

    assert "TREASURY_PRIVATE_KEY is not set" in str(captured.value)
    assert _WELL_FORMED_TEST_KEY not in str(captured.value)


def test_ledger_branch_bypasses_local_account_entirely():
    # `--ledger` must sign with the device, never fall back to an env key.
    source = (ROOT / "scripts/migrate.py").read_text()
    ledger_branch = source.split("elif ledger != -1:")[1].split("else:")[0]

    assert "LedgerAccount(final_rpc, ledger)" in ledger_branch
    assert "_local_account" not in ledger_branch
