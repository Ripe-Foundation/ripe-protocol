from __future__ import annotations

import copy
import hashlib

import pytest


def test_accepted_sequencer_feed_is_read_from_identity_manifest(
    fork_framework, accepted_preflight
):
    feed = fork_framework.require_owner_identity_kind(
        accepted_preflight.identity_manifest, "sequencer-uptime-feed"
    )
    assert feed.authority == "owner-supplied"
    assert feed.identity_id == "synthetic-sequencer-feed"


@pytest.mark.rh_classification("blocked")
def test_missing_accepted_sequencer_feed_receipt_is_machine_readable(
    fork_framework, accepted_preflight_inputs, tmp_path
):
    identity_value = copy.deepcopy(accepted_preflight_inputs.identity_value)
    identity_value["identities"] = [
        row
        for row in identity_value["identities"]
        if row["kind"] != "sequencer-uptime-feed"
    ]
    identity_data = fork_framework.canonical_json_bytes(identity_value)
    identity_path = tmp_path / "missing-sequencer.json"
    identity_path.write_bytes(identity_data)
    envelope_value = copy.deepcopy(
        accepted_preflight_inputs.envelope_value
    )
    envelope_value["owner_inputs"]["identity_manifest_sha256"] = (
        hashlib.sha256(identity_data).hexdigest()
    )
    envelope_path = tmp_path / "missing-sequencer-envelope.json"
    envelope_path.write_bytes(
        fork_framework.canonical_json_bytes(envelope_value)
    )
    environment = dict(accepted_preflight_inputs.environment)
    environment[fork_framework.IDENTITY_MANIFEST_ENV] = str(identity_path)
    environment[fork_framework.MANIFEST_ENV] = str(envelope_path)
    receipt = fork_framework.qualification_preflight_receipt(
        environment,
        repository_observation=accepted_preflight_inputs.observation,
    )
    assert receipt["status"] == "blocked"
    assert receipt["error_codes"] == ["H09_SEQUENCER_AUTHORITY_MISSING"]
    assert receipt["missing_inputs"] == [
        "sequencer_uptime_feed:accepted-owner-authority"
    ]


def test_candidate_identity_cannot_replace_feed_authority(
    fork_framework, accepted_preflight
):
    feed = fork_framework.require_owner_identity_kind(
        accepted_preflight.identity_manifest, "sequencer-uptime-feed"
    )
    owner = {"address": feed.address, "authority": feed.authority}
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_SEQUENCER_MISMATCH",
    ):
        fork_framework.consume_owner_output(
            owner,
            {**owner, "address": "0x3333333333333333333333333333333333333333"},
            required_fields=tuple(sorted(owner)),
            code="H09_SEQUENCER",
        )
