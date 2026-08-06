from __future__ import annotations

import pytest


def test_synthetic_core_lifecycle_runs_inside_disposable_runtime(
    fork_framework, synthetic_disposable_runtime, accepted_preflight
):
    controller = synthetic_disposable_runtime
    controller.create()
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h08_assertions", "typed_actions")
    )
    for action in ("impersonate", "set_balance", "set_storage"):
        fork_framework.validate_local_fork_action(
            action,
            disposable_runtime_active=True,
            targets_local_fork=True,
        )
    initial = {
        "collateral": 0,
        "debt": 0,
        "synthetic_green_balance": 1_000_003,
        "vault_shares": 0,
    }
    state = dict(initial)
    state.update(collateral=500_009, vault_shares=500_009)
    state.update(debt=100_003)
    state.update(debt=0, collateral=0, vault_shares=0)
    assert state == initial
    proof = controller.destroy()
    assert proof.process_terminated is True
    assert proof.storage_disposed is True


def test_core_lifecycle_consumes_bound_synthetic_postconditions(
    fork_framework, accepted_preflight
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h08_assertions",)
    )
    fields = (
        "collateral_after",
        "debt_after",
        "green_after",
        "vault_shares_after",
    )
    owner = {
        "collateral_after": 0,
        "debt_after": 0,
        "green_after": 1_000_003,
        "vault_shares_after": 0,
    }
    assert fork_framework.consume_owner_output(
        owner,
        dict(owner),
        required_fields=fields,
        code="H09_CORE_LIFECYCLE",
    ) == owner


def test_core_lifecycle_synthetic_postcondition_drift_fails_closed(
    fork_framework, accepted_preflight
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h08_assertions",)
    )
    fields = ("collateral_after", "debt_after")
    owner = {"collateral_after": 0, "debt_after": 0}
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_CORE_LIFECYCLE_MISMATCH",
    ):
        fork_framework.consume_owner_output(
            owner,
            {"collateral_after": 0, "debt_after": 1},
            required_fields=fields,
            code="H09_CORE_LIFECYCLE",
        )
