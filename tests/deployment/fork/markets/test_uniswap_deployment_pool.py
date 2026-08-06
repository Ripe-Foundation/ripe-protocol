from __future__ import annotations

import pytest


def test_synthetic_v2_deployment_and_pair_graph_bind_exactly(
    fork_framework, accepted_preflight
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h07_artifacts", "h08_assertions")
    )
    fields = (
        "factory_runtime_sha256",
        "pair_runtime_sha256",
        "router_runtime_sha256",
    )
    owner = {
        field: f"{index:02x}" * 32
        for index, field in enumerate(fields, 1)
    }
    assert fork_framework.consume_owner_output(
        owner,
        dict(owner),
        required_fields=fields,
        code="H09_UNISWAP_V2",
    ) == owner


def test_v2_pair_token_order_is_address_numeric_and_unique(fork_framework):
    high = "0xFf00000000000000000000000000000000000000"
    low = "0x0100000000000000000000000000000000000000"
    assert fork_framework.ordered_token_pair(high, low) == (low, high)
    with pytest.raises(
        fork_framework.ForkFrameworkError, match="H09_PAIR_DUPLICATE"
    ):
        fork_framework.ordered_token_pair(low, low)


def test_candidate_v2_pair_cannot_replace_synthetic_owner_graph(
    fork_framework, accepted_preflight
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h08_assertions",)
    )
    fields = ("pair", "token0", "token1")
    owner = {
        "pair": "synthetic-owner-v2-pair",
        "token0": "synthetic-owner-token-0",
        "token1": "synthetic-owner-token-1",
    }
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_UNISWAP_V2_PAIR_MISMATCH",
    ):
        fork_framework.consume_owner_output(
            owner,
            {**owner, "pair": "synthetic-candidate-v2-pair"},
            required_fields=fields,
            code="H09_UNISWAP_V2_PAIR",
        )


@pytest.mark.rh_classification("blocked")
def test_uniswap_has_no_accepted_launch_oracle_identity(
    accepted_preflight,
):
    accepted_kinds = {
        identity.kind
        for identity in accepted_preflight.identity_manifest.identities
    }
    assert "uniswap-price-source" not in accepted_kinds
