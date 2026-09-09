from __future__ import annotations

import pytest


def test_chainlink_feed_identity_consumes_accepted_owner_manifest(
    fork_framework, accepted_preflight
):
    feed = fork_framework.require_owner_identity_kind(
        accepted_preflight.identity_manifest, "sequencer-uptime-feed"
    )
    owner = {
        "address": feed.address,
        "authority": feed.authority,
        "runtime_code_sha256": feed.runtime_code_sha256,
    }
    observed = dict(owner)
    assert fork_framework.consume_owner_output(
        owner,
        observed,
        required_fields=tuple(sorted(owner)),
        code="H09_CHAINLINK_IDENTITY",
    ) == owner


@pytest.mark.parametrize(
    ("field", "value", "code"),
    (
        ("answer", 0, "H09_CHAINLINK_VALUE"),
        ("answer", -1, "H09_CHAINLINK_VALUE"),
        ("round_id", 0, "H09_CHAINLINK_VALUE"),
        ("updated_at", 0, "H09_CHAINLINK_VALUE"),
        ("stale_after", 0, "H09_CHAINLINK_VALUE"),
        ("decimals", 37, "H09_CHAINLINK_DECIMALS"),
    ),
)
def test_synthetic_chainlink_boundary_values_fail_closed(
    fork_framework, field, value, code
):
    observation = {
        "answer": 123_456_789,
        "decimals": 8,
        "observed_at": 1_800_000_100,
        "round_id": 9,
        "stale_after": 300,
        "updated_at": 1_800_000_000,
    }
    observation[field] = value
    with pytest.raises(fork_framework.ForkFrameworkError, match=code):
        fork_framework.validate_chainlink_observation(**observation)


def test_synthetic_chainlink_freshness_boundary_is_enforced(fork_framework):
    observation = {
        "answer": 123_456_789,
        "decimals": 8,
        "observed_at": 1_800_000_301,
        "round_id": 9,
        "stale_after": 300,
        "updated_at": 1_800_000_000,
    }
    with pytest.raises(
        fork_framework.ForkFrameworkError, match="H09_CHAINLINK_STALE"
    ):
        fork_framework.validate_chainlink_observation(**observation)


def test_feed_graph_mismatch_cannot_be_promoted(
    fork_framework, accepted_preflight
):
    feed = fork_framework.require_owner_identity_kind(
        accepted_preflight.identity_manifest, "sequencer-uptime-feed"
    )
    fields = ("address", "runtime_code_sha256")
    owner = {
        "address": feed.address,
        "runtime_code_sha256": feed.runtime_code_sha256,
    }
    with pytest.raises(
        fork_framework.ForkFrameworkError, match="H09_CHAINLINK_MISMATCH"
    ):
        fork_framework.consume_owner_output(
            owner,
            {**owner, "runtime_code_sha256": "ab" * 32},
            required_fields=fields,
            code="H09_CHAINLINK",
        )
