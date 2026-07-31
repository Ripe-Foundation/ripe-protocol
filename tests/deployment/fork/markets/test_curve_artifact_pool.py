from __future__ import annotations

import pytest


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
def test_profile_two_curve_graph_remains_blocked_without_owner_identity(
    fork_framework, accepted_preflight
):
    kinds = {
        item.kind for item in accepted_preflight.identity_manifest.identities
    }
    assert "curve-pool" not in kinds
    assert "curve-blueprint" not in kinds
