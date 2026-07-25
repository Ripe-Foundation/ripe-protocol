from __future__ import annotations

import socket
import subprocess
from dataclasses import replace
from pathlib import Path, PurePosixPath

import pytest
import requests

from config.network_profiles import (
    NETWORK_PROFILE_IDS,
    NetworkProfileError,
    Operation,
    OperationOutcome,
    PathState,
    VerifiedNetworkIdentity,
    get_profile,
    manifest_path,
    operation_decision,
    validate_registry,
)
from scripts import console, migrate, verify


ROOT = Path(__file__).resolve().parents[2]
PYTHON = Path(__import__("sys").executable)


@pytest.fixture(scope="session")
def ripe_hq():
    yield None


@pytest.fixture(autouse=True)
def no_external_network(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("external networking is disabled")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(requests.sessions.Session, "request", blocked)


def _run_module(module, *args):
    environment = {
        "PATH": __import__("os").defpath,
        "PYTHONPATH": str(ROOT),
    }
    return subprocess.run(
        [str(PYTHON), "-m", module, *args],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_base_mainnet_chain_id_is_8453():
    assert get_profile("base-mainnet").identity.chain_id == 8453


def test_base_mainnet_source_and_history_are_preserved():
    repository = get_profile("base-mainnet").repository
    assert repository.migration_dir == PurePosixPath(
        "migrations/base-mainnet"
    )
    assert repository.history_dir == PurePosixPath(
        "migration_history/base-mainnet/v1"
    )
    assert repository.migration_state is PathState.EXISTING
    assert repository.history_state is PathState.EXISTING


def test_generated_profile_choices_have_no_duplicates():
    assert len(NETWORK_PROFILE_IDS) == len(set(NETWORK_PROFILE_IDS))
    assert NETWORK_PROFILE_IDS == (
        "local",
        "base-mainnet",
        "base-sepolia",
        "robinhood-mainnet",
        "robinhood-testnet",
    )
    for command in (migrate.cli, console.main, verify.cli):
        option = next(
            parameter
            for parameter in command.params
            if parameter.name == "profile_id"
        )
        assert option.required is True
        assert tuple(option.type.choices) == NETWORK_PROFILE_IDS


@pytest.mark.parametrize(
    "module", ("scripts.migrate", "scripts.console", "scripts.verify")
)
def test_cli_default_policy_matches_help_and_runtime(module):
    help_result = _run_module(module, "--help")
    assert help_result.returncode == 0
    assert "[required]" in help_result.stdout
    assert "default: base-mainnet" not in help_result.stdout.lower()

    result = _run_module(module)
    assert result.returncode != 0
    assert "Missing option" in result.stderr
    assert "--profile" in result.stderr


def test_legacy_chain_option_resolves_only_to_canonical_base():
    result = _run_module(
        "scripts.verify", "--chain", "BASE-MAINNET"
    )
    assert result.returncode != 0
    assert "Manifest:" not in result.stdout
    assert "H02_VERIFIER_BLOCKED profile=base-mainnet" in result.stderr


def test_blocked_robinhood_verification_never_advertises_proposed_path():
    result = _run_module(
        "scripts.verify", "--profile", "robinhood-mainnet"
    )
    assert result.returncode != 0
    assert "Manifest:" not in result.stdout
    assert "migration_history/robinhood-mainnet" not in result.stdout
    assert "H02_VERIFIER_BLOCKED profile=robinhood-mainnet" in result.stderr


@pytest.mark.parametrize(
    ("option", "value", "error_code"),
    (
        ("--manifest", "../evil", "H02_REPOSITORY_UNAVAILABLE"),
        ("--environment", "bogus", "H02_HISTORY_ALIAS"),
    ),
)
def test_verify_validates_assertions_before_blocked_route(
    option, value, error_code
):
    result = _run_module(
        "scripts.verify",
        "--profile",
        "base-mainnet",
        option,
        value,
    )
    assert result.returncode != 0
    assert "Manifest:" not in result.stdout
    assert error_code in result.stderr
    assert value not in result.stderr


def test_unknown_label_never_resolves_to_base():
    with pytest.raises(NetworkProfileError, match="H02_PROFILE_UNKNOWN"):
        get_profile("totally-unknown")
    result = _run_module(
        "scripts.migrate", "--profile", "totally-unknown"
    )
    assert result.returncode != 0
    assert "Invalid value" in result.stderr
    assert "profile=base-mainnet" not in result.stderr


def test_base_sepolia_identity_valid_repository_unsupported():
    profile = get_profile("base-sepolia")
    assert profile.identity.chain_id == 84532
    assert profile.repository.migration_dir is None
    assert profile.repository.history_dir is None
    assert (
        operation_decision(profile, Operation.REPOSITORY_READ).outcome
        is OperationOutcome.UNSUPPORTED
    )
    assert (
        operation_decision(profile, Operation.MIGRATION_FORK).outcome
        is OperationOutcome.UNSUPPORTED
    )


@pytest.mark.parametrize("label", ("eth-mainnet", "eth-sepolia"))
def test_ethereum_labels_are_not_supported_profiles(label):
    with pytest.raises(NetworkProfileError, match="H02_PROFILE_UNKNOWN"):
        get_profile(label)
    result = _run_module("scripts.verify", "--profile", label)
    assert result.returncode != 0
    assert "Invalid value" in result.stderr


def test_base_manifest_path_remains_compatible():
    identity = VerifiedNetworkIdentity(
        "base-mainnet",
        Operation.REPOSITORY_READ,
        8453,
        8453,
    )
    selected = manifest_path(
        get_profile("base-mainnet"),
        "current",
        root=ROOT,
        identity=identity,
    )
    assert selected == (
        ROOT / "migration_history/base-mainnet/v1/current-manifest.json"
    )
    assert selected.is_file()


def test_base_manifest_read_failure_is_fail_closed(tmp_path):
    invalid_manifest = tmp_path / "current-manifest.json"
    invalid_manifest.write_text("{invalid")
    with pytest.raises(
        NetworkProfileError, match="H02_REPOSITORY_UNAVAILABLE"
    ):
        console.Console(
            "base-mainnet",
            Operation.CONSOLE_EVIDENCE,
            "reproducible pinned evidence",
            invalid_manifest,
        )


@pytest.mark.parametrize(
    "module", ("scripts.migrate", "scripts.console", "scripts.verify")
)
def test_import_and_help_need_no_base_explorer_key(module):
    result = _run_module(module, "--help")
    assert result.returncode == 0, result.stderr
    assert "BASESCAN_API_KEY" not in result.stderr
    assert "ETHERSCAN_API_KEY" not in result.stderr


def test_no_alchemy_token_url_construction():
    for path in (
        ROOT / "config/network_profiles.py",
        ROOT / "scripts/migrate.py",
        ROOT / "scripts/console.py",
        ROOT / "scripts/verify.py",
    ):
        source = path.read_text()
        assert "WEB3_ALCHEMY_API_KEY" not in source
        assert ".g.alchemy.com" not in source


def test_no_test_key_fallback_regression():
    # These source-text assertions are cheap tripwires; behavioral secret and
    # account-boundary tests provide the authority proof.
    source = (ROOT / "scripts/utils/migration_helpers.py").read_text()
    assert "TEST_PRIVATE_KEY" not in source
    assert "ac0974bec39a" not in source
    assert "else TEST_" not in source


def test_no_rpc_logging_regression():
    # Text checks complement the behavioral redaction tests that capture the
    # successful and failing CLI paths.
    migrate_source = (ROOT / "scripts/migrate.py").read_text()
    console_source = (ROOT / "scripts/console.py").read_text()
    assert "final_rpc[:" not in migrate_source + console_source
    assert "Connected to rpc" not in migrate_source
    assert "via {final_rpc" not in console_source
    assert "value=<redacted>" in migrate_source
    assert "value=<redacted>" in console_source


def test_unknown_provider_returns_typed_outcome_not_keyerror():
    profile = get_profile("base-mainnet")
    invalid_verifier = replace(profile.verifier, provider="unknown")
    with pytest.raises(NetworkProfileError, match="H02_PROFILE_INVALID"):
        validate_registry((replace(profile, verifier=invalid_verifier),))


def test_base_verification_route_is_truthfully_blocked(monkeypatch):
    calls = []
    monkeypatch.setattr(
        requests.sessions.Session,
        "request",
        lambda *args, **kwargs: calls.append(args),
    )
    with pytest.raises(Exception) as captured:
        verify.cli.callback("base-mainnet", None, "current")
    assert "H02_VERIFIER_BLOCKED" in str(captured.value)
    assert calls == []


def test_committed_base_history_inventory_is_unchanged():
    checkout = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if checkout.returncode != 0 or checkout.stdout.strip() != "true":
        pytest.skip("requires a Git worktree")

    result = subprocess.run(
        [
            "git",
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--",
            "migration_history/base-mainnet/v1",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
