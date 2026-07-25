from __future__ import annotations

import socket
from dataclasses import FrozenInstanceError, fields, replace
from pathlib import Path, PurePosixPath

import pytest
import requests

from config.network_profiles import (
    NETWORK_PROFILES,
    NETWORK_PROFILE_IDS,
    ForkPolicy,
    NetworkProfile,
    NetworkProfileError,
    Operation,
    OperationOutcome,
    PathState,
    ProfileAlias,
    RedactedRpc,
    VerifiedNetworkIdentity,
    canonical_profile_ids,
    get_profile,
    operation_decision,
    repository_paths,
    resolve_rpc_reference,
    validate_fork_request,
    validate_registry,
    verify_chain_identity,
)


@pytest.fixture(scope="session")
def ripe_hq():
    yield None


@pytest.fixture(autouse=True)
def no_external_network(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("external networking is disabled")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(requests.sessions.Session, "request", blocked)


def profile_factory(
    profile_id: str = "base-mainnet", **overrides
) -> NetworkProfile:
    profile = get_profile(profile_id)
    return replace(profile, **overrides)


def verified(profile_id: str, operation: Operation):
    profile = get_profile(profile_id)
    assert profile.identity.chain_id is not None
    return VerifiedNetworkIdentity(
        profile_id,
        operation,
        profile.identity.chain_id,
        profile.identity.chain_id,
    )


def test_all_five_canonical_profiles_and_chain_ids():
    assert canonical_profile_ids() == (
        "local",
        "base-mainnet",
        "base-sepolia",
        "robinhood-mainnet",
        "robinhood-testnet",
    )
    assert {
        profile.identity.profile_id: profile.identity.chain_id
        for profile in NETWORK_PROFILES
    } == {
        "local": None,
        "base-mainnet": 8453,
        "base-sepolia": 84532,
        "robinhood-mainnet": 4663,
        "robinhood-testnet": 46630,
    }


def test_profile_and_nested_values_are_immutable():
    profile = get_profile("base-mainnet")
    with pytest.raises(FrozenInstanceError):
        profile.identity.chain_id = 1
    with pytest.raises(FrozenInstanceError):
        profile.repository.history_dir = PurePosixPath("other")
    with pytest.raises(AttributeError):
        profile.rpc.allowed_operations.add(Operation.VERIFICATION)
    assert isinstance(profile.operations, tuple)
    assert isinstance(profile.live_account_backend_ids, tuple)


def test_operation_table_is_total_and_uses_required_vocabulary():
    allowed = set(OperationOutcome)
    for profile in NETWORK_PROFILES:
        assert len(profile.operations) == len(Operation)
        assert {policy.operation for policy in profile.operations} == set(
            Operation
        )
        assert {policy.outcome for policy in profile.operations} <= allowed


def test_unknown_profile_fails_closed():
    events = []
    with pytest.raises(NetworkProfileError, match="H02_PROFILE_UNKNOWN"):
        get_profile("unknown-profile")
    assert events == []


def test_duplicate_canonical_profile_id_is_invalid():
    duplicate = profile_factory()
    with pytest.raises(NetworkProfileError, match="H02_PROFILE_INVALID"):
        validate_registry((duplicate, duplicate))


def test_invalid_schema_fields_fail_closed():
    profile = get_profile("base-mainnet")
    invalid_repository = replace(
        profile.repository,
        migration_dir=None,
        migration_state=PathState.EXISTING,
    )
    with pytest.raises(NetworkProfileError, match="H02_PROFILE_INVALID"):
        validate_registry((replace(profile, repository=invalid_repository),))

    invalid_operations = profile.operations[:-1]
    with pytest.raises(NetworkProfileError, match="H02_PROFILE_INVALID"):
        validate_registry((replace(profile, operations=invalid_operations),))

    invalid_verifier = replace(profile.verifier, provider="unknown")
    with pytest.raises(NetworkProfileError, match="H02_PROFILE_INVALID"):
        validate_registry((replace(profile, verifier=invalid_verifier),))


def test_alias_cannot_change_identity_or_repository():
    alias = ProfileAlias("base", "base-mainnet")
    validate_registry(NETWORK_PROFILES, (alias,))
    assert {field.name for field in fields(ProfileAlias)} == {
        "alias",
        "canonical_profile_id",
    }
    with pytest.raises(FrozenInstanceError):
        alias.canonical_profile_id = "base-sepolia"
    with pytest.raises(NetworkProfileError, match="H02_PROFILE_INVALID"):
        validate_registry(
            NETWORK_PROFILES, (ProfileAlias("bad", "missing-profile"),)
        )


def test_casefolded_base_id_resolves_only_to_base_mainnet():
    profile = get_profile("BASE-MAINNET")
    assert profile.identity.profile_id == "base-mainnet"
    assert profile.identity.chain_id == 8453


def test_profiles_cannot_share_history():
    base = get_profile("base-mainnet")
    sepolia = get_profile("base-sepolia")
    aliased_repository = replace(
        sepolia.repository,
        migration_dir=PurePosixPath("migrations/base-sepolia"),
        migration_state=PathState.EXISTING,
        history_dir=base.repository.history_dir,
        history_state=PathState.EXISTING,
    )
    with pytest.raises(NetworkProfileError, match="H02_HISTORY_ALIAS"):
        validate_registry(
            (base, replace(sepolia, repository=aliased_repository))
        )


def test_robinhood_profiles_share_only_proposed_source():
    mainnet = get_profile("robinhood-mainnet").repository
    testnet = get_profile("robinhood-testnet").repository
    assert mainnet.migration_dir == testnet.migration_dir
    assert mainnet.migration_state is PathState.PROPOSED
    assert testnet.migration_state is PathState.PROPOSED
    assert mainnet.history_dir != testnet.history_dir


def test_missing_repository_does_not_fallback_or_create(tmp_path):
    base = get_profile("base-mainnet")
    identity = verified("base-mainnet", Operation.MIGRATION_FORK)
    with pytest.raises(
        NetworkProfileError, match="H02_REPOSITORY_UNAVAILABLE"
    ):
        repository_paths(
            base,
            Operation.MIGRATION_FORK,
            root=tmp_path,
            identity=identity,
        )
    assert list(tmp_path.iterdir()) == []

    sepolia = get_profile("base-sepolia")
    with pytest.raises(
        NetworkProfileError, match="H02_REPOSITORY_UNAVAILABLE"
    ):
        repository_paths(
            sepolia,
            Operation.CONSOLE_EXPLORATION,
            root=tmp_path,
            identity=verified(
                "base-sepolia", Operation.CONSOLE_EXPLORATION
            ),
        )
    assert list(tmp_path.iterdir()) == []


def test_verified_identity_cannot_select_another_profile_history():
    base = get_profile("base-mainnet")
    wrong_identity = VerifiedNetworkIdentity(
        "base-sepolia",
        Operation.MIGRATION_FORK,
        84532,
        84532,
    )
    with pytest.raises(NetworkProfileError, match="H02_CHAIN_ID_MISMATCH"):
        repository_paths(
            base,
            Operation.MIGRATION_FORK,
            root=Path(__file__).resolve().parents[2],
            identity=wrong_identity,
        )


def test_unsupported_and_blocked_pending_policy_are_distinct():
    sepolia = operation_decision(
        get_profile("base-sepolia"), Operation.MIGRATION_LIVE
    )
    robinhood = operation_decision(
        get_profile("robinhood-mainnet"), Operation.MIGRATION_LIVE
    )
    assert sepolia.outcome is OperationOutcome.UNSUPPORTED
    assert robinhood.outcome is OperationOutcome.BLOCKED_PENDING_POLICY


def test_fork_submission_is_always_false():
    for profile in NETWORK_PROFILES:
        assert profile.fork.allow_submission is False

    base = get_profile("base-mainnet")
    unsafe_fork = ForkPolicy(True, True, True, True, allow_submission=True)
    with pytest.raises(
        NetworkProfileError, match="H02_FORK_SUBMISSION_FORBIDDEN"
    ):
        validate_registry((replace(base, fork=unsafe_fork),))


def test_reproducible_fork_requires_block_pin():
    base = get_profile("base-mainnet")
    with pytest.raises(NetworkProfileError, match="H02_FORK_PIN_REQUIRED"):
        validate_fork_request(
            base,
            Operation.CONSOLE_EVIDENCE,
            evidence_mode=True,
            block_number=None,
            allow_dirty=False,
        )


def test_latest_and_dirty_are_exploration_only():
    base = get_profile("base-mainnet")
    validate_fork_request(
        base,
        Operation.CONSOLE_EXPLORATION,
        evidence_mode=False,
        block_number=None,
        allow_dirty=True,
    )
    with pytest.raises(
        NetworkProfileError, match="H02_DIRTY_EVIDENCE_FORBIDDEN"
    ):
        validate_fork_request(
            base,
            Operation.CONSOLE_EVIDENCE,
            evidence_mode=True,
            block_number=123,
            allow_dirty=True,
        )


def test_chain_id_mismatch_before_account_load():
    profile = get_profile("base-mainnet")
    operation = Operation.MIGRATION_FORK
    rpc = resolve_rpc_reference(
        profile, operation, {}, "https://rpc.invalid.example"
    )
    events = []

    def reader(value):
        events.append("chain_id")
        return 1

    with pytest.raises(NetworkProfileError, match="H02_CHAIN_ID_MISMATCH"):
        verify_chain_identity(profile, operation, rpc, reader)
        events.append("account")
    assert events == ["chain_id"]


def test_matching_chain_id_allows_only_next_mocked_step():
    profile = get_profile("base-mainnet")
    operation = Operation.MIGRATION_FORK
    rpc = resolve_rpc_reference(
        profile, operation, {}, "https://rpc.invalid.example"
    )
    events = []

    def reader(value):
        events.append("chain_id")
        return "0x2105"

    identity = verify_chain_identity(profile, operation, rpc, reader)
    events.append("next_mocked_step")
    assert identity.expected_chain_id == 8453
    assert events == ["chain_id", "next_mocked_step"]


def test_invalid_chain_id_response_fails_with_sanitized_typed_error():
    profile = get_profile("base-mainnet")
    operation = Operation.MIGRATION_FORK
    rpc = resolve_rpc_reference(
        profile, operation, {}, "https://rpc.invalid.example"
    )
    with pytest.raises(NetworkProfileError, match="H02_CHAIN_ID_INVALID"):
        verify_chain_identity(
            profile, operation, rpc, lambda value: "not-a-chain-id"
        )


def test_local_runtime_requires_explicit_chain_id():
    local = get_profile("local")
    with pytest.raises(
        NetworkProfileError, match="H02_LOCAL_CHAIN_ID_REQUIRED"
    ):
        verify_chain_identity(
            local,
            Operation.LOCAL_RUNTIME,
            None,
            lambda value: pytest.fail("reader must not run"),
        )

    identity = verify_chain_identity(
        local,
        Operation.LOCAL_RUNTIME,
        None,
        lambda value: pytest.fail("reader must not run"),
        local_chain_id=31337,
    )
    assert identity.expected_chain_id == 31337


def test_profile_errors_never_render_sensitive_rpc():
    sensitive = (
        "https://synthetic-user:synthetic-password@rpc.invalid.example/"
        "path-token?api_key=query-token#fragment-token"
    )
    profile = get_profile("base-mainnet")
    operation = Operation.MIGRATION_FORK
    rpc = RedactedRpc(sensitive, "base-mainnet", operation, "--rpc")

    def reader(value):
        assert value == sensitive
        raise RuntimeError(sensitive)

    with pytest.raises(NetworkProfileError) as captured:
        verify_chain_identity(profile, operation, rpc, reader)
    rendered = f"{captured.value!s} {captured.value!r} {rpc!s} {rpc!r}"
    for component in (
        sensitive,
        "synthetic-user",
        "synthetic-password",
        "path-token",
        "query-token",
        "fragment-token",
    ):
        assert component not in rendered
