from __future__ import annotations

import copy
import hashlib
import os
from datetime import datetime, timezone

import pytest


@pytest.mark.parametrize(
    ("profile", "chain_id"),
    (
        ("robinhood-mainnet", 4663),
        ("robinhood-testnet", 46630),
    ),
)
def test_robinhood_profile_chain_binding(
    fork_framework, envelope_value, profile, chain_id
):
    candidate = copy.deepcopy(envelope_value)
    candidate["owner_inputs"]["profile"] = profile
    candidate["owner_inputs"]["expected_chain_id"] = chain_id
    data = fork_framework.canonical_json_bytes(candidate)
    parsed = fork_framework.parse_input_envelope(
        data,
        now=datetime(2029, 1, 1, tzinfo=timezone.utc),
    )
    assert parsed.owner.profile == profile
    assert parsed.owner.expected_chain_id == chain_id


def test_base_profile_is_rejected(
    fork_framework, envelope_value, parse_envelope
):
    candidate = copy.deepcopy(envelope_value)
    candidate["owner_inputs"]["profile"] = "base-mainnet"
    candidate["owner_inputs"]["expected_chain_id"] = 8453
    with pytest.raises(
        fork_framework.ForkFrameworkError, match="H09_PROFILE"
    ):
        parse_envelope(candidate)


def test_exact_pin_and_endpoint_observation_bind(
    fork_framework, parse_envelope, observed_facts
):
    bound = fork_framework.bind_observed_facts(
        parse_envelope(), observed_facts
    )
    assert bound.owner.pin.number == observed_facts.block_number
    assert bound.owner.pin.block_hash == observed_facts.block_hash


def test_archive_capability_is_explicit_and_read_only(parse_envelope):
    owner = parse_envelope().owner
    assert owner.read_only is True
    assert {
        "eth_getBlockByHash",
        "eth_getBlockByNumber",
        "eth_getCode",
        "eth_getProof",
        "eth_getStorageAt",
    } <= set(owner.rpc_methods)
    assert all(
        not method.startswith("eth_send") for method in owner.rpc_methods
    )


@pytest.mark.parametrize(
    ("field", "value", "code"),
    (
        ("chain_id", 1, "H09_CHAIN_ID_MISMATCH"),
        ("block_number", 124, "H09_BLOCK_NUMBER_MISMATCH"),
        ("block_hash", "0x" + "91" * 32, "H09_BLOCK_HASH_MISMATCH"),
        ("parent_hash", "0x" + "92" * 32, "H09_PARENT_HASH_MISMATCH"),
        ("state_root", "0x" + "93" * 32, "H09_STATE_ROOT_MISMATCH"),
        ("timestamp", 1_800_000_001, "H09_TIMESTAMP_MISMATCH"),
        (
            "endpoint_fingerprint_sha256",
            "94" * 32,
            "H09_ENDPOINT_FINGERPRINT_MISMATCH",
        ),
    ),
)
def test_every_observed_pin_mismatch_fails_closed(
    fork_framework,
    parse_envelope,
    mutate_observation,
    field,
    value,
    code,
):
    with pytest.raises(fork_framework.ForkFrameworkError, match=code):
        fork_framework.bind_observed_facts(
            parse_envelope(), mutate_observation(**{field: value})
        )


def test_partial_pin_is_rejected(
    fork_framework, envelope_value, parse_envelope
):
    candidate = copy.deepcopy(envelope_value)
    del candidate["owner_inputs"]["pin"]["state_root"]
    with pytest.raises(
        fork_framework.ForkFrameworkError, match="H09_PIN_KEYS"
    ):
        parse_envelope(candidate)


def test_contradictory_parent_and_block_hash_are_rejected(
    fork_framework, envelope_value, parse_envelope
):
    candidate = copy.deepcopy(envelope_value)
    candidate["owner_inputs"]["pin"]["parent_hash"] = candidate[
        "owner_inputs"
    ]["pin"]["block_hash"]
    with pytest.raises(
        fork_framework.ForkFrameworkError, match="H09_PIN_CONTRADICTION"
    ):
        parse_envelope(candidate)


def test_absent_accepted_inputs_produce_deterministic_blocked_receipt(
    fork_framework,
):
    first = fork_framework.qualification_preflight_receipt({})
    second = fork_framework.qualification_preflight_receipt({})
    assert first == second
    assert first["status"] == "blocked"
    assert frozenset(first) == fork_framework.RECEIPT_KEYS
    assert first["error_codes"] == [
        "H09_OPT_IN_REQUIRED",
        "H09_ACCEPTED_INPUTS_MISSING",
    ]
    assert first["missing_inputs"] == [
        "OWNER_RH_ARCHIVE_*:envelope-named-read-only-archive-endpoint",
        "RIPE_RH_FORK_IDENTITY_MANIFEST:"
        "complete-accepted-owner-identities",
        "RIPE_RH_FORK_MANIFEST:complete-accepted-h09-envelope",
    ]
    assert first["invalid_inputs"] == []


def test_complete_synthetic_inputs_produce_qualifying_receipt(
    fork_framework, accepted_preflight_inputs
):
    receipt = fork_framework.qualification_preflight_receipt(
        accepted_preflight_inputs.environment,
        repository_observation=accepted_preflight_inputs.observation,
    )
    assert frozenset(receipt) == fork_framework.RECEIPT_KEYS
    assert receipt["status"] == "qualifying"
    assert receipt["error_codes"] == []
    assert receipt["missing_inputs"] == []
    assert receipt["invalid_inputs"] == []
    assert receipt["endpoint_alias"] == "OWNER_RH_ARCHIVE_TEST"
    assert len(receipt["envelope_sha256"]) == 64
    assert len(receipt["identity_manifest_sha256"]) == 64


def test_complete_inputs_without_sequencer_authority_are_blocked(
    fork_framework, accepted_preflight_inputs, tmp_path
):
    candidate = copy.deepcopy(accepted_preflight_inputs.identity_value)
    candidate["identities"] = [
        row
        for row in candidate["identities"]
        if row["kind"] != "sequencer-uptime-feed"
    ]
    identity_data = fork_framework.canonical_json_bytes(candidate)
    identity_path = tmp_path / "sequencer-free-identities.json"
    identity_path.write_bytes(identity_data)
    envelope = copy.deepcopy(accepted_preflight_inputs.envelope_value)
    envelope["owner_inputs"]["identity_manifest_sha256"] = hashlib.sha256(
        identity_data
    ).hexdigest()
    envelope_path = tmp_path / "sequencer-free-envelope.json"
    envelope_path.write_bytes(fork_framework.canonical_json_bytes(envelope))
    environment = dict(accepted_preflight_inputs.environment)
    environment[fork_framework.IDENTITY_MANIFEST_ENV] = str(identity_path)
    environment[fork_framework.MANIFEST_ENV] = str(envelope_path)
    observation = dict(accepted_preflight_inputs.observation)
    receipt = fork_framework.qualification_preflight_receipt(
        environment, repository_observation=observation
    )
    assert receipt["status"] == "blocked"
    assert receipt["error_codes"] == ["H09_SEQUENCER_AUTHORITY_MISSING"]
    assert receipt["missing_inputs"] == [
        "sequencer_uptime_feed:accepted-owner-authority"
    ]


def test_malformed_envelope_and_repository_drift_have_coded_receipts(
    fork_framework, accepted_preflight_inputs, tmp_path
):
    malformed_path = tmp_path / "malformed-envelope.json"
    malformed_path.write_bytes(b"{broken")
    environment = dict(accepted_preflight_inputs.environment)
    environment[fork_framework.MANIFEST_ENV] = str(malformed_path)
    malformed = fork_framework.qualification_preflight_receipt(
        environment,
        repository_observation=accepted_preflight_inputs.observation,
    )
    assert malformed["error_codes"] == ["H09_ENVELOPE_MALFORMED"]
    assert malformed["invalid_inputs"] == [
        "preflight:H09_ENVELOPE_MALFORMED"
    ]

    dirty = dict(accepted_preflight_inputs.observation)
    dirty["staged_paths"] = ("synthetic-staged.txt",)
    drift = fork_framework.qualification_preflight_receipt(
        accepted_preflight_inputs.environment,
        repository_observation=dirty,
    )
    assert drift["error_codes"] == ["H09_REPOSITORY_NOT_CLEAN"]
    assert drift["invalid_inputs"] == [
        "preflight:H09_REPOSITORY_NOT_CLEAN"
    ]


def test_repository_observation_failure_has_blocked_receipt(
    fork_framework, accepted_preflight_inputs, monkeypatch
):
    def fail_observation():
        raise fork_framework.ForkFrameworkError(
            "H09_REPOSITORY_OBSERVATION_FAILED"
        )

    monkeypatch.setitem(
        fork_framework.qualification_preflight_receipt.__globals__,
        "observe_repository_authority",
        fail_observation,
    )
    receipt = fork_framework.qualification_preflight_receipt(
        accepted_preflight_inputs.environment
    )
    assert receipt["status"] == "blocked"
    assert receipt["error_codes"] == [
        "H09_REPOSITORY_OBSERVATION_FAILED"
    ]


@pytest.mark.rh_archive_fork
def test_robinhood_archive_qualification_preflight(fork_framework):
    receipt = fork_framework.qualification_preflight_receipt(
        os.environ
    )
    if receipt["status"] != "qualifying":
        pytest.fail(
            fork_framework.canonical_json_bytes(receipt).decode("utf-8")
        )
