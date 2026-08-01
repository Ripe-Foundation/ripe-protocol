from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

import pytest

from config.robinhood_blueprint import ROBINHOOD_BLUEPRINT, Disposition
from scripts.utils.deployment_assertions import (
    REQUIRED_DISPOSITIONS,
    SUPPORTED_DISPOSITIONS,
    UNAVAILABLE_DISPOSITIONS,
    DeploymentAssertionInputError,
    assert_deployment,
    blueprint_policy,
    blueprint_registry_map,
)


def expectations():
    return {
        "schema_version": 1,
        "profile_id": "robinhood-mainnet",
        "profile_kind": "profile1",
        "chain_id": 4663,
    }


def observations():
    policy = blueprint_policy()
    return {
        "schema_version": 1,
        "mode": "synthetic",
        "profile_id": "robinhood-mainnet",
        "chain_id": 4663,
        "registries": [
            {
                "domain": domain,
                "registry_id": registry_id,
                "component_id": policy.canonical_registries[(domain, registry_id)],
            }
            for domain, registry_id in sorted(policy.required_registries)
        ],
    }


def codes(report):
    return {failure.code for failure in report.failures}


def test_blueprint_policy_handles_every_disposition_explicitly():
    assert REQUIRED_DISPOSITIONS == {Disposition.REQUIRED}
    assert UNAVAILABLE_DISPOSITIONS == {
        Disposition.OMITTED,
        Disposition.DISABLED,
        Disposition.DEFERRED,
        Disposition.BLOCKED,
    }
    assert SUPPORTED_DISPOSITIONS == frozenset(Disposition)

    policy = blueprint_policy()
    assert len(policy.required_registries) == 32
    assert len(policy.reserved_registries) == 6
    assert policy.unavailable_components["CM-008"] is Disposition.BLOCKED
    assert policy.unavailable_components["CM-051"] is Disposition.DEFERRED


def test_price_desk_selected_one_two_three_and_unavailable_others_are_exact():
    policy = blueprint_policy()
    assert policy.canonical_registries[("price_desk", 1)] == "CM-016"
    assert policy.canonical_registries[("price_desk", 2)] == "CM-017"
    assert policy.canonical_registries[("price_desk", 3)] == "CM-018"
    assert {
        key for key in policy.required_registries if key[0] == "price_desk"
    } == {
        ("price_desk", 1),
        ("price_desk", 2),
        ("price_desk", 3),
    }
    assert {
        key for key in policy.reserved_registries if key[0] == "price_desk"
    } == {
        ("price_desk", 4),
        ("price_desk", 5),
    }

    value = observations()
    curve = next(
        row
        for row in value["registries"]
        if (row["domain"], row["registry_id"]) == ("price_desk", 2)
    )
    curve["component_id"] = "CM-018"
    assert "SHIFTED_REGISTRY_ID" in codes(
        assert_deployment(expectations(), value)
    )


def test_vault_book_ids_and_omitted_four_are_exact():
    policy = blueprint_policy()
    assert {
        key: policy.canonical_registries[key]
        for key in policy.canonical_registries
        if key[0] == "vault_book"
    } == {
        ("vault_book", 1): "CM-022",
        ("vault_book", 2): "CM-023",
        ("vault_book", 3): "CM-024",
        ("vault_book", 4): "CM-025",
    }
    assert ("vault_book", 4) in policy.reserved_registries


def test_blocked_and_deferred_registry_ids_are_reserved():
    policy = blueprint_policy()
    assert policy.canonical_registries[("ripe_hq", 4)] == "CM-008"
    assert policy.canonical_registries[("ripe_hq", 23)] == "CM-051"
    assert policy.canonical_registries[("ripe_hq", 24)] == "CM-052"
    assert {
        ("ripe_hq", 4),
        ("ripe_hq", 23),
        ("ripe_hq", 24),
    } <= policy.reserved_registries


def test_shift_duplicate_and_reserved_reuse_fail_closed():
    shifted = observations()
    for row in shifted["registries"]:
        if row["domain"] == "price_desk" and row["registry_id"] == 1:
            row["component_id"] = "CM-017"
            break
    assert "SHIFTED_REGISTRY_ID" in codes(
        assert_deployment(expectations(), shifted)
    )

    duplicate = observations()
    duplicate["registries"].append(deepcopy(duplicate["registries"][0]))
    assert "DUPLICATE_REGISTRY_ID" in codes(
        assert_deployment(expectations(), duplicate)
    )


@pytest.mark.parametrize("replacement", ("CM-018", "CM-999", "0x0000000000000000000000000000000000000000"))
def test_curve_slot_rejects_bluechip_unrelated_and_zero_placeholders(replacement):
    value = observations()
    curve = next(
        row
        for row in value["registries"]
        if (row["domain"], row["registry_id"]) == ("price_desk", 2)
    )
    curve["component_id"] = replacement
    assert "SHIFTED_REGISTRY_ID" in codes(
        assert_deployment(expectations(), value)
    )


def test_missing_required_registry_fails_closed():
    value = observations()
    value["registries"].pop()
    assert "MISSING_REQUIRED_REGISTRY" in codes(
        assert_deployment(expectations(), value)
    )


def test_blueprint_registry_collisions_fail_before_assertion_evaluation():
    component = ROBINHOOD_BLUEPRINT.components[0]
    assert component.registry_expectations
    duplicate = replace(
        ROBINHOOD_BLUEPRINT,
        components=(
            replace(
                component,
                registry_expectations=(
                    *component.registry_expectations,
                    component.registry_expectations[0],
                ),
            ),
            *ROBINHOOD_BLUEPRINT.components[1:],
        ),
    )
    with pytest.raises(DeploymentAssertionInputError, match="duplicate registry key"):
        blueprint_registry_map(duplicate)


def test_malformed_component_disposition_cannot_fall_through_policy():
    component = ROBINHOOD_BLUEPRINT.components[0]
    malformed = replace(
        ROBINHOOD_BLUEPRINT,
        components=(
            replace(component, deployment="future-disposition"),
            *ROBINHOOD_BLUEPRINT.components[1:],
        ),
    )
    with pytest.raises(
        DeploymentAssertionInputError,
        match="component disposition is unsupported",
    ):
        blueprint_policy(malformed)
