from __future__ import annotations

import copy

import pytest


def test_evidence_serialization_and_hash_are_deterministic(
    fork_framework, evidence_value
):
    reordered = dict(reversed(tuple(evidence_value.items())))
    assert fork_framework.deterministic_evidence_bytes(evidence_value) == (
        fork_framework.deterministic_evidence_bytes(reordered)
    )
    assert fork_framework.deterministic_evidence_hash(evidence_value) == (
        fork_framework.deterministic_evidence_hash(reordered)
    )


@pytest.mark.parametrize(
    ("key", "value"),
    (
        ("rpc_url", "https://archive.invalid"),
        ("private_key", "do-not-log"),
        ("credential", "do-not-log"),
        ("safe_field", "https://archive.invalid/private?token=secret"),
        ("safe_field", "sk-do-not-log"),
    ),
)
def test_credentials_never_enter_evidence(
    fork_framework, evidence_value, key, value
):
    candidate = copy.deepcopy(evidence_value)
    candidate[key] = value
    with pytest.raises(
        fork_framework.ForkFrameworkError, match="H09_EVIDENCE_SECRET"
    ):
        fork_framework.deterministic_evidence_bytes(candidate)


def test_replay_identity_is_stable_and_input_bound(
    fork_framework, evidence_value
):
    envelope = "12" * 32
    identities = "34" * 32
    nodes = fork_framework.ordered_node_digest(("a", "b"))
    first = fork_framework.replay_identity(
        envelope_sha256=envelope,
        identity_manifest_sha256=identities,
        ordered_node_sha256=nodes,
    )
    second = fork_framework.replay_identity(
        envelope_sha256=envelope,
        identity_manifest_sha256=identities,
        ordered_node_sha256=nodes,
    )
    changed = fork_framework.replay_identity(
        envelope_sha256="56" * 32,
        identity_manifest_sha256=identities,
        ordered_node_sha256=nodes,
    )
    assert first == second
    assert first != changed


def test_rollback_vocabulary_excludes_compensating_actions(
    fork_framework,
):
    for action in ("transfer", "admin_call", "reverse_migration"):
        with pytest.raises(
            fork_framework.ForkFrameworkError,
            match="H09_LOCAL_ACTION_FORBIDDEN",
        ):
            fork_framework.validate_local_fork_action(
                action,
                disposable_runtime_active=True,
                targets_local_fork=True,
            )
