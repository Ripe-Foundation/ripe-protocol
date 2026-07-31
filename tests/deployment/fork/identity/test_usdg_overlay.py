from __future__ import annotations

import pytest


@pytest.mark.rh_classification("blocked")
def test_usdg_overlay_remains_blocked_without_accepted_layout_identity(
    fork_framework, accepted_preflight
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h07_artifacts", "h08_assertions")
    )
    identity_ids = {
        identity.identity_id
        for identity in accepted_preflight.identity_manifest.identities
    }
    assert "usdg-proxy" not in identity_ids
    assert "usdg-implementation" not in identity_ids


def test_synthetic_usdg_layout_missing_value_is_blocked(
    fork_framework, accepted_preflight
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h08_assertions",)
    )
    fields = (
        "balance_mapping_slot",
        "getter_to_slot_proved",
        "total_supply_slot",
    )
    owner = {
        "balance_mapping_slot": None,
        "getter_to_slot_proved": False,
        "total_supply_slot": None,
    }
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_USDG_OVERLAY_OWNER_VALUE_MISSING",
    ):
        fork_framework.consume_owner_output(
            owner,
            owner,
            required_fields=fields,
            code="H09_USDG_OVERLAY",
        )


def test_exactly_two_synthetic_storage_deltas_use_disposable_runtime(
    fork_framework, synthetic_disposable_runtime, accepted_preflight
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h08_assertions", "typed_actions")
    )
    controller = synthetic_disposable_runtime
    controller.create()
    deltas = {
        "balance-delta": b"synthetic-balance-delta",
        "supply-delta": b"synthetic-supply-delta",
    }
    for name, value in deltas.items():
        fork_framework.validate_local_fork_action(
            "set_storage",
            disposable_runtime_active=True,
            targets_local_fork=True,
        )
        (controller.runtime_dir / name).write_bytes(value)
    names = tuple(
        sorted(path.name for path in controller.runtime_dir.iterdir())
    )
    assert names == (
        "balance-delta",
        "supply-delta",
    )
    proof = controller.destroy()
    assert proof.storage_disposed is True


def test_candidate_usdg_identity_cannot_replace_accepted_token_identity(
    fork_framework, accepted_preflight
):
    token = next(
        identity
        for identity in accepted_preflight.identity_manifest.identities
        if identity.kind == "token"
    )
    fields = ("address", "runtime_code_sha256")
    owner = {
        "address": token.address,
        "runtime_code_sha256": token.runtime_code_sha256,
    }
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_USDG_IDENTITY_MISMATCH",
    ):
        fork_framework.consume_owner_output(
            owner,
            {**owner, "address": "0x3333333333333333333333333333333333333333"},
            required_fields=fields,
            code="H09_USDG_IDENTITY",
        )
