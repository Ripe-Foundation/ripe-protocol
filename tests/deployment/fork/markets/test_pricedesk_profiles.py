from __future__ import annotations

from config.robinhood_blueprint import (
    ROBINHOOD_BLUEPRINT,
    Disposition,
    RegistryDomain,
)


def _price_desk_rows():
    return {
        row.registry_id: row
        for component in ROBINHOOD_BLUEPRINT.components
        for row in component.registry_expectations
        if row.domain is RegistryDomain.PRICE_DESK
    }


def test_profile_one_pricedesk_topology_uses_real_robinhood_blueprint(
    fork_framework, accepted_preflight
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h08_assertions",)
    )
    rows = _price_desk_rows()
    assert rows[1].semantic_name == "Chainlink"
    assert rows[1].disposition is Disposition.REQUIRED
    assert all(
        rows[index].disposition is Disposition.OMITTED
        for index in range(2, 6)
    )


def test_profile_two_is_not_inferred_from_profile_one_authority(
    fork_framework, accepted_preflight
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h07_artifacts", "h08_assertions")
    )
    accepted_kinds = {
        identity.kind
        for identity in accepted_preflight.identity_manifest.identities
    }
    assert "curve-pool" not in accepted_kinds
    assert "curve-blueprint" not in accepted_kinds


def test_base_deleverage_values_are_absent_from_robinhood_inputs(
    fork_framework, accepted_preflight
):
    parameters = (
        fork_framework.REPOSITORY_ROOT / "config/robinhood-parameters.json"
    ).read_bytes()
    envelope = accepted_preflight.envelope.canonical_bytes
    for forbidden_key in (
        b'"fullPayoffBuffer"',
        b'"overageBps"',
        b'"dustThreshold"',
        b'"dustBps"',
    ):
        assert forbidden_key not in parameters
        assert forbidden_key not in envelope


def test_pricedesk_synthetic_observation_consumes_accepted_h08_binding(
    fork_framework, accepted_preflight
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h08_assertions",)
    )
    fields = ("profile", "source_1_role", "source_2_role")
    owner = {
        "profile": "synthetic-profile-1",
        "source_1_role": "synthetic-chainlink-authority",
        "source_2_role": "synthetic-empty",
    }
    assert fork_framework.consume_owner_output(
        owner,
        dict(owner),
        required_fields=fields,
        code="H09_PRICEDESK",
    ) == owner
