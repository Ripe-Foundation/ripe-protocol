from __future__ import annotations

import pytest


def test_teller_snapshot_consumes_bound_synthetic_observation(
    fork_framework, accepted_preflight
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h08_assertions",)
    )
    fields = (
        "asset",
        "block_number",
        "price",
        "snapshot_count",
        "timestamp",
    )
    owner = {
        "asset": "owner-asset-fixture",
        "block_number": 100,
        "price": 10**18,
        "snapshot_count": 10,
        "timestamp": 1_800_000_000,
    }
    assert fork_framework.consume_owner_output(
        owner,
        dict(owner),
        required_fields=fields,
        code="H09_TELLER_SNAPSHOT",
    ) == owner


def test_snapshot_count_drift_fails_closed(
    fork_framework, accepted_preflight
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h08_assertions",)
    )
    fields = ("block_number", "snapshot_count", "timestamp")
    owner = {
        "block_number": 100,
        "snapshot_count": 10,
        "timestamp": 1_800_000_000,
    }
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_TELLER_SNAPSHOT_MISMATCH",
    ):
        fork_framework.consume_owner_output(
            owner,
            {**owner, "snapshot_count": 9},
            required_fields=fields,
            code="H09_TELLER_SNAPSHOT",
        )


def test_teller_snapshot_clock_uses_four_clock_validator(
    fork_framework, accepted_preflight
):
    pin = accepted_preflight.envelope.owner.pin
    expected = {
        "arbsys_number": pin.number,
        "evm_number": pin.number,
        "rpc_child_number": pin.number,
        "rpc_l1_number": pin.number - 1,
        "timestamp": pin.timestamp,
    }
    fork_framework.validate_clock_observation(**expected, expected=expected)


def test_teller_snapshot_gate_does_not_infer_missing_asset(
    fork_framework, accepted_preflight
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h08_assertions",)
    )
    fields = ("asset", "price")
    owner = {"asset": None, "price": 10**18}
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_TELLER_SNAPSHOT_OWNER_VALUE_MISSING",
    ):
        fork_framework.consume_owner_output(
            owner,
            owner,
            required_fields=fields,
            code="H09_TELLER_SNAPSHOT",
        )
