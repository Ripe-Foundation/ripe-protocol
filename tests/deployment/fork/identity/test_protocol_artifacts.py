from __future__ import annotations

import copy
from datetime import datetime, timezone

import pytest


def test_identity_manifest_digest_profile_and_chain_bind(
    fork_framework,
    envelope_value,
    parse_identity,
):
    manifest = parse_identity()
    candidate = copy.deepcopy(envelope_value)
    candidate["owner_inputs"]["identity_manifest_sha256"] = manifest.sha256
    envelope = fork_framework.parse_input_envelope(
        fork_framework.canonical_json_bytes(candidate),
        now=datetime(2029, 1, 1, tzinfo=timezone.utc),
    )
    fork_framework.bind_identity_manifest(envelope, manifest)


def test_accepted_preflight_binds_required_sequencer_artifact(
    fork_framework, accepted_preflight
):
    feed = fork_framework.require_owner_identity_kind(
        accepted_preflight.identity_manifest, "sequencer-uptime-feed"
    )
    assert feed.authority == "owner-supplied"


def test_identity_manifest_digest_mismatch_fails_closed(
    fork_framework, parse_envelope, parse_identity
):
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_IDENTITY_MANIFEST_DIGEST_MISMATCH",
    ):
        fork_framework.bind_identity_manifest(
            parse_envelope(), parse_identity()
        )


def test_identity_manifest_profile_mismatch_fails_closed(
    fork_framework, envelope_value, parse_identity
):
    manifest = parse_identity()
    candidate = copy.deepcopy(envelope_value)
    candidate["owner_inputs"]["profile"] = "robinhood-mainnet"
    candidate["owner_inputs"]["expected_chain_id"] = 4663
    candidate["owner_inputs"]["identity_manifest_sha256"] = manifest.sha256
    envelope = fork_framework.parse_input_envelope(
        fork_framework.canonical_json_bytes(candidate),
        now=datetime(2029, 1, 1, tzinfo=timezone.utc),
    )
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_IDENTITY_MANIFEST_PROFILE_MISMATCH",
    ):
        fork_framework.bind_identity_manifest(envelope, manifest)
