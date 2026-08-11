from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path

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
    ccip_live_assertion_expectations,
)
from scripts.utils.migration_runner import (
    ROBINHOOD_RESERVATIONS,
    ccip_external_existing_stages,
)


def expectations():
    ccip_capabilities, ccip_external_facts = ccip_live_assertion_expectations()
    return {
        "schema_version": 1,
        "profile_id": "robinhood-mainnet",
        "profile_kind": "profile1",
        "chain_id": 4663,
        "capabilities": ccip_capabilities,
        "external_facts": ccip_external_facts,
    }


def observations():
    policy = blueprint_policy()
    ccip_capabilities, ccip_external_facts = ccip_live_assertion_expectations()
    return {
        "schema_version": 1,
        "mode": "synthetic",
        "profile_id": "robinhood-mainnet",
        "chain_id": 4663,
        "capabilities": ccip_capabilities,
        "external_facts": ccip_external_facts,
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
    assert len(policy.required_registries) == 34
    assert len(policy.reserved_registries) == 4
    assert policy.unavailable_components["CM-008"] is Disposition.BLOCKED
    assert {"CM-051", "CM-052", "CM-053", "CM-058"} <= (
        policy.required_components
    )


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


def test_blocked_registry_is_reserved_and_live_ccip_ids_are_required():
    policy = blueprint_policy()
    assert policy.canonical_registries[("ripe_hq", 4)] == "CM-008"
    assert policy.canonical_registries[("ripe_hq", 23)] == "CM-052"
    assert policy.canonical_registries[("ripe_hq", 24)] == "CM-051"
    assert ("ripe_hq", 4) in policy.reserved_registries
    assert {("ripe_hq", 23), ("ripe_hq", 24)} <= policy.required_registries
    assert not {("ripe_hq", 23), ("ripe_hq", 24)} & policy.reserved_registries


def test_migration_planner_represents_live_ccip_as_external_state_not_deferred():
    reservation = next(
        row for row in ROBINHOOD_RESERVATIONS if row.migration_id == "1000"
    )
    assert reservation.disposition == "confirmed_external_state_gated"
    assert ccip_external_existing_stages() == [
        {
            "migration_id": "1000",
            "semantic_id": "ccip-pools-and-registration",
            "state": "confirmed_existing_live_state",
            "reason": (
                "ccip-live-state-observed-outside-launch-mutation-graph; "
                "any further transaction remains separately gated"
            ),
            "blockers": ["B-T1-CCIP", "B-T1-TOOLCHAIN"],
        }
    ]


def test_historical_ccip_status_surfaces_carry_currentness_overlays():
    root = Path(__file__).resolve().parents[2]
    historical_surfaces = (
        "docs/chains/rh-summary.md",
        "docs/chains/rh/block-clock-validation-plan.md",
        "docs/chains/rh/block-number-inventory.md",
        "docs/chains/rh/component-matrix.md",
        "docs/chains/rh/reassessment-and-qualification-synthesis.md",
        "docs/chains/rh/robinhood-deployment-support-specification.md",
        "docs/chains/rh/robinhood-deployment-validation-plan.md",
        "docs/chains/rh/smart-contract-changes/defaults-robinhood.md",
        "docs/chains/rh/smart-contract-changes/guarded-erc20.md",
        "docs/chains/rh/smart-contract-changes/lootbox.md",
        "docs/chains/rh/smart-contract-changes/teller.md",
        "docs/chains/rh/hardening/BASELINE.md",
        "docs/chains/rh/hardening/hardening-pass-report.md",
    )
    for relative in historical_surfaces:
        prefix = (root / relative).read_text()[:4_000]
        assert (
            "11 August 2026 CCIP" in prefix
            or "CCIP supersession note (2026-08-11)" in prefix
        ), relative
        assert "ccip-live-state.md" in prefix, relative

    current = (root / "docs/chains/rh/ccip-live-state.md").read_text()
    assert "LIVE TOPOLOGY CONFIRMED" in current
    assert "exact live source set" in current
    assert "41acd8763b41d45ecef8541d1a31b8ac58cc582cc0a333d3f5f2f31f9e7357fa" in current

    question_packet = (
        root / "docs/chains/rh/ccip-chainlink-question-packet.md"
    ).read_text()
    assert "relationship to the repository's 1.5.1 candidate are unresolved" in (
        question_packet
    )
    assert "deployed and activated from the repository's 1.5.1" not in (
        question_packet
    )

    status = (root / "docs/chains/rh/status.yaml").read_text()
    assert "64 unresolved or unverified bindings" in status
    assert "deployment_readiness_blockers: 64" in status
    assert "deployment_readiness_blocker_count: 64" in status
    assert "Sixty-four unresolved or unverified bindings" in status

    current_topology_surfaces = (
        "docs/chains/rh-summary.md",
        "docs/chains/rh/current-owner-priorities.md",
        "docs/chains/rh/curve-launch-activation.md",
        "docs/chains/rh/curve-launch-migration-handoff.md",
        "docs/chains/rh/decision-register.md",
        "docs/chains/rh/reassessment-and-qualification-synthesis.md",
    )
    for relative in current_topology_surfaces:
        content = (root / relative).read_text()
        assert "[1, 2]" in content or "[1,2]" in content, relative
        assert "[1, 3]" not in content, relative
        assert "[1,3]" not in content, relative

    for relative in (
        "docs/chains/rh/robinhood-deployment-support-specification.md",
        "docs/chains/rh/robinhood-deployment-validation-plan.md",
    ):
        current_overlay = (root / relative).read_text()[:4_000]
        assert "[1,2]" in current_overlay, relative
        assert "[1,3]" not in current_overlay, relative

    runner = (root / "scripts/utils/migration_runner.py").read_text()
    assert "ccip-deferred-outside-launch-graph" not in runner


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
