from __future__ import annotations

import copy
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import pytest


def test_default_mode_is_network_disabled(fork_framework):
    assert fork_framework.qualification_mode({}) == "disabled"
    assert (
        fork_framework.qualification_mode(
            {"RIPE_RH_FORK_MODE": "disabled"}
        )
        == "disabled"
    )


def test_opt_in_is_exact_and_invalid_values_fail_closed(fork_framework):
    assert (
        fork_framework.qualification_mode(
            {"RIPE_RH_FORK_MODE": "read-only-archive-fork"}
        )
        == "read-only-archive-fork"
    )
    with pytest.raises(
        fork_framework.ForkFrameworkError, match="H09_MODE_INVALID"
    ):
        fork_framework.qualification_mode(
            {"RIPE_RH_FORK_MODE": "yes-please"}
        )


def test_complete_canonical_envelope_parses(parse_envelope):
    envelope = parse_envelope()
    assert envelope.owner.profile == "robinhood-testnet"
    assert envelope.owner.expected_chain_id == 46630
    assert envelope.owner.read_only is True
    assert len(envelope.sha256) == 64


def test_noncanonical_or_malformed_envelope_is_rejected(
    fork_framework, envelope_value
):
    canonical = fork_framework.canonical_json_bytes(envelope_value)
    noncanonical = canonical.replace(b'":', b'": ', 1)
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_ENVELOPE_NONCANONICAL",
    ):
        fork_framework.parse_input_envelope(noncanonical)
    with pytest.raises(
        fork_framework.ForkFrameworkError, match="H09_ENVELOPE_MALFORMED"
    ):
        fork_framework.parse_input_envelope(b"{broken")


@pytest.mark.parametrize(
    ("path", "value", "code"),
    (
        (("owner_inputs", "read_only"), False, "H09_READ_ONLY"),
        (
            ("owner_inputs", "affirmative_opt_in"),
            "archive",
            "H09_OPT_IN",
        ),
        (
            ("requested_capabilities", "real_signer"),
            True,
            "H09_FORBIDDEN_CAPABILITY",
        ),
        (
            ("requested_capabilities", "broadcast"),
            True,
            "H09_FORBIDDEN_CAPABILITY",
        ),
        (
            ("requested_capabilities", "live_mutation"),
            True,
            "H09_FORBIDDEN_CAPABILITY",
        ),
        (
            ("repository_authority", "suite_path_ceiling"),
            34,
            "H09_PATH_CEILING",
        ),
    ),
)
def test_forbidden_or_contradictory_inputs_fail_closed(
    parse_envelope, envelope_value, path, value, code
):
    candidate = copy.deepcopy(envelope_value)
    candidate[path[0]][path[1]] = value
    with pytest.raises(Exception, match=code):
        parse_envelope(candidate)


def test_partial_envelope_is_rejected(
    parse_envelope, envelope_value, fork_framework
):
    candidate = copy.deepcopy(envelope_value)
    del candidate["owner_inputs"]["endpoint"]
    with pytest.raises(
        fork_framework.ForkFrameworkError, match="H09_OWNER_KEYS"
    ):
        parse_envelope(candidate)


def test_stale_envelope_is_rejected(
    parse_envelope, envelope_value, fork_framework
):
    candidate = copy.deepcopy(envelope_value)
    candidate["owner_inputs"]["valid_until"] = "2029-01-01T00:00:00Z"
    with pytest.raises(
        fork_framework.ForkFrameworkError, match="H09_INPUT_STALE"
    ):
        parse_envelope(
            candidate,
            now=datetime(2029, 1, 1, tzinfo=timezone.utc),
        )


def test_profile_chain_contradiction_is_rejected(
    parse_envelope, envelope_value, fork_framework
):
    candidate = copy.deepcopy(envelope_value)
    candidate["owner_inputs"]["expected_chain_id"] = 4663
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_PROFILE_CHAIN_CONTRADICTION",
    ):
        parse_envelope(candidate)


def test_repository_observed_facts_are_separate_and_clean(
    fork_framework, parse_envelope
):
    authority = parse_envelope().repository
    fork_framework.validate_repository_authority(
        authority,
        observed_commit=authority.commit,
        observed_tree=authority.tree,
        changed_paths=(),
        staged_paths=(),
        ignored_paths=(),
    )
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_REPOSITORY_NOT_CLEAN",
    ):
        fork_framework.validate_repository_authority(
            authority,
            observed_commit=authority.commit,
            observed_tree=authority.tree,
            changed_paths=("unapproved",),
            staged_paths=(),
            ignored_paths=(),
        )


@pytest.mark.parametrize(
    ("owner_value", "observed_value"),
    (
        (True, 1),
        (False, 0),
        (7, 7.0),
        ({"nested": [True]}, {"nested": [1]}),
    ),
)
def test_owner_output_comparison_is_recursively_type_strict(
    fork_framework, owner_value, observed_value
):
    with pytest.raises(
        fork_framework.ForkFrameworkError, match="H09_STRICT_MISMATCH"
    ):
        fork_framework.consume_owner_output(
            {"value": owner_value},
            {"value": observed_value},
            required_fields=("value",),
            code="H09_STRICT",
        )


@pytest.mark.parametrize(
    ("required_fields", "owner", "observed", "code"),
    (
        ((), {}, {}, "H09_OWNER_REQUIREMENTS"),
        (
            ("b", "a"),
            {"a": 1, "b": 2},
            {"a": 1, "b": 2},
            "H09_OWNER_REQUIREMENTS",
        ),
        (("a",), {"a": 1, "extra": 2}, {"a": 1}, "H09_OWNER_OWNER_FIELDS"),
        (("a",), {"a": 1}, {"a": 1, "extra": 2}, "H09_OWNER_OBSERVED_FIELDS"),
    ),
)
def test_owner_output_requirements_and_fields_fail_closed(
    fork_framework, required_fields, owner, observed, code
):
    with pytest.raises(fork_framework.ForkFrameworkError, match=code):
        fork_framework.consume_owner_output(
            owner,
            observed,
            required_fields=required_fields,
            code="H09_OWNER",
        )


def test_owner_binding_requirements_and_missing_name_fail_closed(
    fork_framework, parse_envelope
):
    envelope = parse_envelope()
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_OWNER_BINDING_REQUIREMENTS",
    ):
        fork_framework.require_owner_bindings(envelope, ())
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_OWNER_BINDING_MISSING",
    ):
        fork_framework.require_owner_bindings(
            envelope, ("synthetic-missing-binding",)
        )


def test_forbidden_environment_and_alias_drift_fail_closed(fork_framework):
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_FORBIDDEN_ENVIRONMENT",
    ):
        fork_framework.validate_environment({"PRIVATE_KEY": "do-not-log"})
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_ENDPOINT_ALIAS_DRIFT",
    ):
        fork_framework.validate_environment(
            {
                "OWNER_RH_ARCHIVE_EXPECTED": "https://one.invalid",
                "OWNER_RH_ARCHIVE_EXTRA": "https://two.invalid",
            },
            endpoint_alias="OWNER_RH_ARCHIVE_EXPECTED",
        )


def _identity_value(digest):
    return {
        "artifact_kind": "rh_canonical_identity_manifest",
        "chain_id": 46630,
        "identities": [
            {
                "address": "0x1111111111111111111111111111111111111111",
                "authority": "owner-supplied",
                "identity_id": "synthetic-sequencer-feed",
                "implementation_address": None,
                "kind": "sequencer-uptime-feed",
                "provenance_sha256": digest,
                "proxy_address": None,
                "runtime_code_sha256": digest,
            }
        ],
        "owner_approval_sha256": digest,
        "profile": "robinhood-testnet",
        "schema_version": "owner-rh-canonical-identities-v1",
    }


def test_explicit_preflight_binds_all_local_inputs_before_endpoint_use(
    fork_framework, envelope_value, digest, tmp_path: Path
):
    raw_endpoint = "https://user:secret@archive.invalid/private?key=hidden"
    identity_data = fork_framework.canonical_json_bytes(
        _identity_value(digest)
    )
    identity_path = tmp_path / "identity.json"
    identity_path.write_bytes(identity_data)
    candidate = copy.deepcopy(envelope_value)
    candidate["owner_inputs"]["identity_manifest_sha256"] = hashlib.sha256(
        identity_data
    ).hexdigest()
    candidate["owner_inputs"]["endpoint"]["fingerprint_sha256"] = (
        fork_framework.endpoint_fingerprint(raw_endpoint)
    )
    envelope_path = tmp_path / "envelope.json"
    envelope_path.write_bytes(
        fork_framework.canonical_json_bytes(candidate)
    )
    environment = {
        "RIPE_RH_FORK_MODE": "read-only-archive-fork",
        "RIPE_RH_FORK_MANIFEST": str(envelope_path),
        "RIPE_RH_FORK_IDENTITY_MANIFEST": str(identity_path),
        "OWNER_RH_ARCHIVE_TEST": raw_endpoint,
    }
    result = fork_framework.preflight_from_environment(
        environment,
        observed_commit=candidate["repository_authority"]["commit"],
        observed_tree=candidate["repository_authority"]["tree"],
        now=datetime(2029, 1, 1, tzinfo=timezone.utc),
    )
    assert result.identity_manifest.sha256 == (
        candidate["owner_inputs"]["identity_manifest_sha256"]
    )
    assert raw_endpoint not in repr(result.endpoint)


def test_preflight_rejects_repository_drift_before_parsing_endpoint(
    fork_framework, envelope_value, digest, tmp_path: Path
):
    identity_data = fork_framework.canonical_json_bytes(
        _identity_value(digest)
    )
    identity_path = tmp_path / "identity.json"
    identity_path.write_bytes(identity_data)
    candidate = copy.deepcopy(envelope_value)
    candidate["owner_inputs"]["identity_manifest_sha256"] = hashlib.sha256(
        identity_data
    ).hexdigest()
    envelope_path = tmp_path / "envelope.json"
    envelope_path.write_bytes(
        fork_framework.canonical_json_bytes(candidate)
    )
    environment = {
        "RIPE_RH_FORK_MODE": "read-only-archive-fork",
        "RIPE_RH_FORK_MANIFEST": str(envelope_path),
        "RIPE_RH_FORK_IDENTITY_MANIFEST": str(identity_path),
        "OWNER_RH_ARCHIVE_TEST": "not-an-endpoint",
    }
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_REPOSITORY_NOT_CLEAN",
    ):
        fork_framework.preflight_from_environment(
            environment,
            observed_commit=candidate["repository_authority"]["commit"],
            observed_tree=candidate["repository_authority"]["tree"],
            changed_paths=("candidate-change",),
            now=datetime(2029, 1, 1, tzinfo=timezone.utc),
        )


def test_opt_in_preflight_with_complete_local_files_requires_endpoint(
    fork_framework, envelope_value, digest, tmp_path: Path
):
    identity_data = fork_framework.canonical_json_bytes(
        _identity_value(digest)
    )
    identity_path = tmp_path / "identity.json"
    identity_path.write_bytes(identity_data)
    candidate = copy.deepcopy(envelope_value)
    candidate["owner_inputs"]["identity_manifest_sha256"] = hashlib.sha256(
        identity_data
    ).hexdigest()
    envelope_path = tmp_path / "envelope.json"
    envelope_path.write_bytes(
        fork_framework.canonical_json_bytes(candidate)
    )
    environment = {
        "RIPE_RH_FORK_MODE": "read-only-archive-fork",
        "RIPE_RH_FORK_MANIFEST": str(envelope_path),
        "RIPE_RH_FORK_IDENTITY_MANIFEST": str(identity_path),
    }
    with pytest.raises(
        fork_framework.ForkFrameworkError, match="H09_ENDPOINT_MISSING"
    ):
        fork_framework.preflight_from_environment(
            environment,
            observed_commit=candidate["repository_authority"]["commit"],
            observed_tree=candidate["repository_authority"]["tree"],
            now=datetime(2029, 1, 1, tzinfo=timezone.utc),
        )
