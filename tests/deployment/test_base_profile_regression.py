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


def test_legacy_chain_option_resolves_only_to_canonical_base():
    # A case variant must not be silently folded onto the canonical chain:
    # `verify` looks the label up verbatim and refuses anything it misses.
    result = _run_module(
        "scripts.verify", "--chain", "BASE-MAINNET"
    )
    assert result.returncode != 0
    assert "Manifest:" not in result.stdout
    assert "Unknown chain" in result.stderr


def test_blocked_robinhood_verification_never_advertises_proposed_path():
    # Robinhood manifests exist on disk, so the refusal has to land before the
    # manifest path is resolved or printed -- otherwise the output implies a
    # verification route that cannot exist.
    result = _run_module(
        "scripts.verify", "--chain", "robinhood-mainnet"
    )
    assert result.returncode != 0
    assert "Manifest:" not in result.stdout
    assert "migration_history/robinhood-mainnet" not in result.stdout
    assert "has no Etherscan-family verifier configured" in result.stderr
    assert "verify_blockscout" in result.stderr


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


def test_unknown_provider_returns_typed_outcome_not_keyerror():
    profile = get_profile("base-mainnet")
    invalid_verifier = replace(profile.verifier, provider="unknown")
    with pytest.raises(NetworkProfileError, match="H02_PROFILE_INVALID"):
        validate_registry((replace(profile, verifier=invalid_verifier),))


def test_unresolvable_chain_fails_before_any_network_call(monkeypatch):
    calls = []
    monkeypatch.setattr(
        requests.sessions.Session,
        "request",
        lambda *args, **kwargs: calls.append(args),
    )
    # `chain` is unset here, which is the shape a scripted run takes when it
    # forgets the option. The refusal must precede any submission attempt.
    with pytest.raises(Exception) as captured:
        verify.cli.callback("base-mainnet", None, "current")
    assert "Unknown chain" in str(captured.value)
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


# --- verify.py input containment -------------------------------------------
#
# `verify` submits contract records with a live explorer credential, so the
# manifest it reads must come from inside the selected history directory. The
# path was previously built by interpolating the three options straight into a
# format string, which let `--environment`/`--manifest` walk out of the tree.


@pytest.mark.parametrize(
    ("option", "value", "label"),
    (
        ("--environment", "../../..", "parent traversal"),
        ("--manifest", "../../../../etc/passwd", "deep traversal"),
        ("--environment", "/etc", "absolute path"),
        ("--manifest", "/etc/passwd", "absolute manifest"),
        ("--environment", "a/b", "forward separator"),
        ("--manifest", "a\\b", "backslash separator"),
        ("--environment", ".", "single dot"),
        ("--environment", "..", "double dot"),
        ("--environment", "", "empty segment"),
    ),
)
def test_verify_rejects_noncanonical_path_segments(option, value, label):
    result = _run_module("scripts.verify", option, value)

    assert result.returncode != 0, label
    # It must fail before a path is built, so nothing path-shaped is printed.
    assert "migration_history" not in result.stdout, label
    assert "migration_history" not in result.stderr, label
    # And the rejected value is not echoed back into logs.
    if value not in ("", ".", ".."):
        assert value not in result.stderr, label
        assert value not in result.stdout, label


def test_verify_resolved_manifest_stays_inside_history_directory():
    root = (ROOT / "migration_history").resolve()
    resolved = verify._history_manifest_path("base-mainnet", "v1", "current")

    assert resolved.is_relative_to(root)
    assert resolved == root / "base-mainnet/v1/current-manifest.json"


@pytest.mark.parametrize("label", ("BASE-MAINNET", "Base-Mainnet", "bogus-chain", "local"))
def test_verify_rejects_unknown_chain_without_blockscout_advice(label):
    result = _run_module("scripts.verify", "--chain", label)

    assert result.returncode != 0
    assert "Unknown chain" in result.stderr
    # A typo or a case variant is not a Robinhood problem; sending it to the
    # Blockscout script would be false advice.
    assert "verify_blockscout" not in result.stderr


@pytest.mark.parametrize(
    ("chain", "expect_blockscout"),
    (
        ("robinhood-mainnet", True),
        # verify_blockscout targets Robinhood mainnet only, so testnet and the
        # retired goerli networks must not be pointed at it.
        ("robinhood-testnet", False),
        ("base-goerli", False),
        ("eth-goerli", False),
    ),
)
def test_verify_separates_unsupported_provider_from_unknown_chain(
    chain, expect_blockscout
):
    result = _run_module("scripts.verify", "--chain", chain)

    assert result.returncode != 0
    assert "no Etherscan-family verifier configured" in result.stderr
    assert "Unknown chain" not in result.stderr
    assert ("verify_blockscout" in result.stderr) is expect_blockscout


def test_verify_reports_missing_manifest_for_canonical_segments():
    result = _run_module(
        "scripts.verify", "--chain", "base-mainnet", "--environment", "v999"
    )

    assert result.returncode != 0
    assert "No manifest found" in result.stderr


def test_verification_policy_and_verify_cli_disagree_by_design():
    """Characterization: the registry blocks VERIFICATION, the CLI ignores it.

    `verify.py` was wired to `verify_from_manifest` in this cleanup, so it now
    has a real submission path -- but it resolves chains from
    `verify_etherscan.CHAIN_SPECS` and never calls `operation_decision`. The
    profile registry still records VERIFICATION as blocked.

    This test exists so the contradiction is explicit and tracked. Wiring the
    CLI through the registry should flip the policy to SUPPORTED and delete
    this test in the same change; until then, the mismatch must not be
    mistaken for enforcement.
    """
    profile = get_profile("base-mainnet")
    decision = operation_decision(profile, Operation.VERIFICATION)
    assert decision.outcome is OperationOutcome.BLOCKED_PENDING_POLICY

    # The CLI does not consult that decision: base-mainnet resolves and gets
    # as far as the manifest/key checks rather than being refused as blocked.
    source = (ROOT / "scripts/verify.py").read_text()
    assert "operation_decision" not in source
    assert "network_profiles" not in source

    result = _run_module(
        "scripts.verify", "--chain", "base-mainnet", "--environment", "v999"
    )
    assert "No manifest found" in result.stderr
    assert "BLOCKED_PENDING_POLICY" not in result.stderr
