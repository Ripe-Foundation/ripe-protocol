from __future__ import annotations

import pytest


def test_exact_clock_observation_is_accepted(fork_framework):
    expected = {
        "rpc_child_number": 100,
        "rpc_l1_number": 90,
        "evm_number": 100,
        "timestamp": 1_800_000_000,
        "arbsys_number": 100,
    }
    fork_framework.validate_clock_observation(**expected, expected=expected)


@pytest.mark.parametrize(
    "field",
    (
        "rpc_child_number",
        "rpc_l1_number",
        "evm_number",
        "timestamp",
        "arbsys_number",
    ),
)
def test_each_clock_divergence_fails_closed(fork_framework, field):
    expected = {
        "rpc_child_number": 100,
        "rpc_l1_number": 90,
        "evm_number": 100,
        "timestamp": 1_800_000_000,
        "arbsys_number": 100,
    }
    observed = dict(expected)
    observed[field] += 1
    with pytest.raises(
        fork_framework.ForkFrameworkError, match="H09_CLOCK_DIVERGENCE"
    ):
        fork_framework.validate_clock_observation(
            **observed, expected=expected
        )


def test_missing_clock_field_is_rejected(fork_framework):
    expected = {
        "rpc_child_number": 100,
        "evm_number": 100,
        "timestamp": 1_800_000_000,
        "arbsys_number": 100,
    }
    with pytest.raises(
        fork_framework.ForkFrameworkError, match="H09_CLOCK_FIELDS"
    ):
        fork_framework.validate_clock_observation(
            rpc_child_number=100,
            rpc_l1_number=90,
            evm_number=100,
            timestamp=1_800_000_000,
            arbsys_number=100,
            expected=expected,
        )
