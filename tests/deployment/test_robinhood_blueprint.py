from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from pathlib import Path

import pytest

from config import BluePrint as blueprint_source
from config.BluePrint import ADDYS, CORE_TOKENS, WHALES, YIELD_TOKENS
from config.robinhood_blueprint import (
    ROBINHOOD_BLUEPRINT,
    ROBINHOOD_BLUEPRINT_ID,
    ROBINHOOD_PROFILE_IDS,
    AuthorityClass,
    Blocker,
    ComponentRecord,
    ComponentRelation,
    Disposition,
    LifecyclePhase,
    PromotionRecord,
    Profile1LaunchSelection,
    RegistryDomain,
    RegistryExpectation,
    RegistryIdAuthority,
    RelationKind,
    RelationPhase,
    RobinhoodBlueprint,
    RobinhoodBlueprintError,
    SourceClass,
    SourcePathKind,
    SourcePathRecord,
    SourcePathState,
    SurfaceKind,
    SurfaceRecord,
    SymbolicInput,
    _validate_symbolic_authority_classes,
    get_blocker,
    get_component,
    get_promotion,
    get_robinhood_blueprint,
    get_symbolic_input,
    validate_blueprint,
)


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "config" / "robinhood_blueprint.py"
BASE_BLUEPRINT = ROOT / "config" / "BluePrint.py"
BASE_MANIFEST = (
    ROOT
    / "migration_history"
    / "base-mainnet"
    / "v1"
    / "current-manifest.json"
)
RELEVANT_ENV = (
    "BASESCAN_API_KEY",
    "ETHERSCAN_API_KEY",
    "WEB3_ALCHEMY_API_KEY",
    "BASE_MAINNET_RPC_URL",
    "BASE_SEPOLIA_RPC_URL",
    "ROBINHOOD_MAINNET_RPC_URL",
    "ROBINHOOD_TESTNET_RPC_URL",
    "DEPLOYER_PRIVATE_KEY",
    "TEST_PRIVATE_KEY",
)


def all_surfaces(blueprint=ROBINHOOD_BLUEPRINT):
    return tuple(
        surface
        for component in blueprint.components
        for surface in component.surfaces
    )


def all_relations(blueprint=ROBINHOOD_BLUEPRINT):
    return tuple(
        (component.component_id, relation)
        for component in blueprint.components
        for relation in component.relations
    )


def all_paths(blueprint=ROBINHOOD_BLUEPRINT):
    return tuple(
        (component.component_id, source)
        for component in blueprint.components
        for source in component.source_paths
    )


def all_registries(blueprint=ROBINHOOD_BLUEPRINT):
    return tuple(
        expectation
        for component in blueprint.components
        for expectation in component.registry_expectations
    )


def replace_component(component_id, **changes):
    components = tuple(
        replace(component, **changes)
        if component.component_id == component_id
        else component
        for component in ROBINHOOD_BLUEPRINT.components
    )
    return replace(ROBINHOOD_BLUEPRINT, components=components)


def replace_surface(surface_id, **changes):
    for component in ROBINHOOD_BLUEPRINT.components:
        if any(
            surface.surface_id == surface_id
            for surface in component.surfaces
        ):
            surfaces = tuple(
                replace(surface, **changes)
                if surface.surface_id == surface_id
                else surface
                for surface in component.surfaces
            )
            return replace_component(
                component.component_id,
                surfaces=surfaces,
            )
    raise AssertionError(surface_id)


def replace_relation(relation_id, **changes):
    for component in ROBINHOOD_BLUEPRINT.components:
        if any(
            relation.relation_id == relation_id
            for relation in component.relations
        ):
            relations = tuple(
                replace(relation, **changes)
                if relation.relation_id == relation_id
                else relation
                for relation in component.relations
            )
            return replace_component(
                component.component_id,
                relations=relations,
            )
    raise AssertionError(relation_id)


def assert_code(code, candidate):
    with pytest.raises(RobinhoodBlueprintError) as error:
        validate_blueprint(candidate)
    assert error.value.code == code


def address_strings(value):
    if isinstance(value, dict):
        values = value.values()
    elif isinstance(value, (tuple, list, set)):
        values = value
    else:
        values = ()
    result = {
        item
        for item in values
        if isinstance(item, str)
        and item.startswith("0x")
        and len(item) == 42
    }
    for item in values:
        result.update(address_strings(item))
    return result


def test_public_api_and_exact_profiles_share_one_singleton():
    assert ROBINHOOD_BLUEPRINT_ID == "robinhood-v1"
    assert ROBINHOOD_PROFILE_IDS == (
        "robinhood-mainnet",
        "robinhood-testnet",
    )
    mainnet = get_robinhood_blueprint("robinhood-mainnet")
    testnet = get_robinhood_blueprint("robinhood-testnet")
    assert mainnet is testnet is ROBINHOOD_BLUEPRINT
    assert mainnet.profile_ids == ROBINHOOD_PROFILE_IDS


@pytest.mark.parametrize(
    "profile_id",
    (
        "ROBINHOOD-MAINNET",
        "Robinhood-Testnet",
        "robinhood",
        "base",
        "base-mainnet",
        "base-sepolia",
        "local",
        "unknown",
        "",
        None,
    ),
)
def test_nonexact_profiles_are_rejected_before_h02_lookup(
    monkeypatch, profile_id
):
    events = []
    monkeypatch.setattr(
        "config.robinhood_blueprint.get_profile",
        lambda value: events.append(value),
    )
    with pytest.raises(RobinhoodBlueprintError) as error:
        get_robinhood_blueprint(profile_id)
    assert error.value.code == "H03_PROFILE_EXACT"
    assert events == []


def test_closed_enums_have_exact_approved_values():
    assert {value.value for value in AuthorityClass} == {
        "repository_approved",
        "externally_verifiable_canonical_fact",
        "owner_selected",
        "deployment_produced",
    }
    assert {value.value for value in Disposition} == {
        "required",
        "omitted",
        "disabled",
        "deferred",
        "blocked",
    }
    assert {value.value for value in SurfaceKind} == {
        "artifact",
        "capability",
        "route",
        "permission",
        "configuration",
        "registration",
        "behavioral_invariant",
    }
    assert {value.value for value in LifecyclePhase} == {
        "deployed_initial_value",
        "pre_activation_configuration",
        "atomic_stock_activation",
        "within_seven_day_separately_reviewed_ccip_promotion",
        "within_seven_day_separately_reviewed_reward_activation",
        "post_launch_release",
        "omitted",
        "blocked",
    }
    assert {value.value for value in RelationPhase} == {
        "constructor",
        "bootstrap",
        "post_deployment_setup",
        "registration_order",
        "runtime_security",
    }
    assert {value.value for value in RelationKind} == {
        "construction_dependency",
        "bootstrap_dependency",
        "setup_dependency",
        "registration_order_dependency",
        "direct_execution",
        "authority_dependency",
        "indirect_security_dependency",
    }
    assert {value.value for value in SourcePathState} == {
        "existing",
        "reviewed_planned",
        "external_pending",
        "absent",
    }
    assert {value.value for value in SourcePathKind} == {
        "file",
        "directory",
        "none",
    }
    assert {value.value for value in SourceClass} == {
        "shared_contract",
        "chain_specific_config",
        "external_integration",
        "non_onchain_tooling",
        "external_artifact",
    }
    assert {value.value for value in RegistryDomain} == {
        "ripe_hq",
        "vault_book",
        "price_desk",
        "switchboard",
    }
    assert {value.value for value in RegistryIdAuthority} == {
        "source_hard_coded",
        "registration_order",
        "provisional_reservation",
    }


def test_frozen_slotted_records_have_exact_approved_fields():
    expected = {
        ComponentRelation: (
            "relation_id",
            "kind",
            "phase",
            "target_component_id",
            "source_proof_refs",
            "basis",
            "evidence_authority_ids",
        ),
        SourcePathRecord: (
            "path",
            "path_kind",
            "path_state",
            "source_class",
            "evidence_id",
        ),
        SymbolicInput: (
            "field_id",
            "semantic_class",
            "authority_class",
            "consumers",
            "primary_owner_id",
            "co_owner_ids",
            "deadline_gate",
            "status",
            "blocker_ids",
        ),
        Blocker: (
            "blocker_id",
            "primary_owner_id",
            "co_owner_ids",
            "summary",
            "deadline_gate",
        ),
        SurfaceRecord: (
            "surface_id",
            "component_id",
            "kind",
            "semantic_meaning",
            "disposition",
            "lifecycle_phase",
            "blocker_ids",
            "assertion_ids",
        ),
        PromotionRecord: (
            "promotion_id",
            "surface_ids",
            "promotion_phase",
            "disposition",
            "primary_owner_id",
            "co_owner_ids",
            "blocker_ids",
            "assertion_ids",
        ),
            Profile1LaunchSelection: (
                "source_commit",
                "source_paths",
                "external_fact_input_ids",
            "deployment_produced_input_ids",
            "excluded_lanes",
        ),
        RegistryExpectation: (
            "domain",
            "registry_id",
            "semantic_name",
            "authority",
            "component_id",
            "disposition",
        ),
        ComponentRecord: (
            "component_id",
            "name",
            "source_paths",
            "deployment",
            "registry_expectations",
            "surfaces",
            "relations",
            "blocker_ids",
            "primary_owner_id",
            "co_owner_ids",
            "negative_assertion_ids",
            "downstream_slices",
            "controlling_evidence_ids",
        ),
        RobinhoodBlueprint: (
            "blueprint_id",
            "profile_ids",
            "profile1_selection",
            "symbolic_inputs",
            "blockers",
            "promotions",
            "components",
        ),
    }
    for record_type, names in expected.items():
        assert tuple(field.name for field in fields(record_type)) == names
        assert record_type.__dataclass_params__.frozen
        assert hasattr(record_type, "__slots__")


def test_complete_inventory_and_cardinality_reconciliation():
    components = ROBINHOOD_BLUEPRINT.components
    surfaces = all_surfaces()
    relations = all_relations()
    paths = all_paths()
    registries = all_registries()

    assert len(components) == 60
    assert tuple(component.component_id for component in components) == tuple(
        f"CM-{value:03d}" for value in range(1, 61)
    )
    assert Counter(component.deployment for component in components) == {
        Disposition.REQUIRED: 43,
        Disposition.OMITTED: 14,
        Disposition.DEFERRED: 2,
        Disposition.BLOCKED: 1,
    }
    assert len(surfaces) == 100
    assert Counter(surface.kind for surface in surfaces) == {
        SurfaceKind.ARTIFACT: 8,
        SurfaceKind.CAPABILITY: 19,
        SurfaceKind.ROUTE: 45,
        SurfaceKind.PERMISSION: 3,
        SurfaceKind.CONFIGURATION: 8,
        SurfaceKind.REGISTRATION: 8,
        SurfaceKind.BEHAVIORAL_INVARIANT: 9,
    }
    assert Counter(surface.disposition for surface in surfaces) == {
        Disposition.REQUIRED: 19,
        Disposition.OMITTED: 20,
        Disposition.DISABLED: 22,
        Disposition.DEFERRED: 3,
        Disposition.BLOCKED: 36,
    }
    assert Counter(surface.lifecycle_phase for surface in surfaces) == {
        LifecyclePhase.DEPLOYED_INITIAL_VALUE: 32,
        LifecyclePhase.PRE_ACTIVATION_CONFIGURATION: 20,
        LifecyclePhase.ATOMIC_STOCK_ACTIVATION: 4,
        LifecyclePhase.POST_LAUNCH_RELEASE: 6,
        LifecyclePhase.OMITTED: 20,
        LifecyclePhase.BLOCKED: 18,
    }
    assert len(relations) == 296
    assert Counter(relation.phase for _, relation in relations) == {
        RelationPhase.CONSTRUCTOR: 40,
        RelationPhase.BOOTSTRAP: 3,
        RelationPhase.POST_DEPLOYMENT_SETUP: 3,
        RelationPhase.REGISTRATION_ORDER: 32,
        RelationPhase.RUNTIME_SECURITY: 218,
    }
    assert Counter(relation.kind for _, relation in relations) == {
        RelationKind.CONSTRUCTION_DEPENDENCY: 40,
        RelationKind.BOOTSTRAP_DEPENDENCY: 3,
        RelationKind.SETUP_DEPENDENCY: 3,
        RelationKind.REGISTRATION_ORDER_DEPENDENCY: 32,
        RelationKind.DIRECT_EXECUTION: 167,
        RelationKind.AUTHORITY_DEPENDENCY: 40,
        RelationKind.INDIRECT_SECURITY_DEPENDENCY: 11,
    }
    assert (
        len(
            {
                (source, relation.phase, relation.target_component_id)
                for source, relation in relations
            }
        )
        == 292
    )
    assert len(paths) == 103
    assert Counter(source.path_kind for _, source in paths) == {
        SourcePathKind.FILE: 96,
        SourcePathKind.DIRECTORY: 6,
        SourcePathKind.NONE: 1,
    }
    assert Counter(source.path_state for _, source in paths) == {
        SourcePathState.EXISTING: 96,
        SourcePathState.REVIEWED_PLANNED: 6,
        SourcePathState.ABSENT: 1,
    }
    assert Counter(source.source_class for _, source in paths) == {
        SourceClass.SHARED_CONTRACT: 53,
        SourceClass.NON_ONCHAIN_TOOLING: 36,
        SourceClass.EXTERNAL_INTEGRATION: 9,
        SourceClass.CHAIN_SPECIFIC_CONFIG: 3,
        SourceClass.EXTERNAL_ARTIFACT: 2,
    }
    # 49 after I-STOCK-VAULT-ARTIFACT was removed with the retired
    # artifact-expectations pipeline; it asserted SimpleErc20 artifact
    # identity and nothing else.
    assert len(ROBINHOOD_BLUEPRINT.symbolic_inputs) == 49
    assert len(ROBINHOOD_BLUEPRINT.blockers) == 28
    assert len(registries) == 35
    assert Counter(item.domain for item in registries) == {
        RegistryDomain.RIPE_HQ: 24,
        RegistryDomain.VAULT_BOOK: 4,
        RegistryDomain.PRICE_DESK: 2,
        RegistryDomain.SWITCHBOARD: 5,
    }
    assert len(ROBINHOOD_BLUEPRINT.promotions) == 1


def test_primary_and_nested_structures_are_immutable():
    component = get_component("CM-001")
    surface = component.surfaces[0]
    with pytest.raises(FrozenInstanceError):
        ROBINHOOD_BLUEPRINT.blueprint_id = "other"
    with pytest.raises(FrozenInstanceError):
        component.name = "other"
    with pytest.raises(FrozenInstanceError):
        surface.disposition = Disposition.REQUIRED
    with pytest.raises(AttributeError):
        component.surfaces.append(surface)
    with pytest.raises(AttributeError):
        ROBINHOOD_BLUEPRINT.components.clear()

    assert_code(
        "H03_IMMUTABLE",
        replace(ROBINHOOD_BLUEPRINT, components=list(ROBINHOOD_BLUEPRINT.components)),
    )
    assert_code(
        "H03_IMMUTABLE",
        replace_component("CM-001", relations=list(component.relations)),
    )


def test_profile1_launch_selection_is_exact_and_exclusion_complete():
    selection = ROBINHOOD_BLUEPRINT.profile1_selection
    assert selection.source_commit == (
        "74c4120fbfa1ade859dc32f61acdf567c139fe02"
    )
    assert selection.source_paths == (
        "config/BluePrint.py",
        "contracts/config/DefaultsRobinhood.vy",
    )
    assert set(selection.excluded_lanes) == {
        "PSM_PARAMETERS_OR_ACTIVATION",
        "DELEVERAGE_VALUES",
        "CREDIT_ENGINE_ZERO_BACKING",
        "CURVE_HIGHER_POWERS_OR_LP_ACTIVATION",
        "UNISWAP",
        "OLD_MIGRATION_NAMESPACE_AND_CUSTOM_RUNNER",
    }


def test_symbolic_inputs_are_value_free_owned_gated_and_bidirectional():
    expected = {
        component.component_id: {
            item.field_id
            for item in ROBINHOOD_BLUEPRINT.symbolic_inputs
            if component.component_id in item.consumers
        }
        for component in ROBINHOOD_BLUEPRINT.components
    }
    assert expected["CM-001"] >= {
        "I-GREEN",
        "I-GREEN-INITIAL-SUPPLY",
        "I-GREEN-INITIAL-SUPPLY-RECIPIENT",
    }
    for item in ROBINHOOD_BLUEPRINT.symbolic_inputs:
        assert item.consumers
        assert item.primary_owner_id.startswith("OWN-")
        assert item.authority_class in AuthorityClass
        assert item.deadline_gate
        assert item.status in Disposition
        assert not hasattr(item, "value")
        assert all(consumer in expected for consumer in item.consumers)
    assert expected["CM-034"] >= {
        "I-TELLER-INITIAL-PAUSE",
        "I-AAPL-TOKEN",
        "I-ASSET-CONFIG-STOCK",
    }


def test_symbolic_authority_class_mapping_is_exact_and_nonpromotional():
    expected = {
        "I-GREEN": AuthorityClass.DEPLOYMENT_PRODUCED,
        "I-GREEN-INITIAL-SUPPLY": AuthorityClass.OWNER_SELECTED,
        "I-GREEN-INITIAL-SUPPLY-RECIPIENT": AuthorityClass.OWNER_SELECTED,
        "I-RIPE": AuthorityClass.DEPLOYMENT_PRODUCED,
        "I-RIPE-INITIAL-SUPPLY": AuthorityClass.OWNER_SELECTED,
        "I-RIPE-INITIAL-SUPPLY-RECIPIENT": AuthorityClass.OWNER_SELECTED,
        "I-SGREEN": AuthorityClass.DEPLOYMENT_PRODUCED,
        "I-SGREEN-INITIAL-SUPPLY": AuthorityClass.OWNER_SELECTED,
        "I-SGREEN-INITIAL-SUPPLY-RECIPIENT": AuthorityClass.OWNER_SELECTED,
        "I-GOV-HANDOFF": AuthorityClass.OWNER_SELECTED,
        "I-CLOCK-PARAMS": AuthorityClass.REPOSITORY_APPROVED,
        "I-LEDGER-BLOCK-SOURCE": AuthorityClass.REPOSITORY_APPROVED,
        "I-LEDGER-DEFAULTS": AuthorityClass.REPOSITORY_APPROVED,
        "I-RH-DEFAULTS": AuthorityClass.REPOSITORY_APPROVED,
        "I-TRAINING-WHEELS": AuthorityClass.OWNER_SELECTED,
        "I-CHAINLINK-CORE": (
            AuthorityClass.EXTERNALLY_VERIFIABLE_CANONICAL_FACT
        ),
        "I-CHAINLINK-TIMELOCKS": AuthorityClass.OWNER_SELECTED,
        "I-AAPL-TOKEN": AuthorityClass.EXTERNALLY_VERIFIABLE_CANONICAL_FACT,
        "I-AAPL-FEED": AuthorityClass.EXTERNALLY_VERIFIABLE_CANONICAL_FACT,
        "I-AAPL-RISK": AuthorityClass.OWNER_SELECTED,
        "I-STOCK-VAULT-SLOT": AuthorityClass.OWNER_SELECTED,
        "I-TELLER-INITIAL-PAUSE": AuthorityClass.OWNER_SELECTED,
        "I-USDG": AuthorityClass.EXTERNALLY_VERIFIABLE_CANONICAL_FACT,
        "I-USDG-FEED": AuthorityClass.EXTERNALLY_VERIFIABLE_CANONICAL_FACT,
        "I-WETH": AuthorityClass.EXTERNALLY_VERIFIABLE_CANONICAL_FACT,
        "I-GREEN-USDG-LP": AuthorityClass.OWNER_SELECTED,
        "I-RIPE-WETH-LP": (
            AuthorityClass.EXTERNALLY_VERIFIABLE_CANONICAL_FACT
        ),
        "I-PSM-CONFIG": AuthorityClass.OWNER_SELECTED,
        "I-ECHO-TIMELOCKS": AuthorityClass.OWNER_SELECTED,
        "I-ASSET-CONFIG-NONSTOCK": AuthorityClass.OWNER_SELECTED,
        "I-ASSET-CONFIG-STOCK": AuthorityClass.OWNER_SELECTED,
        "I-STABILITY-CONFIG": AuthorityClass.OWNER_SELECTED,
        "I-RIPE-GOV-CONFIG": AuthorityClass.OWNER_SELECTED,
        "I-AUCTION-CREDIT-NONSTOCK": AuthorityClass.OWNER_SELECTED,
        "I-AUCTION-CREDIT-STOCK": AuthorityClass.OWNER_SELECTED,
        "I-ENDAOMENT-NATIVE-METADATA": (
            AuthorityClass.EXTERNALLY_VERIFIABLE_CANONICAL_FACT
        ),
        "I-LOOTBOX-CONFIG": AuthorityClass.OWNER_SELECTED,
        "I-REWARDS-PROMOTION": AuthorityClass.OWNER_SELECTED,
        "I-BOND-ROOM-CONFIG": AuthorityClass.OWNER_SELECTED,
        "I-BOND-BOOSTER-CONFIG": AuthorityClass.OWNER_SELECTED,
        "I-HR-TIMELOCKS": AuthorityClass.OWNER_SELECTED,
        "I-CCIP-ARTIFACTS": AuthorityClass.DEPLOYMENT_PRODUCED,
        "I-CCIP-REGISTRATION": AuthorityClass.OWNER_SELECTED,
        "I-MIGRATION-PLAN": AuthorityClass.DEPLOYMENT_PRODUCED,
        "I-VERIFY-EXPORT": AuthorityClass.DEPLOYMENT_PRODUCED,
        "I-RELEASE-PROOF": AuthorityClass.DEPLOYMENT_PRODUCED,
        "I-MANIFEST-HISTORY": AuthorityClass.REPOSITORY_APPROVED,
        "I-MORPHO-V2-FACTORY": (
            AuthorityClass.EXTERNALLY_VERIFIABLE_CANONICAL_FACT
        ),
        "I-CONTRIB-TEMPLATE": AuthorityClass.DEPLOYMENT_PRODUCED,
    }
    actual = {
        item.field_id: item.authority_class
        for item in ROBINHOOD_BLUEPRINT.symbolic_inputs
    }
    assert actual == expected
    assert Counter(actual.values()) == {
        AuthorityClass.REPOSITORY_APPROVED: 5,
        AuthorityClass.EXTERNALLY_VERIFIABLE_CANONICAL_FACT: 9,
        AuthorityClass.OWNER_SELECTED: 27,
        # 8 after I-STOCK-VAULT-ARTIFACT was removed with the retired
        # artifact-expectations pipeline.
        AuthorityClass.DEPLOYMENT_PRODUCED: 8,
    }
    for field_id in ("I-WETH", "I-USDG", "I-CHAINLINK-CORE"):
        item = get_symbolic_input(field_id)
        assert (
            item.authority_class
            is AuthorityClass.EXTERNALLY_VERIFIABLE_CANONICAL_FACT
        )
        assert item.status is Disposition.REQUIRED
        assert item.blocker_ids
        assert item.semantic_class.startswith("symbolic ")
        assert not hasattr(item, "value")
    assert (
        get_symbolic_input("I-LEDGER-BLOCK-SOURCE").authority_class
        is AuthorityClass.REPOSITORY_APPROVED
    )
    assert (
        get_symbolic_input("I-TELLER-INITIAL-PAUSE").authority_class
        is AuthorityClass.OWNER_SELECTED
    )


def test_lookup_api_returns_canonical_records_and_rejects_unknowns():
    assert get_component("CM-001") is ROBINHOOD_BLUEPRINT.components[0]
    assert get_symbolic_input("I-GREEN").field_id == "I-GREEN"
    assert get_blocker("B-S5-LEDGER").blocker_id == "B-S5-LEDGER"
    assert get_promotion("P-CCIP-SEVEN-DAY").promotion_id == (
        "P-CCIP-SEVEN-DAY"
    )
    for function, value, code in (
        (get_component, "CM-999", "H03_COMPONENT_SET"),
        (get_symbolic_input, "I-UNKNOWN", "H03_SYMBOLIC_FIELD"),
        (get_blocker, "B-UNKNOWN", "H03_BLOCKER"),
        (get_promotion, "P-UNKNOWN", "H03_PROMOTION_SET"),
    ):
        with pytest.raises(RobinhoodBlueprintError) as error:
            function(value)
        assert error.value.code == code


def test_all_28_remaining_blockers_are_open_and_morpho_gate_is_closed():
    expected_core = {
        "B-S5-LEDGER",
        "B-H04-PARAMS",
        "B-H05-PLAN",
        "B-T8-M1",
        "B-T8-M2",
        "B-T8-M3",
        "B-T8-M4",
        "B-T8-M5",
        "B-T8-FREEZE",
        "B-ORACLE-FREEZE",
        "B-P1-EXTERNAL-VERIFY",
        "B-LP-ARTIFACTS",
        "B-PSM-SEQUENCE",
        "B-REWARD-PROMOTION",
        "B-T1-CCIP",
        "B-T1-TOOLCHAIN",
        "B-H08-PROOF",
        "B-H09-RELEASE",
        "B-SECOPS-HANDOFF",
    }
    expected_curve = {
        "B-CURVE-"
        + row.input_id.removeprefix("curve.")
        .upper()
        .replace(".", "-")
        .replace("_", "-")
        for row in blueprint_source.ROBINHOOD_CURVE_LAUNCH_INPUTS
        if row.resolution_state
        in blueprint_source.ROBINHOOD_CURVE_BLOCKING_STATES
    }
    assert len(expected_curve) == 9
    blockers = {blocker.blocker_id: blocker for blocker in ROBINHOOD_BLUEPRINT.blockers}
    assert set(blockers) == expected_core | expected_curve
    assert "B-H02-AUDIT" not in blockers
    assert "B-P1-BLUECHIP-MORPHO-V2" not in blockers
    assert all(blocker.primary_owner_id for blocker in blockers.values())
    assert all(blocker.deadline_gate for blocker in blockers.values())
    ledger = blockers["B-S5-LEDGER"]
    assert "Integrated shared Ledger source" in ledger.summary
    assert "final constructor binding" in ledger.summary
    assert get_component("CM-008").deployment is Disposition.BLOCKED


def test_relations_are_explicit_typed_oriented_and_proved():
    relation_map = {
        relation.relation_id: (source, relation)
        for source, relation in all_relations()
    }
    assert set(relation_map) == {
        f"R-{value:03d}" for value in range(1, 297)
    }
    for source, relation in relation_map.values():
        assert source.startswith("CM-")
        assert relation.target_component_id.startswith("CM-")
        assert relation.source_proof_refs
        assert relation.evidence_authority_ids
        assert relation.basis
    assert relation_map["R-197"][0] == "CM-031"
    assert relation_map["R-197"][1].target_component_id == "CM-047"
    assert relation_map["R-197"][1].kind is RelationKind.DIRECT_EXECUTION
    assert relation_map["R-282"][0] == "CM-047"
    assert relation_map["R-282"][1].target_component_id == "CM-031"
    assert relation_map["R-282"][1].kind is RelationKind.AUTHORITY_DEPENDENCY
    assert not any(
        source == "CM-013" and relation.target_component_id == "CM-006"
        for source, relation in relation_map.values()
    )


def test_relation_mutations_fail_with_stable_diagnostic():
    assert_code(
        "H03_RELATION",
        replace_relation("R-282", target_component_id="CM-010"),
    )
    assert_code(
        "H03_RELATION",
        replace_relation("R-001", source_proof_refs=()),
    )
    assert_code(
        "H03_RELATION",
        replace_relation("R-001", phase=RelationPhase.RUNTIME_SECURITY),
    )
    assert_code(
        "H03_RELATION",
        replace_relation("R-001", target_component_id="CM-999"),
    )


def test_source_authority_is_exact_component_qualified_and_value_free():
    for component_id, source in all_paths():
        assert component_id.startswith("CM-")
        if source.path_kind is SourcePathKind.NONE:
            assert source.path is None
            assert source.path_state in {
                SourcePathState.ABSENT,
                SourcePathState.EXTERNAL_PENDING,
            }
        else:
            assert source.path
            assert not source.path.startswith("/")
            assert "*" not in source.path
    assert {
        source.path
        for source in get_component("CM-056").source_paths
        if source.path and source.path.startswith("migration_history/")
    } == {
        "migration_history/base-mainnet/v1",
        "migration_history/robinhood-mainnet/v1",
        "migration_history/robinhood-testnet/v1",
    }


def test_address_literals_and_base_values_never_enter_blueprint():
    source = MODULE.read_text()
    assert re.findall(r"(?i)0x[0-9a-f]{40}", source) == []

    blueprint_hash_before = hashlib.sha256(BASE_BLUEPRINT.read_bytes()).hexdigest()
    manifest_hash_before = hashlib.sha256(BASE_MANIFEST.read_bytes()).hexdigest()
    manifest = json.loads(BASE_MANIFEST.read_text())
    base_addresses = set()
    for values in (ADDYS, CORE_TOKENS, WHALES, YIELD_TOKENS):
        base_addresses.update(address_strings(values))
    base_addresses.update(address_strings(manifest))
    blueprint_strings = {
        value
        for value in (
            item
            for component in ROBINHOOD_BLUEPRINT.components
            for item in (
                component.name,
                *(
                    source.path or ""
                    for source in component.source_paths
                ),
            )
        )
        if isinstance(value, str)
    }
    assert base_addresses
    assert base_addresses.isdisjoint(blueprint_strings)

    zero = "0x" + ("0" * 40)
    candidate = replace(
        ROBINHOOD_BLUEPRINT,
        symbolic_inputs=(
            replace(
                ROBINHOOD_BLUEPRINT.symbolic_inputs[0],
                semantic_class=zero,
            ),
            *ROBINHOOD_BLUEPRINT.symbolic_inputs[1:],
        ),
    )
    assert_code("H03_ADDRESS_LITERAL", candidate)
    assert hashlib.sha256(BASE_BLUEPRINT.read_bytes()).hexdigest() == (
        blueprint_hash_before
    )
    assert hashlib.sha256(BASE_MANIFEST.read_bytes()).hexdigest() == (
        manifest_hash_before
    )


def test_exact_registry_topology_and_authority_classes():
    topology = {
        (item.domain, item.registry_id): item
        for item in all_registries()
    }
    assert [
        topology[(RegistryDomain.RIPE_HQ, value)].component_id
        for value in range(1, 25)
    ] == [
        "CM-001",
        "CM-003",
        "CM-002",
        "CM-008",
        "CM-009",
        "CM-010",
        "CM-015",
        "CM-021",
        "CM-026",
        "CM-027",
        "CM-028",
        "CM-029",
        "CM-030",
        "CM-031",
        "CM-032",
        "CM-033",
        "CM-034",
        "CM-044",
        "CM-043",
        "CM-045",
        "CM-047",
        "CM-048",
        "CM-052",
        "CM-051",
    ]
    assert all(
        topology[(RegistryDomain.RIPE_HQ, value)].authority
        is RegistryIdAuthority.SOURCE_HARD_CODED
        for value in range(1, 25)
    )
    assert {
        value: topology[(RegistryDomain.VAULT_BOOK, value)].semantic_name
        for value in range(1, 5)
    } == {
        1: "Stability Pool",
        2: "Ripe Gov Vault",
        3: "Simple ERC20 Vault",
        4: "Rebase ERC20 Vault",
    }
    assert {
        value: topology[(RegistryDomain.PRICE_DESK, value)].semantic_name
        for value in range(1, 3)
    } == {
        1: "Chainlink",
        2: "Curve",
    }
    assert {
        value: topology[(RegistryDomain.SWITCHBOARD, value)].semantic_name
        for value in range(1, 6)
    } == {
        1: "Switchboard Alpha",
        2: "Switchboard Bravo",
        3: "Switchboard Charlie",
        4: "Switchboard Delta",
        5: "Switchboard Echo",
    }
    assert not any(
        "Stock" in item.semantic_name
        for item in topology.values()
        if item.domain is RegistryDomain.VAULT_BOOK
    )


def test_blueprint_owns_complete_component_and_registry_censuses():
    assert len(blueprint_source.ROBINHOOD_COMPONENT_SELECTIONS) == 60
    assert tuple(
        row.component_id for row in blueprint_source.ROBINHOOD_COMPONENT_SELECTIONS
    ) == tuple(f"CM-{value:03d}" for value in range(1, 61))

    rows = blueprint_source.ROBINHOOD_REGISTRY_TOPOLOGY
    assert len(rows) == 35
    assert Counter(row.domain for row in rows) == {
        "ripe_hq": 24,
        "vault_book": 4,
        "price_desk": 2,
        "switchboard": 5,
    }
    price_rows = tuple(row for row in rows if row.domain == "price_desk")
    assert [row.registry_id for row in price_rows if row.selection_state == "selected"] == [1, 2]
    assert next(row for row in price_rows if row.registry_id == 2).component_id == "CM-017"


def test_non_price_desk_blueprint_registry_drift_fails_closed(monkeypatch):
    rows = blueprint_source.ROBINHOOD_REGISTRY_TOPOLOGY
    changed = tuple(
        replace(row, semantic_name="Unexpected Vault")
        if (row.domain, row.registry_id) == ("vault_book", 3)
        else row
        for row in rows
    )
    monkeypatch.setattr(blueprint_source, "ROBINHOOD_REGISTRY_TOPOLOGY", changed)
    with pytest.raises(RobinhoodBlueprintError) as error:
        validate_blueprint()
    assert error.value.code == "H03_REGISTRY_SOURCE_DRIFT"


def test_blueprint_component_disposition_drift_fails_closed(monkeypatch):
    rows = blueprint_source.ROBINHOOD_COMPONENT_SELECTIONS
    changed = tuple(
        replace(row, deployment_disposition="omitted", selection_state="omitted")
        if row.component_id == "CM-018"
        else row
        for row in rows
    )
    monkeypatch.setattr(blueprint_source, "ROBINHOOD_COMPONENT_SELECTIONS", changed)
    with pytest.raises(RobinhoodBlueprintError) as error:
        validate_blueprint()
    assert error.value.code == "H03_COMPONENT_SOURCE_DRIFT"


def test_curve_component_cannot_be_omitted(monkeypatch):
    rows = blueprint_source.ROBINHOOD_COMPONENT_SELECTIONS
    changed = tuple(
        replace(row, deployment_disposition="omitted", selection_state="omitted")
        if row.component_id == "CM-017"
        else row
        for row in rows
    )
    monkeypatch.setattr(blueprint_source, "ROBINHOOD_COMPONENT_SELECTIONS", changed)
    with pytest.raises(RobinhoodBlueprintError) as error:
        validate_blueprint()
    assert error.value.code == "H03_COMPONENT_SOURCE_DRIFT"


def test_curve_registration_source_id_cannot_move_from_two(monkeypatch):
    rows = list(blueprint_source.ROBINHOOD_REGISTRY_TOPOLOGY)
    curve_index = next(
        index
        for index, row in enumerate(rows)
        if (row.domain, row.registry_id) == ("price_desk", 2)
    )
    rows[curve_index] = replace(rows[curve_index], registry_id=3)
    monkeypatch.setattr(blueprint_source, "ROBINHOOD_REGISTRY_TOPOLOGY", tuple(rows))
    with pytest.raises(RobinhoodBlueprintError) as error:
        validate_blueprint()
    assert error.value.code == "H03_REGISTRY_SOURCE_CENSUS"


def _mutate_curve_input(monkeypatch, input_id, **changes):
    rows = tuple(
        replace(row, **changes) if row.input_id == input_id else row
        for row in blueprint_source.ROBINHOOD_CURVE_LAUNCH_INPUTS
    )
    monkeypatch.setattr(blueprint_source, "ROBINHOOD_CURVE_LAUNCH_INPUTS", rows)


@pytest.mark.parametrize(
    ("input_id", "changes", "code"),
    (
        ("launch.chain_id", {"value": 1}, "RH_CURVE_LAUNCH_TOPOLOGY"),
        ("curve.constructor_bindings", {"value": ()}, "RH_CURVE_CONSTRUCTOR_BINDINGS"),
        ("curve.address_provider", {"value": "0x1111111111111111111111111111111111111111"}, "RH_CURVE_ADDRESS_PROVIDER"),
        ("curve.address_provider_binding_12", {"value": (12, "StableSwapNG", "0x1111111111111111111111111111111111111111")}, "RH_CURVE_ADDRESS_PROVIDER"),
        ("pool.coin_order", {"value": ("GREEN", "USDG")}, "RH_CURVE_POOL_PARAMS"),
        ("pool.coin_decimals", {"value": (18, 6)}, "RH_CURVE_POOL_PARAMS"),
        ("pool.fee", {"value": 4}, "RH_CURVE_POOL_PARAMS"),
        ("pool.offpeg_fee_multiplier", {"value": 20}, "RH_CURVE_POOL_PARAMS"),
        ("pool.ma_exp_time", {"value": 600}, "RH_CURVE_POOL_PARAMS"),
        ("pool.address", {"value": "0x0000000000000000000000000000000000000000"}, "RH_CURVE_POOL_IDENTITY"),
        ("pool.factory_method", {"value": "unknown"}, "RH_CURVE_POOL_IDENTITY"),
        ("pool.factory_nonce_or_order", {"value": "precomputed"}, "RH_CURVE_POOL_IDENTITY"),
        ("pool.funding_source", {"value": 1}, "RH_CURVE_FUNDING_INPUT"),
        # A literal address here would bypass execution-time role resolution.
        ("pool.custodian", {"value": "0x" + "11" * 20}, "RH_CURVE_FUNDING_INPUT"),
        ("pool.approving_account", {"value": ""}, "RH_CURVE_FUNDING_INPUT"),
        ("pool.production_liquidity_amount", {"value": (0, 0)}, "RH_CURVE_FUNDING_INPUT"),
        ("pool.minimum_minted_lp", {"value": 0}, "RH_CURVE_FUNDING_INPUT"),
        (
            # Caught by the earlier metadata gate rather than the funding gate;
            # either way, un-resolving an approved value fails closed.
            "pool.minimum_minted_lp",
            {"resolution_state": "owner_choice_unresolved"},
            "RH_CURVE_INPUT_METADATA",
        ),
        ("pool.production_observation", {"value": 1}, "RH_CURVE_OBSERVATION"),
        ("feed.curve_assets", {"value": ("GREEN", "USDG")}, "RH_CURVE_RECURSION_GUARD"),
        ("feed.usdg_curve_feed", {"value": True}, "RH_CURVE_RECURSION_GUARD"),
        ("feed.route", {"value": ("GREEN", "manual constant")}, "RH_CURVE_RECURSION_GUARD"),
        ("inactive.capabilities", {"value": ()}, "RH_CURVE_BOUNDED_CAPABILITY"),
    ),
)
def test_curve_source_authority_mutations_fail_closed(
    monkeypatch, input_id, changes, code
):
    _mutate_curve_input(monkeypatch, input_id, **changes)
    with pytest.raises(RobinhoodBlueprintError) as error:
        validate_blueprint()
    assert error.value.code == code


def test_curve_external_identity_cannot_be_marked_verified_without_observation(monkeypatch):
    _mutate_curve_input(
        monkeypatch,
        "curve.address_provider",
        resolution_state="resolved_repository_fact",
    )
    with pytest.raises(RobinhoodBlueprintError) as error:
        validate_blueprint()
    assert error.value.code == "RH_CURVE_INPUT_METADATA"


def test_curve_official_address_candidate_drift_fails_closed(monkeypatch):
    monkeypatch.setitem(
        blueprint_source.ROBINHOOD_ADDRESSES,
        "CURVE_ADDRESS_PROVIDER",
        "0x1111111111111111111111111111111111111111",
    )
    with pytest.raises(RobinhoodBlueprintError) as error:
        validate_blueprint()
    assert error.value.code == "RH_CURVE_EXTERNAL_IDENTITY"


def test_curve_official_repository_candidates_are_exact():
    assert {
        "address_provider": blueprint_source.ROBINHOOD_CURVE_ADDRESS_PROVIDER,
        "meta_registry": blueprint_source.ROBINHOOD_CURVE_META_REGISTRY,
        "tricrypto_ng_factory": blueprint_source.ROBINHOOD_CURVE_TRICRYPTO_NG_FACTORY,
        "stableswap_ng_factory": blueprint_source.ROBINHOOD_CURVE_STABLESWAP_NG_FACTORY,
        "twocrypto_ng_factory": blueprint_source.ROBINHOOD_CURVE_TWOCRYPTO_NG_FACTORY,
    } == {
        "address_provider": "0x4574921eb950d3Fd5B01562162EC566Cb8bc3648",
        "meta_registry": "0xe6dA14500f0b5783E2325F9C5a7eE5d99DA0fB42",
        "tricrypto_ng_factory": "0x6E28493348446503db04A49621d8e6C9A40015FB",
        "stableswap_ng_factory": "0x8271e06E5887FE5ba05234f5315c19f3Ec90E8aD",
        "twocrypto_ng_factory": "0xe7FBd704B938cB8fe26313C3464D4b7B7348c88C",
    }


def test_curve_profile_view_cannot_drift_from_authority_rows(monkeypatch):
    monkeypatch.setitem(
        blueprint_source.CURVE_PARAMS["robinhood"], "GREEN_POOL_A", 200
    )
    with pytest.raises(RobinhoodBlueprintError) as error:
        validate_blueprint()
    assert error.value.code == "RH_CURVE_PROFILE_VIEW"


def test_curve_input_provenance_is_required(monkeypatch):
    _mutate_curve_input(monkeypatch, "pool.A", provenance="")
    with pytest.raises(RobinhoodBlueprintError) as error:
        validate_blueprint()
    assert error.value.code == "RH_CURVE_INPUT_SCHEMA"


@pytest.mark.parametrize(
    ("input_id", "changes"),
    (
        ("pool.address", {"provenance": "unknown deployment provenance"}),
        ("pool.address", {"authority_class": "repository_approved"}),
        ("pool.address", {"primary_owner": "oracle_owner"}),
        ("pool.A", {"provenance": "unrelated source"}),
        ("pool.A", {"resolution_state": "owner_choice_unresolved"}),
    ),
)
def test_curve_exact_metadata_substitution_fails_closed(
    monkeypatch, input_id, changes
):
    _mutate_curve_input(monkeypatch, input_id, **changes)
    with pytest.raises(RobinhoodBlueprintError) as error:
        validate_blueprint()
    assert error.value.code == "RH_CURVE_INPUT_METADATA"


def test_curve_metadata_census_substitution_fails_closed(monkeypatch):
    monkeypatch.setattr(
        blueprint_source,
        "ROBINHOOD_CURVE_LAUNCH_METADATA",
        blueprint_source.ROBINHOOD_CURVE_LAUNCH_METADATA[:-1],
    )
    with pytest.raises(RobinhoodBlueprintError) as error:
        validate_blueprint()
    assert error.value.code == "RH_CURVE_INPUT_METADATA"


@pytest.mark.parametrize("mutation", ("missing", "duplicate", "extra"))
def test_blueprint_registry_source_census_fails_closed(monkeypatch, mutation):
    rows = blueprint_source.ROBINHOOD_REGISTRY_TOPOLOGY
    if mutation == "missing":
        changed = rows[:-1]
    elif mutation == "duplicate":
        changed = (*rows[:-1], rows[0])
    else:
        changed = (
            *rows,
            replace(rows[-1], registry_id=6, semantic_name="Unexpected Extra"),
        )
    monkeypatch.setattr(blueprint_source, "ROBINHOOD_REGISTRY_TOPOLOGY", changed)
    with pytest.raises(RobinhoodBlueprintError) as error:
        validate_blueprint()
    assert error.value.code == "H03_REGISTRY_SOURCE_CENSUS"


def test_registry_shift_and_semantic_reuse_fail_closed():
    component = get_component("CM-018")
    assert component.registry_expectations == ()
    changed = RegistryExpectation(
        domain=RegistryDomain.PRICE_DESK,
        registry_id=3,
        semantic_name="BlueChipYield",
        authority=RegistryIdAuthority.REGISTRATION_ORDER,
        component_id="CM-018",
        disposition=Disposition.DEFERRED,
    )
    assert_code(
        "H03_REGISTRY_TOPOLOGY",
        replace_component(
            "CM-018",
            registry_expectations=(changed,),
        ),
    )
    live_row = get_component("CM-051").registry_expectations[0]
    assert_code(
        "H03_REGISTRY_TOPOLOGY",
        replace_component(
            "CM-051",
            registry_expectations=(
                replace(
                    live_row,
                    authority=RegistryIdAuthority.PROVISIONAL_RESERVATION,
                ),
            ),
        ),
    )


def test_ccip_promotion_record_matches_confirmed_live_state():
    ccip = get_promotion("P-CCIP-SEVEN-DAY")
    assert ccip.surface_ids == (
        "S-001-CCIP-CAP",
        "S-002-CCIP-CAP",
        "S-051-ARTIFACT",
        "S-052-ARTIFACT",
        "S-053-REGISTRATION",
        "S-058-TOOLCHAIN",
    )
    assert ROBINHOOD_BLUEPRINT.promotions == (ccip,)
    assert ccip.disposition is Disposition.REQUIRED
    assert ccip.promotion_phase is LifecyclePhase.DEPLOYED_INITIAL_VALUE
    assert not any(
        surface.lifecycle_phase
        is LifecyclePhase.WITHIN_SEVEN_DAY_SEPARATELY_REVIEWED_REWARD_ACTIVATION
        for surface in all_surfaces()
    )


def test_promotion_subset_fails_closed():
    (ccip,) = ROBINHOOD_BLUEPRINT.promotions
    assert_code(
        "H03_PROMOTION_SET",
        replace(
            ROBINHOOD_BLUEPRINT,
            promotions=(
                replace(ccip, surface_ids=ccip.surface_ids[:-1]),
            ),
        ),
    )


def test_component_surface_and_symbolic_mutations_have_stable_diagnostics():
    assert_code(
        "H03_COMPONENT_SET",
        replace(
            ROBINHOOD_BLUEPRINT,
            components=ROBINHOOD_BLUEPRINT.components[:-1],
        ),
    )
    first = ROBINHOOD_BLUEPRINT.symbolic_inputs[0]
    assert_code(
        "H03_SYMBOLIC_FIELD",
        replace(
            ROBINHOOD_BLUEPRINT,
            symbolic_inputs=(
                replace(first, consumers=()),
                *ROBINHOOD_BLUEPRINT.symbolic_inputs[1:],
            ),
        ),
    )
    component = get_component("CM-001")
    assert_code(
        "H03_SURFACE_SET",
        replace_component("CM-001", surfaces=component.surfaces[:-1]),
    )
    omitted = get_component("CM-007")
    injected = SurfaceRecord(
        "S-007-INJECTED",
        "CM-007",
        SurfaceKind.ARTIFACT,
        "synthetic omitted artifact",
        Disposition.REQUIRED,
        LifecyclePhase.DEPLOYED_INITIAL_VALUE,
        (),
        ("NEG-016",),
    )
    assert_code(
        "H03_OMISSION_SURFACE",
        replace_component("CM-007", surfaces=(injected,)),
    )
    assert omitted.surfaces == ()


def test_pure_import_and_validation_with_environment_absent():
    script = f"""
import builtins
import os
import socket
import subprocess
import sys

for name in (
    "BASESCAN_API_KEY", "ETHERSCAN_API_KEY", "WEB3_ALCHEMY_API_KEY",
    "BASE_MAINNET_RPC_URL", "BASE_SEPOLIA_RPC_URL",
    "ROBINHOOD_MAINNET_RPC_URL", "ROBINHOOD_TESTNET_RPC_URL",
    "DEPLOYER_PRIVATE_KEY", "TEST_PRIVATE_KEY",
):
    os.environ.pop(name, None)

events = []
real_getenv = os.getenv
real_popen = subprocess.Popen

def blocked_getenv(*args, **kwargs):
    events.append(("getenv", args))
    raise AssertionError("environment read")

def blocked_popen(*args, **kwargs):
    events.append(("popen", args))
    raise AssertionError("subprocess")

def blocked_socket(*args, **kwargs):
    events.append(("socket", args))
    raise AssertionError("socket")

os.getenv = blocked_getenv
subprocess.Popen = blocked_popen
socket.create_connection = blocked_socket

sys.path.insert(0, {str(ROOT)!r})
from config.robinhood_blueprint import validate_blueprint
validate_blueprint()
assert events == []
assert "boa" not in __import__("sys").modules
print("H03_IMPORT_PURE")
"""
    environment = {
        "PATH": os.defpath,
        "PYTHONPATH": str(ROOT),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    result = subprocess.run(
        [sys.executable, "-I", "-c", script],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "H03_IMPORT_PURE"


def test_module_static_import_surface_has_no_io_or_runtime_dependencies():
    tree = ast.parse(MODULE.read_text())
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(
                alias.name.split(".", 1)[0] for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
    assert imports.isdisjoint(
        {
            "boa",
            "socket",
            "subprocess",
            "pathlib",
            "os",
            "requests",
            "dotenv",
            "scripts",
        }
    )
    forbidden_calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"open", "exec", "eval", "compile"}
    }
    assert forbidden_calls == set()


def test_robinhood_blueprint_error_matches_runtime_boundary():
    assert issubclass(RobinhoodBlueprintError, RuntimeError)
    error = RobinhoodBlueprintError("H03_COMPONENT_SET", "CM-999")
    assert error.code == "H03_COMPONENT_SET"
    assert str(error) == "H03_COMPONENT_SET record=CM-999"


def test_module_contains_no_mutable_authority_literals():
    def walk(value):
        assert not isinstance(value, (list, dict, set))
        if is_dataclass(value):
            for field in fields(value):
                yield from walk(getattr(value, field.name))
        elif isinstance(value, tuple):
            for item in value:
                yield from walk(item)
        yield value

    assert tuple(walk(ROBINHOOD_BLUEPRINT))


def test_validation_is_deterministic_and_does_not_mutate_singleton():
    before = repr(ROBINHOOD_BLUEPRINT)
    validate_blueprint()
    validate_blueprint(ROBINHOOD_BLUEPRINT)
    assert repr(ROBINHOOD_BLUEPRINT) == before


def test_symbolic_authority_class_mutations_fail_closed():
    exact = {
        item.field_id: item.authority_class
        for item in ROBINHOOD_BLUEPRINT.symbolic_inputs
    }
    missing = dict(exact)
    missing.pop("I-GREEN")
    unknown = {**exact, "I-UNKNOWN": AuthorityClass.OWNER_SELECTED}
    incorrect = {**exact, "I-GREEN": AuthorityClass.OWNER_SELECTED}
    promotional = {
        **exact,
        "I-WETH": "externally_verified_canonical_fact",
    }

    for candidate in (missing, unknown, promotional):
        with pytest.raises(
            RobinhoodBlueprintError,
            match="H03_SYMBOLIC_FIELD",
        ):
            _validate_symbolic_authority_classes(candidate)

    _validate_symbolic_authority_classes(incorrect)
    incorrect_blueprint = replace(
        ROBINHOOD_BLUEPRINT,
        symbolic_inputs=tuple(
            replace(item, authority_class=incorrect[item.field_id])
            for item in ROBINHOOD_BLUEPRINT.symbolic_inputs
        ),
    )
    assert_code("H03_SYMBOLIC_FIELD", incorrect_blueprint)
