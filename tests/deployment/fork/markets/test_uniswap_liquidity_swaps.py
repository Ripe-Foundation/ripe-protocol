from __future__ import annotations

import pytest


def test_constant_product_swap_math_and_rounding_are_deterministic(
    fork_framework, accepted_preflight
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h08_assertions",)
    )
    first = fork_framework.constant_product_amount_out(
        10_000,
        1_000_000,
        2_000_000,
        fee_numerator=3,
        fee_denominator=1000,
    )
    second = fork_framework.constant_product_amount_out(
        10_000,
        1_000_000,
        2_000_000,
        fee_numerator=3,
        fee_denominator=1000,
    )
    assert first == second == 19_743


def test_swap_reserve_delta_preserves_or_increases_invariant(
    fork_framework, accepted_preflight
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h08_assertions",)
    )
    reserve_in = 1_000_000
    reserve_out = 2_000_000
    amount_in = 10_000
    amount_out = fork_framework.constant_product_amount_out(
        amount_in,
        reserve_in,
        reserve_out,
        fee_numerator=3,
        fee_denominator=1000,
    )
    assert (reserve_in + amount_in) * (reserve_out - amount_out) >= (
        reserve_in * reserve_out
    )


@pytest.mark.parametrize(
    "values",
    (
        (0, 1, 1, 3, 1000),
        (1, 0, 1, 3, 1000),
        (1, 1, 0, 3, 1000),
        (1, 1, 1, 1000, 1000),
    ),
)
def test_invalid_swap_inputs_fail_closed(fork_framework, values):
    with pytest.raises(fork_framework.ForkFrameworkError):
        fork_framework.constant_product_amount_out(
            values[0],
            values[1],
            values[2],
            fee_numerator=values[3],
            fee_denominator=values[4],
        )


def test_v2_liquidity_observation_consumes_synthetic_owner_reserves(
    fork_framework, accepted_preflight
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h08_assertions",)
    )
    fields = ("reserve0", "reserve1")
    owner = {
        "reserve0": 100_000_003,
        "reserve1": 90_000_007,
    }
    assert fork_framework.consume_owner_output(
        owner,
        dict(owner),
        required_fields=fields,
        code="H09_UNISWAP_V2_LIQUIDITY",
    ) == owner
