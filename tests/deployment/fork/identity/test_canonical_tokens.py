from __future__ import annotations

import copy

import pytest


def test_owner_identity_manifest_parses_without_observed_facts(
    parse_identity,
):
    manifest = parse_identity()
    assert manifest.profile == "robinhood-testnet"
    assert manifest.chain_id == 46630
    assert manifest.identities[0].authority == "owner-supplied"


def test_accepted_preflight_exposes_owner_token_identity(
    accepted_preflight,
):
    tokens = tuple(
        identity
        for identity in accepted_preflight.identity_manifest.identities
        if identity.kind == "token"
    )
    assert len(tokens) == 1
    assert tokens[0].authority == "owner-supplied"


@pytest.mark.parametrize(
    ("field", "value", "code"),
    (
        (
            "authority",
            "observed",
            "H09_IDENTITY_AUTHORITY",
        ),
        (
            "address",
            "0x0000000000000000000000000000000000000000",
            "H09_IDENTITY_ADDRESS",
        ),
        (
            "runtime_code_sha256",
            "0" * 64,
            "H09_IDENTITY_RUNTIME",
        ),
        (
            "provenance_sha256",
            "candidate",
            "H09_IDENTITY_PROVENANCE",
        ),
    ),
)
def test_placeholder_or_non_owner_identity_values_are_rejected(
    fork_framework,
    identity_manifest_value,
    parse_identity,
    field,
    value,
    code,
):
    candidate = copy.deepcopy(identity_manifest_value)
    candidate["identities"][0][field] = value
    with pytest.raises(fork_framework.ForkFrameworkError, match=code):
        parse_identity(candidate)


def test_duplicate_or_unsorted_identity_ids_are_rejected(
    fork_framework, identity_manifest_value, parse_identity
):
    candidate = copy.deepcopy(identity_manifest_value)
    second = copy.deepcopy(candidate["identities"][0])
    second["identity_id"] = "another-synthetic-fixture"
    second["address"] = "0x2222222222222222222222222222222222222222"
    candidate["identities"].append(second)
    with pytest.raises(
        fork_framework.ForkFrameworkError, match="H09_IDENTITY_ORDER"
    ):
        parse_identity(candidate)

    candidate["identities"][1]["identity_id"] = candidate["identities"][0][
        "identity_id"
    ]
    with pytest.raises(
        fork_framework.ForkFrameworkError, match="H09_IDENTITY_DUPLICATE"
    ):
        parse_identity(candidate)


def test_profile_chain_contradiction_is_rejected(
    fork_framework, identity_manifest_value, parse_identity
):
    candidate = copy.deepcopy(identity_manifest_value)
    candidate["chain_id"] = 4663
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_IDENTITY_CHAIN_CONTRADICTION",
    ):
        parse_identity(candidate)
