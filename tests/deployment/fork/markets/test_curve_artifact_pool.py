from __future__ import annotations

import pytest

from config import BluePrint as source_blueprint
from scripts.params.generate_robinhood_defaults import deployment_readiness


def test_curve_graph_requires_accepted_h07_and_h08_bindings(
    fork_framework, accepted_preflight
):
    bindings = fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h07_artifacts", "h08_assertions")
    )
    assert tuple(bindings) == ("h07_artifacts", "h08_assertions")


def test_synthetic_curve_graph_drift_fails_against_bound_owner_fields(
    fork_framework, accepted_preflight
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h07_artifacts", "h08_assertions")
    )
    fields = (
        "blueprint_runtime_sha256",
        "compiler_settings_sha256",
        "pool_runtime_sha256",
        "source_closure_sha256",
    )
    owner = {
        field: f"{index:02x}" * 32
        for index, field in enumerate(fields, 1)
    }
    observed = {**owner, "pool_runtime_sha256": "ab" * 32}
    with pytest.raises(
        fork_framework.ForkFrameworkError, match="H09_CURVE_GRAPH_MISMATCH"
    ):
        fork_framework.consume_owner_output(
            owner,
            observed,
            required_fields=fields,
            code="H09_CURVE_GRAPH",
        )


@pytest.mark.rh_classification("blocked")
def test_launch_curve_pool_graph_remains_blocked_without_owner_identity(
    fork_framework, accepted_preflight
):
    kinds = {
        item.kind for item in accepted_preflight.identity_manifest.identities
    }
    assert "curve-pool" not in kinds
    assert "curve-blueprint" not in kinds


@pytest.mark.rh_classification("blocked")
def test_curve_launch_has_typed_blocked_receipt_without_archive_inputs(
    fork_framework, accepted_preflight
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h07_artifacts", "h08_assertions")
    )
    ready, blockers = deployment_readiness()
    assert ready is False
    assert (
        "curve:deployment_produced:pool.address:deployment_produced_unresolved"
        in blockers
    )
    assert any(
        item.endswith(":external_observation_unverified") for item in blockers
    )
    assert any(
        item.endswith(":owner_choice_unresolved") for item in blockers
    )


def test_curve_repository_candidates_do_not_become_owner_observations():
    rows = {
        row.input_id: row for row in source_blueprint.ROBINHOOD_CURVE_LAUNCH_INPUTS
    }
    for input_id in (
        "curve.address_provider",
        "curve.address_provider_binding_7",
        "curve.address_provider_binding_11",
        "curve.address_provider_binding_12",
        "curve.address_provider_binding_13",
    ):
        assert rows[input_id].authority_class == (
            "externally_verifiable_canonical_fact"
        )
        assert rows[input_id].resolution_state == (
            "selected_external_fact_unverified"
        )
    assert rows["pool.production_observation"].resolution_state == (
        "external_observation_unverified"
    )
