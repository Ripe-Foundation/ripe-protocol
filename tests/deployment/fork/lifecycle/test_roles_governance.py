from __future__ import annotations

import pytest

from config.robinhood_blueprint import ROBINHOOD_BLUEPRINT, Disposition


def _surface(surface_id):
    return next(
        surface
        for component in ROBINHOOD_BLUEPRINT.components
        for surface in component.surfaces
        if surface.surface_id == surface_id
    )


def test_synthetic_owner_role_graph_requires_accepted_action_binding(
    fork_framework, accepted_preflight
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h08_assertions", "typed_actions")
    )
    fields = ("governance", "guardian", "operator", "treasury")
    owner = {
        "governance": "synthetic-owner-governance",
        "guardian": "synthetic-owner-guardian",
        "operator": "synthetic-owner-operator",
        "treasury": "synthetic-owner-treasury",
    }
    assert fork_framework.consume_owner_output(
        owner,
        dict(owner),
        required_fields=fields,
        code="H09_ROLES",
    ) == owner


def test_governance_presence_does_not_activate_real_psm_surfaces(
    fork_framework, accepted_preflight
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h08_assertions", "typed_actions")
    )
    assert _surface("S-048-MINT").disposition is Disposition.DISABLED
    assert _surface("S-048-REDEEM").disposition is Disposition.DISABLED


def test_missing_synthetic_owner_role_is_blocked(
    fork_framework, accepted_preflight
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("typed_actions",)
    )
    fields = ("governance", "guardian")
    owner = {"governance": "synthetic-owner-governance", "guardian": None}
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_ROLES_OWNER_VALUE_MISSING",
    ):
        fork_framework.consume_owner_output(
            owner,
            owner,
            required_fields=fields,
            code="H09_ROLES",
        )
