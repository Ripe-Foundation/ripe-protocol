from __future__ import annotations

import pytest


def test_synthetic_token_metadata_uses_accepted_token_identity(
    fork_framework, accepted_preflight
):
    token = next(
        identity
        for identity in accepted_preflight.identity_manifest.identities
        if identity.kind == "token"
    )
    fields = ("decimals", "name", "symbol")
    owner = {
        "decimals": 7,
        "name": f"Synthetic owner fixture {token.identity_id}",
        "symbol": "SYN",
    }
    observed = dict(owner)
    assert (
        fork_framework.consume_owner_output(
            owner,
            observed,
            required_fields=fields,
            code="H09_TOKEN_METADATA",
        )
        == observed
    )


def test_synthetic_omitted_or_different_metadata_fails_closed(
    fork_framework, accepted_preflight
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h08_assertions",)
    )
    fields = ("decimals", "name", "symbol")
    owner = {"decimals": 7, "name": "Synthetic owner fixture", "symbol": "SYN"}
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_TOKEN_METADATA_OBSERVED_FIELDS",
    ):
        fork_framework.consume_owner_output(
            owner,
            {"decimals": 7, "symbol": "SYN"},
            required_fields=fields,
            code="H09_TOKEN_METADATA",
        )
    with pytest.raises(
        fork_framework.ForkFrameworkError, match="H09_TOKEN_METADATA_MISMATCH"
    ):
        fork_framework.consume_owner_output(
            owner,
            {**owner, "decimals": 18},
            required_fields=fields,
            code="H09_TOKEN_METADATA",
        )


@pytest.mark.parametrize(
    ("value", "empty_allowed"),
    ((True, False), (True, True), (b"", True)),
)
def test_accepted_token_return_shapes_are_explicit(
    fork_framework, value, empty_allowed
):
    fork_framework.validate_token_return(
        value, empty_allowed=empty_allowed
    )


@pytest.mark.parametrize("value", (False, None, 1, b"\x00"))
def test_false_ambiguous_or_malformed_token_returns_fail(
    fork_framework, value
):
    with pytest.raises(
        fork_framework.ForkFrameworkError, match="H09_TOKEN_RETURN"
    ):
        fork_framework.validate_token_return(value, empty_allowed=False)
