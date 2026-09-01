from __future__ import annotations

import pytest


def test_synthetic_permit_controls_use_accepted_token_identity(
    fork_framework, accepted_preflight
):
    token = next(
        identity
        for identity in accepted_preflight.identity_manifest.identities
        if identity.kind == "token"
    )
    fields = (
        "blocklist_enforced",
        "domain_separator",
        "nonce_after",
        "nonce_before",
        "paused",
        "permit_supported",
    )
    owner = {
        "blocklist_enforced": True,
        "domain_separator": token.provenance_sha256,
        "nonce_after": 8,
        "nonce_before": 7,
        "paused": False,
        "permit_supported": True,
    }
    consumed = fork_framework.consume_owner_output(
        owner,
        dict(owner),
        required_fields=fields,
        code="H09_TOKEN_CONTROLS",
    )
    assert consumed["nonce_after"] == consumed["nonce_before"] + 1


def test_permit_support_is_never_inferred_from_missing_owner_output(
    fork_framework, accepted_preflight
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h08_assertions",)
    )
    fields = ("nonce_after", "nonce_before", "permit_supported")
    owner = {
        "nonce_after": 1,
        "nonce_before": 0,
        "permit_supported": None,
    }
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_TOKEN_CONTROLS_OWNER_VALUE_MISSING",
    ):
        fork_framework.consume_owner_output(
            owner,
            owner,
            required_fields=fields,
            code="H09_TOKEN_CONTROLS",
        )


def test_pause_and_blocklist_results_must_match_owner_authority(
    fork_framework, accepted_preflight
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h08_assertions",)
    )
    fields = ("blocklisted_transfer_reverted", "paused_transfer_reverted")
    owner = {
        "blocklisted_transfer_reverted": True,
        "paused_transfer_reverted": True,
    }
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_TOKEN_CONTROLS_MISMATCH",
    ):
        fork_framework.consume_owner_output(
            owner,
            {**owner, "paused_transfer_reverted": False},
            required_fields=fields,
            code="H09_TOKEN_CONTROLS",
        )
