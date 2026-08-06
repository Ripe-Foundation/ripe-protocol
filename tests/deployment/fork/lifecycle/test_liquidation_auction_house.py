from __future__ import annotations

import pytest


def test_synthetic_liquidation_and_auction_run_in_disposable_runtime(
    fork_framework, synthetic_disposable_runtime, accepted_preflight
):
    controller = synthetic_disposable_runtime
    controller.create()
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h08_assertions", "typed_actions")
    )
    fork_framework.validate_local_fork_action(
        "set_storage",
        disposable_runtime_active=True,
        targets_local_fork=True,
    )
    state = {
        "auction_collateral": 0,
        "borrower_collateral": 500_009,
        "borrower_debt": 100_003,
    }
    state.update(auction_collateral=500_009, borrower_collateral=0)
    assert state["auction_collateral"] == 500_009
    state.update(auction_collateral=0, borrower_debt=0)
    assert state["auction_collateral"] == state["borrower_debt"] == 0
    controller.destroy()


def test_auction_house_consumes_bound_synthetic_postconditions(
    fork_framework, accepted_preflight
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h08_assertions",)
    )
    fields = (
        "auction_closed",
        "collateral_delivered",
        "debt_repaid",
        "green_charged",
    )
    owner = {
        "auction_closed": True,
        "collateral_delivered": 500_009,
        "debt_repaid": 100_003,
        "green_charged": 100_003,
    }
    assert fork_framework.consume_owner_output(
        owner,
        dict(owner),
        required_fields=fields,
        code="H09_AUCTION_HOUSE",
    ) == owner


def test_synthetic_partial_delivery_mismatch_fails_closed(
    fork_framework, accepted_preflight
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h08_assertions",)
    )
    fields = ("collateral_delivered", "green_charged")
    owner = {
        "collateral_delivered": 500_009,
        "green_charged": 100_003,
    }
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_AUCTION_HOUSE_MISMATCH",
    ):
        fork_framework.consume_owner_output(
            owner,
            {**owner, "collateral_delivered": 499_999},
            required_fields=fields,
            code="H09_AUCTION_HOUSE",
        )
