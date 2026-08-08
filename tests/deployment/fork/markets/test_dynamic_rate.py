from __future__ import annotations

import pytest


def test_dynamic_rate_requires_owner_plan_artifact_and_assertion_bindings(
    fork_framework, accepted_preflight
):
    bindings = fork_framework.require_owner_bindings(
        accepted_preflight.envelope,
        ("h05_plan", "h07_artifacts", "h08_assertions"),
    )
    assert tuple(bindings) == (
        "h05_plan",
        "h07_artifacts",
        "h08_assertions",
    )


def test_dynamic_rate_observation_binds_all_synthetic_owner_values(
    fork_framework, accepted_preflight
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope,
        ("h05_plan", "h07_artifacts", "h08_assertions"),
    )
    fields = ("ceiling", "floor", "period", "rate", "weight")
    owner = {
        "ceiling": 50_000,
        "floor": 10_000,
        "period": 10,
        "rate": 10_000,
        "weight": 10_000,
    }
    assert fork_framework.consume_owner_output(
        owner,
        dict(owner),
        required_fields=fields,
        code="H09_DYNAMIC_RATE",
    ) == owner


def test_dynamic_rate_is_blocked_when_synthetic_owner_value_is_omitted(
    fork_framework, accepted_preflight
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h08_assertions",)
    )
    fields = ("period", "rate")
    owner = {"period": 10, "rate": None}
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_DYNAMIC_RATE_OWNER_VALUE_MISSING",
    ):
        fork_framework.consume_owner_output(
            owner,
            owner,
            required_fields=fields,
            code="H09_DYNAMIC_RATE",
        )
