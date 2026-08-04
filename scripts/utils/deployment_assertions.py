"""Pure, deterministic deployment/topology assertions.

The structural blueprint supplies lifecycle policy and cross-checks registry
selection against config/BluePrint.py. Exact observed deployment facts must be
supplied by an owner-controlled expectations envelope.
Future fork tooling can collect observations and pass them here without adding
RPC behavior to this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Mapping, Sequence

from config.robinhood_blueprint import (
    ROBINHOOD_BLUEPRINT,
    Disposition,
    RegistryDomain,
    RegistryExpectation,
    RobinhoodBlueprint,
)


SCHEMA_VERSION = 1
ZERO_ADDRESS = "0x" + "0" * 40
REQUIRED_DISPOSITIONS = frozenset({Disposition.REQUIRED})
UNAVAILABLE_DISPOSITIONS = frozenset(
    {
        Disposition.OMITTED,
        Disposition.DISABLED,
        Disposition.DEFERRED,
        Disposition.BLOCKED,
    }
)
SUPPORTED_DISPOSITIONS = REQUIRED_DISPOSITIONS | UNAVAILABLE_DISPOSITIONS


class ObservationMode(str, Enum):
    SYNTHETIC = "synthetic"
    LOCAL_DEPLOYMENT = "local_deployment"
    DEPLOYED_OBSERVATION = "deployed_observation"


class DeploymentAssertionInputError(ValueError):
    """Raised when an assertion envelope is malformed or ambiguous."""


@dataclass(frozen=True, order=True)
class AssertionFailure:
    code: str
    path: str
    expected: str
    actual: str

    def to_mapping(self) -> Mapping[str, str]:
        return {
            "actual": self.actual,
            "code": self.code,
            "expected": self.expected,
            "path": self.path,
        }


@dataclass(frozen=True)
class AssertionReport:
    mode: ObservationMode
    profile_id: str
    failures: tuple[AssertionFailure, ...]

    @property
    def ok(self) -> bool:
        return not self.failures

    def to_mapping(self) -> Mapping[str, Any]:
        return {
            "failures": [failure.to_mapping() for failure in self.failures],
            "mode": self.mode.value,
            "ok": self.ok,
            "profile_id": self.profile_id,
            "schema_version": SCHEMA_VERSION,
        }


@dataclass(frozen=True)
class BlueprintPolicy:
    canonical_registries: Mapping[tuple[str, int], str]
    required_registries: frozenset[tuple[str, int]]
    reserved_registries: frozenset[tuple[str, int]]
    unavailable_components: Mapping[str, Disposition]


def blueprint_registry_map(
    blueprint: RobinhoodBlueprint = ROBINHOOD_BLUEPRINT,
) -> Mapping[tuple[RegistryDomain, int], RegistryExpectation]:
    """Return the one canonical registry derivation used by tests and checks."""
    registries: dict[tuple[RegistryDomain, int], RegistryExpectation] = {}
    for component in blueprint.components:
        for row in component.registry_expectations:
            key = (row.domain, row.registry_id)
            if key in registries:
                raise DeploymentAssertionInputError(
                    "blueprint has duplicate registry key: "
                    f"{row.domain.value}/{row.registry_id}"
                )
            registries[key] = row
    return registries


def blueprint_policy(
    blueprint: RobinhoodBlueprint = ROBINHOOD_BLUEPRINT,
) -> BlueprintPolicy:
    if SUPPORTED_DISPOSITIONS != frozenset(Disposition):
        unsupported = frozenset(Disposition) - SUPPORTED_DISPOSITIONS
        raise DeploymentAssertionInputError(
            "blueprint disposition policy is incomplete: "
            + ", ".join(sorted(value.value for value in unsupported))
        )

    canonical: dict[tuple[str, int], str] = {}
    required: set[tuple[str, int]] = set()
    reserved: set[tuple[str, int]] = set()
    unavailable_components: dict[str, Disposition] = {}
    for component in blueprint.components:
        if component.deployment in REQUIRED_DISPOSITIONS:
            continue
        if component.deployment in UNAVAILABLE_DISPOSITIONS:
            unavailable_components[component.component_id] = component.deployment
            continue
        raise DeploymentAssertionInputError(
            "blueprint component disposition is unsupported: "
            f"{component.deployment!r}"
        )

    for (domain, registry_id), row in blueprint_registry_map(blueprint).items():
        key = (domain.value, registry_id)
        canonical[key] = row.component_id
        if row.disposition in REQUIRED_DISPOSITIONS:
            required.add(key)
        elif row.disposition in UNAVAILABLE_DISPOSITIONS:
            reserved.add(key)
        else:  # Defensive even if a non-Enum value bypasses type construction.
            raise DeploymentAssertionInputError(
                "blueprint registry disposition is unsupported: "
                f"{row.disposition!r}"
            )

    return BlueprintPolicy(
        canonical_registries=canonical,
        required_registries=frozenset(required),
        reserved_registries=frozenset(reserved),
        unavailable_components=unavailable_components,
    )


def _require_mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise DeploymentAssertionInputError(f"{path} must be an object")
    return value


def _require_rows(value: Any, path: str) -> Sequence[Mapping[str, Any]]:
    if not isinstance(value, list):
        raise DeploymentAssertionInputError(f"{path} must be an array")
    return tuple(
        _require_mapping(row, f"{path}[{index}]")
        for index, row in enumerate(value)
    )


def _require_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise DeploymentAssertionInputError(f"{path} must be a nonempty string")
    return value


def _require_int(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise DeploymentAssertionInputError(f"{path} must be a positive integer")
    return value


def _require_bool(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        raise DeploymentAssertionInputError(f"{path} must be boolean")
    return value


def _require_string_fields(
    rows: Sequence[Mapping[str, Any]], fields: tuple[str, ...], *, path: str
) -> None:
    for index, row in enumerate(rows):
        for field in fields:
            _require_string(row.get(field), f"{path}[{index}].{field}")


def _require_identity_fields(
    rows: Sequence[Mapping[str, Any]], *, path: str
) -> None:
    for index, row in enumerate(rows):
        missing = [field for field in IDENTITY_FIELDS if field not in row]
        if missing:
            raise DeploymentAssertionInputError(
                f"{path}[{index}] is missing deployed identity field(s): "
                + ", ".join(missing)
            )


def _schema(value: Mapping[str, Any], path: str) -> None:
    if value.get("schema_version") != SCHEMA_VERSION:
        raise DeploymentAssertionInputError(
            f"{path}.schema_version must equal {SCHEMA_VERSION}"
        )


def _text(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _failure(
    failures: list[AssertionFailure],
    code: str,
    path: str,
    expected: Any,
    actual: Any,
) -> None:
    failures.append(
        AssertionFailure(
            code=code,
            path=path,
            expected=_text(expected),
            actual=_text(actual),
        )
    )


def _index_rows(
    rows: Sequence[Mapping[str, Any]],
    fields: tuple[str, ...],
    *,
    path: str,
    duplicate_code: str,
    failures: list[AssertionFailure],
) -> Mapping[tuple[Any, ...], Mapping[str, Any]]:
    indexed: dict[tuple[Any, ...], Mapping[str, Any]] = {}
    for index, row in enumerate(rows):
        key = tuple(row.get(field) for field in fields)
        if any(value is None for value in key):
            raise DeploymentAssertionInputError(
                f"{path}[{index}] is missing key field(s): {', '.join(fields)}"
            )
        if key in indexed:
            _failure(
                failures,
                duplicate_code,
                f"{path}[{index}]",
                "unique " + "/".join(fields),
                "/".join(map(str, key)),
            )
            continue
        indexed[key] = row
    return indexed


def _edge_key(row: Mapping[str, Any]) -> tuple[Any, Any, Any]:
    return (row.get("source"), row.get("target"), row.get("kind"))


IDENTITY_FIELDS = (
    "address",
    "proxy_type",
    "implementation",
    "runtime_sha256",
    "constructor_sha256",
    "artifact_sha256",
)
PLAN_COMPONENT_FIELDS = (
    "artifact",
    "constructor_refs",
    "activation_state",
)


def expectations_from_plan(plan_value: Mapping[str, Any]) -> Mapping[str, Any]:
    """Derive pre-collected observation expectations from an H-05 plan.

    This transformation is pure and retains source references rather than
    inventing deployment values.  A blocked plan can still produce reviewable
    expectations, but only a complete plan carries a non-null plan hash.
    """

    plan = _require_mapping(plan_value, "plan")
    profile = _require_mapping(plan.get("profile"), "plan.profile")
    stages = _require_rows(plan.get("stages"), "plan.stages")
    components: dict[str, Mapping[str, Any]] = {}
    registries: list[Mapping[str, Any]] = []
    actions: list[Mapping[str, Any]] = []
    for stage in stages:
        for action in _require_rows(stage.get("actions"), "plan.stages.actions"):
            actions.append(action)
            component_id = action.get("component_id")
            if action.get("kind") == "deployment":
                _require_string(component_id, "plan.action.component_id")
                authority = _require_mapping(
                    action.get("component_authority"),
                    "plan.action.component_authority",
                )
                selection_state = authority.get("selection_state")
                if selection_state not in {"selected", "blocked"}:
                    raise DeploymentAssertionInputError(
                        "plan deployment action has unavailable authority: "
                        f"{component_id}"
                    )
                if component_id in components:
                    raise DeploymentAssertionInputError(
                        f"plan has duplicate deployment component: {component_id}"
                    )
                postconditions = action.get("postconditions", [])
                disabled = any(
                    marker in str(condition)
                    for condition in postconditions
                    for marker in ("disabled", "inactive", "not-activated", "withheld", "paused")
                )
                components[component_id] = {
                    "component_id": component_id,
                    "artifact": _require_string(action.get("artifact"), "plan.action.artifact"),
                    "constructor_refs": list(action.get("constructor", [])),
                    "activation_state": "deployed-disabled" if disabled else "deployed",
                    "authority_selection_state": selection_state,
                }
            registry = action.get("registry")
            if action.get("kind") == "registration" and registry is not None:
                row = _require_mapping(registry, "plan.action.registry")
                selection_state = row.get("selection_state")
                if selection_state not in {"selected", "blocked"}:
                    raise DeploymentAssertionInputError(
                        "plan registration action has unavailable authority"
                    )
                registries.append(
                    {
                        "domain": _require_string(row.get("domain"), "plan.action.registry.domain"),
                        "registry_id": _require_int(row.get("registry_id"), "plan.action.registry.registry_id"),
                        "component_id": _require_string(row.get("component_id"), "plan.action.registry.component_id"),
                        "authority_selection_state": selection_state,
                    }
                )

    census = _require_mapping(plan.get("action_census"), "plan.action_census")
    action_ids = [
        _require_string(action.get("action_id"), "plan.action.action_id")
        for action in actions
    ]
    deployment_action_ids = [
        action["action_id"]
        for action in actions
        if action.get("kind") == "deployment"
    ]
    registration_action_ids = [
        action["action_id"]
        for action in actions
        if action.get("kind") == "registration"
    ]
    expected_census = {
        "total": 119,
        "deployments": 38,
        "registrations": 33,
        "all_action_ids": action_ids,
        "deployment_action_ids": deployment_action_ids,
        "registration_action_ids": registration_action_ids,
    }
    if dict(census) != expected_census:
        raise DeploymentAssertionInputError(
            "plan action census does not exactly account for 119/38/33 actions"
        )
    ledger = components.get("CM-008")
    if ledger is None or ledger.get("authority_selection_state") != "blocked":
        raise DeploymentAssertionInputError(
            "plan must retain CM-008 Ledger blocked disposition"
        )
    ledger_registries = [
        row for row in registries if row["component_id"] == "CM-008"
    ]
    if len(ledger_registries) != 1 or ledger_registries[0].get(
        "authority_selection_state"
    ) != "blocked":
        raise DeploymentAssertionInputError(
            "plan must retain CM-008 Ledger blocked registration"
        )
    artifact_kind = _require_string(
        _require_mapping(plan.get("artifact"), "plan.artifact").get("kind"),
        "plan.artifact.kind",
    )
    ledger_action = next(
        (
            action
            for action in actions
            if action.get("semantic_action_id") == "deploy-ledger"
        ),
        None,
    )
    ledger_blockers = set(
        ledger_action.get("blockers", []) if ledger_action else []
    )
    if not ledger_blockers or not ledger_blockers.issubset(
        set(plan.get("blockers", []))
    ):
        raise DeploymentAssertionInputError(
            "plan must preserve Ledger authority blockers"
        )
    if artifact_kind == "synthetic-proof":
        overrides = _require_rows(
            plan.get("synthetic_authority_overrides"),
            "plan.synthetic_authority_overrides",
        )
        overridden = {row.get("key") for row in overrides}
        if not ledger_blockers.issubset(overridden):
            raise DeploymentAssertionInputError(
                "synthetic proof must enumerate Ledger authority override"
            )

    actions_by_semantic_id: dict[str, Mapping[str, Any]] = {}
    for action in actions:
        semantic_id = _require_string(
            action.get("semantic_action_id"), "plan.action.semantic_action_id"
        )
        if semantic_id in actions_by_semantic_id:
            raise DeploymentAssertionInputError(
                f"plan has duplicate semantic action: {semantic_id}"
            )
        actions_by_semantic_id[semantic_id] = action

    def required_action(semantic_id: str) -> Mapping[str, Any]:
        action = actions_by_semantic_id.get(semantic_id)
        if action is None:
            raise DeploymentAssertionInputError(
                f"plan required action is missing: {semantic_id}"
            )
        return action

    curve_validation = required_action("validate-direct-green-pricing")
    curve_configuration = required_action(
        "configure-curve-green-feed-at-id-two"
    )
    curve_disable = required_action("recover-disable-curve-id-two")
    curve_recovery = required_action("recover-update-curve-id-two")
    aapl_seam = required_action("preserve-stock-extension-seam")
    reward_seam = required_action("preserve-reward-promotion-seam")
    lp_seam = required_action("preserve-lp-extension-seam")
    role_bindings = required_action("bind-governance-safe-guardian")
    operator_bindings = required_action(
        "bind-training-wheels-operator-signers"
    )
    capability_bindings = required_action("apply-approved-capabilities")
    psm_assertion = required_action("assert-psm-disabled-posture")
    handoff = actions[-1] if actions else {}
    if handoff.get("semantic_action_id") != "handoff-governance-and-relinquish-deployer":
        raise DeploymentAssertionInputError("plan final handoff action is missing or not last")
    coverage = _require_mapping(plan.get("component_coverage"), "plan.component_coverage")
    source = _require_mapping(plan.get("source"), "plan.source")
    plan_contract = {
        "artifact_kind": artifact_kind,
        "plan_hash": plan.get("plan_hash"),
        "proof_hash": plan.get("proof_hash"),
        "preview_hash": plan.get("preview_hash"),
        "source_digest": _require_string(source.get("source_digest"), "plan.source.source_digest"),
        "expectation_digest": _require_string(plan.get("expectation_digest"), "plan.expectation_digest"),
        "stage_ids": [
            _require_string(stage.get("migration_id"), "plan.stage.migration_id")
            for stage in stages
        ],
        "action_census": expected_census,
        "selected_components": sorted(list(coverage.get("selected", []))),
        "blocked_components": sorted(list(coverage.get("blocked", []))),
        "absent_components": sorted(
            list(coverage.get("omitted", [])) + list(coverage.get("deferred", []))
        ),
        "pricing_posture": {
            "price_desk_registrations": [
                [row["registry_id"], row["component_id"]]
                for row in sorted(
                    (
                        row
                        for row in registries
                        if row["domain"] == "price_desk"
                    ),
                    key=lambda row: row["registry_id"],
                )
            ],
            "priority_ids": [1, 3],
            "validation_postconditions": list(
                curve_validation.get("postconditions", [])
            ),
            "validation_abort_if": list(curve_validation.get("abort_if", [])),
            "feed_postconditions": list(
                curve_configuration.get("postconditions", [])
            ),
            "disable_operation": curve_disable.get("operation"),
            "disable_postconditions": list(
                curve_disable.get("postconditions", [])
            ),
            "recovery_operation": curve_recovery.get("operation"),
            "recovery_postconditions": list(
                curve_recovery.get("postconditions", [])
            ),
        },
        "aapl_posture": {
            "input_refs": list(aapl_seam.get("requires", [])),
            "postconditions": list(aapl_seam.get("postconditions", [])),
        },
        "reward_posture": {
            "input_refs": list(reward_seam.get("requires", [])),
            "postconditions": list(reward_seam.get("postconditions", [])),
        },
        "lp_posture": {
            "input_refs": list(lp_seam.get("requires", [])),
            "postconditions": list(lp_seam.get("postconditions", [])),
        },
        "role_posture": {
            "governance_safe_guardian_refs": list(
                role_bindings.get("requires", [])
            ),
            "training_wheels_operator_signer_refs": list(
                operator_bindings.get("requires", [])
            ),
        },
        "capability_posture": {
            "input_refs": list(capability_bindings.get("requires", [])),
            "postconditions": list(
                capability_bindings.get("postconditions", [])
            ),
        },
        "psm_posture": list(psm_assertion.get("postconditions", [])),
        "ccip_present": False,
        "uniswap_present": False,
        "final_authority": {
            "action_id": handoff.get("action_id"),
            "deployer_retains_authority": False,
            "is_final_action": True,
        },
    }
    expectations = {
        "schema_version": SCHEMA_VERSION,
        "profile_id": _require_string(profile.get("profile_id"), "plan.profile.profile_id"),
        "profile_kind": "profile1",
        "chain_id": _require_int(profile.get("expected_chain_id"), "plan.profile.expected_chain_id"),
        "registries": sorted(registries, key=lambda row: (row["domain"], row["registry_id"])),
        "components": [components[key] for key in sorted(components)],
        "capabilities": [],
        "forbidden_edges": [],
        "profile2_components": [],
        "configuration_sources": {
            "plan.authority": "config/BluePrint.py",
            "defaults.authority": "contracts/config/DefaultsRobinhood.vy",
        },
        "plan_contract": plan_contract,
    }
    identity = hashlib.sha256(
        json.dumps(
            expectations,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    plan_contract["output_identity"] = identity
    return expectations


def expectations_template() -> Mapping[str, Any]:
    """Return a versioned owner-expectations envelope shape for CLI users."""
    return {
        "schema_version": SCHEMA_VERSION,
        "profile_id": "<profile-id>",
        "profile_kind": "profile1",
        "chain_id": 1,
        "registries": [],
        "components": [
            {
                "component_id": "<component-id>",
                "address": "<address>",
                "proxy_type": "<proxy-type>",
                "implementation": "<implementation-address-or-null>",
                "runtime_sha256": "<sha256>",
                "constructor_sha256": "<sha256>",
                "artifact_sha256": "<sha256>",
            }
        ],
        "capabilities": [
            {
                "component_id": "<component-id>",
                "capability": "<capability>",
                "enabled": False,
            }
        ],
        "forbidden_edges": [
            {
                "source": "<component-id>",
                "target": "<component-id>",
                "kind": "<relation-kind>",
            }
        ],
        "profile2_components": [],
        "configuration_sources": {"<component.field>": "<profile-id>"},
    }


def observations_template(mode: ObservationMode) -> Mapping[str, Any]:
    """Return a versioned pre-collected observation envelope shape."""
    expected = expectations_template()
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": mode.value,
        "profile_id": expected["profile_id"],
        "chain_id": expected["chain_id"],
        "registries": expected["registries"],
        "components": expected["components"],
        "capabilities": expected["capabilities"],
        "edges": [],
        "configuration_sources": expected["configuration_sources"],
    }


def assert_deployment(
    expectations_value: Mapping[str, Any],
    observations_value: Mapping[str, Any],
    *,
    blueprint: RobinhoodBlueprint = ROBINHOOD_BLUEPRINT,
) -> AssertionReport:
    expectations = _require_mapping(expectations_value, "expectations")
    observations = _require_mapping(observations_value, "observations")
    _schema(expectations, "expectations")
    _schema(observations, "observations")

    try:
        mode = ObservationMode(observations.get("mode"))
    except (TypeError, ValueError) as exc:
        raise DeploymentAssertionInputError(
            "observations.mode is unsupported"
        ) from exc

    raw_plan_contract = expectations.get("plan_contract")
    synthetic_proof = (
        mode is ObservationMode.SYNTHETIC
        and isinstance(raw_plan_contract, Mapping)
        and raw_plan_contract.get("artifact_kind") == "synthetic-proof"
    )
    synthetic_blocked_registry_keys = {
        (row.get("domain"), row.get("registry_id"))
        for row in _require_rows(
            expectations.get("registries", []), "expectations.registries"
        )
        if row.get("authority_selection_state") == "blocked"
    }
    synthetic_blocked_components = {
        row.get("component_id")
        for row in _require_rows(
            expectations.get("components", []), "expectations.components"
        )
        if row.get("authority_selection_state") == "blocked"
    }

    expected_profile = _require_string(
        expectations.get("profile_id"), "expectations.profile_id"
    )
    observed_profile = _require_string(
        observations.get("profile_id"), "observations.profile_id"
    )
    profile_kind = _require_string(
        expectations.get("profile_kind"), "expectations.profile_kind"
    )
    if profile_kind not in {"profile1", "profile2"}:
        raise DeploymentAssertionInputError(
            "expectations.profile_kind must be profile1 or profile2"
        )
    expected_chain_id = _require_int(
        expectations.get("chain_id"), "expectations.chain_id"
    )
    observed_chain_id = _require_int(
        observations.get("chain_id"), "observations.chain_id"
    )

    failures: list[AssertionFailure] = []
    if observed_profile != expected_profile:
        _failure(
            failures,
            "PROFILE_ID_MISMATCH",
            "profile_id",
            expected_profile,
            observed_profile,
        )
    if observed_chain_id != expected_chain_id:
        _failure(
            failures,
            "CHAIN_ID_MISMATCH",
            "chain_id",
            expected_chain_id,
            observed_chain_id,
        )

    policy = blueprint_policy(blueprint)
    registry_rows = _require_rows(
        observations.get("registries", []), "observations.registries"
    )
    _require_string_fields(
        registry_rows,
        ("domain", "component_id"),
        path="observations.registries",
    )
    for index, row in enumerate(registry_rows):
        _require_int(
            row.get("registry_id"),
            f"observations.registries[{index}].registry_id",
        )
    observed_registries = _index_rows(
        registry_rows,
        ("domain", "registry_id"),
        path="registries",
        duplicate_code="DUPLICATE_REGISTRY_ID",
        failures=failures,
    )

    for key, row in sorted(observed_registries.items()):
        path = f"registries.{key[0]}.{key[1]}"
        canonical_component = policy.canonical_registries.get(key)
        if canonical_component is None:
            _failure(
                failures,
                "UNKNOWN_REGISTRY_ID",
                path,
                "canonical registry ID",
                row.get("component_id"),
            )
        elif row.get("component_id") != canonical_component:
            _failure(
                failures,
                "SHIFTED_REGISTRY_ID",
                path,
                canonical_component,
                row.get("component_id"),
            )

    enforce_registry = expectations.get("enforce_blueprint_registry", True)
    if enforce_registry is not True:
        raise DeploymentAssertionInputError(
            "blueprint registry enforcement is mandatory"
        )
    for domain, registry_id in sorted(policy.required_registries):
        key = (domain, registry_id)
        if key not in observed_registries:
            _failure(
                failures,
                "MISSING_REQUIRED_REGISTRY",
                f"registries.{domain}.{registry_id}",
                policy.canonical_registries[key],
                "missing",
            )
    for domain, registry_id in sorted(policy.reserved_registries):
        key = (domain, registry_id)
        if key in observed_registries:
            if synthetic_proof and key in synthetic_blocked_registry_keys:
                continue
            _failure(
                failures,
                "RESERVED_REGISTRY_REUSE",
                f"registries.{domain}.{registry_id}",
                "empty",
                observed_registries[key].get("component_id"),
            )

    expected_registry_rows = _require_rows(
        expectations.get("registries", []), "expectations.registries"
    )
    _require_string_fields(
        expected_registry_rows,
        ("domain", "component_id"),
        path="expectations.registries",
    )
    for index, row in enumerate(expected_registry_rows):
        _require_int(
            row.get("registry_id"),
            f"expectations.registries[{index}].registry_id",
        )
    expected_registries = _index_rows(
        expected_registry_rows,
        ("domain", "registry_id"),
        path="expected_registries",
        duplicate_code="DUPLICATE_EXPECTED_REGISTRY_ID",
        failures=failures,
    )
    for key, row in sorted(expected_registries.items()):
        if key in policy.reserved_registries:
            if synthetic_proof and key in synthetic_blocked_registry_keys:
                pass
            else:
                raise DeploymentAssertionInputError(
                    "expectations.registries cannot authorize reserved blueprint key: "
                    f"{key[0]}/{key[1]}"
                )
        observed = observed_registries.get(key)
        path = f"registries.{key[0]}.{key[1]}"
        if observed is None:
            _failure(
                failures,
                "MISSING_EXPECTED_REGISTRY",
                path,
                row.get("component_id"),
                "missing",
            )
        elif observed.get("component_id") != row.get("component_id"):
            _failure(
                failures,
                "REGISTRY_COMPONENT_MISMATCH",
                path,
                row.get("component_id"),
                observed.get("component_id"),
            )

    expected_component_rows = _require_rows(
        expectations.get("components", []), "expectations.components"
    )
    observed_component_rows = _require_rows(
        observations.get("components", []), "observations.components"
    )
    _require_string_fields(
        expected_component_rows, ("component_id",), path="expectations.components"
    )
    _require_string_fields(
        observed_component_rows, ("component_id",), path="observations.components"
    )
    if mode in {
        ObservationMode.LOCAL_DEPLOYMENT,
        ObservationMode.DEPLOYED_OBSERVATION,
    }:
        _require_identity_fields(
            expected_component_rows, path="expectations.components"
        )
        _require_identity_fields(
            observed_component_rows, path="observations.components"
        )

    expected_components = _index_rows(
        expected_component_rows,
        ("component_id",),
        path="expected_components",
        duplicate_code="DUPLICATE_EXPECTED_COMPONENT",
        failures=failures,
    )
    observed_components = _index_rows(
        observed_component_rows,
        ("component_id",),
        path="components",
        duplicate_code="DUPLICATE_OBSERVED_COMPONENT",
        failures=failures,
    )

    for (component_id,) in expected_components:
        disposition = policy.unavailable_components.get(component_id)
        if disposition is not None:
            if synthetic_proof and component_id in synthetic_blocked_components:
                continue
            raise DeploymentAssertionInputError(
                "expectations.components cannot authorize "
                f"{disposition.value} blueprint component: {component_id}"
            )

    for (component_id,), row in sorted(observed_components.items()):
        disposition = policy.unavailable_components.get(component_id)
        if disposition is not None:
            if synthetic_proof and component_id in synthetic_blocked_components:
                continue
            _failure(
                failures,
                f"{disposition.value.upper()}_COMPONENT_PRESENT",
                f"components.{component_id}",
                "absent",
                row.get("address", "present"),
            )
        address = row.get("address")
        if address is not None and not isinstance(address, str):
            raise DeploymentAssertionInputError(
                f"observations.components.{component_id}.address must be a string"
            )
        if address in {"", ZERO_ADDRESS}:
            _failure(
                failures,
                "INVALID_COMPONENT_ADDRESS",
                f"components.{component_id}.address",
                "nonzero address",
                address,
            )

    for (component_id,), expected in sorted(expected_components.items()):
        observed = observed_components.get((component_id,))
        if observed is None:
            _failure(
                failures,
                "MISSING_COMPONENT",
                f"components.{component_id}",
                "present",
                "missing",
            )
            continue
        for field in IDENTITY_FIELDS:
            if field not in expected:
                continue
            if observed.get(field) != expected.get(field):
                _failure(
                    failures,
                    f"{field.upper()}_MISMATCH",
                    f"components.{component_id}.{field}",
                    expected.get(field),
                    observed.get(field),
                )
        for field in PLAN_COMPONENT_FIELDS:
            if field not in expected:
                continue
            if observed.get(field) != expected.get(field):
                _failure(
                    failures,
                    f"{field.upper()}_MISMATCH",
                    f"components.{component_id}.{field}",
                    expected.get(field),
                    observed.get(field),
                )

    expected_capability_rows = _require_rows(
        expectations.get("capabilities", []), "expectations.capabilities"
    )
    observed_capability_rows = _require_rows(
        observations.get("capabilities", []), "observations.capabilities"
    )
    _require_string_fields(
        expected_capability_rows,
        ("component_id", "capability"),
        path="expectations.capabilities",
    )
    _require_string_fields(
        observed_capability_rows,
        ("component_id", "capability"),
        path="observations.capabilities",
    )
    for path, rows in (
        ("expectations.capabilities", expected_capability_rows),
        ("observations.capabilities", observed_capability_rows),
    ):
        for index, row in enumerate(rows):
            _require_bool(row.get("enabled"), f"{path}[{index}].enabled")

    expected_capabilities = _index_rows(
        expected_capability_rows,
        ("component_id", "capability"),
        path="expected_capabilities",
        duplicate_code="DUPLICATE_EXPECTED_CAPABILITY",
        failures=failures,
    )
    observed_capabilities = _index_rows(
        observed_capability_rows,
        ("component_id", "capability"),
        path="capabilities",
        duplicate_code="DUPLICATE_OBSERVED_CAPABILITY",
        failures=failures,
    )
    for key in sorted(set(expected_capabilities) | set(observed_capabilities)):
        expected = expected_capabilities.get(key)
        observed = observed_capabilities.get(key)
        path = f"capabilities.{key[0]}.{key[1]}"
        if expected is None:
            _failure(
                failures,
                "UNEXPECTED_CAPABILITY",
                path,
                "absent",
                observed.get("enabled"),
            )
        elif observed is None:
            _failure(
                failures,
                "MISSING_CAPABILITY",
                path,
                expected.get("enabled"),
                "missing",
            )
        elif observed.get("enabled") != expected.get("enabled"):
            _failure(
                failures,
                "CAPABILITY_MEMBERSHIP_MISMATCH",
                path,
                expected.get("enabled"),
                observed.get("enabled"),
            )

    observed_edges = _require_rows(observations.get("edges", []), "observations.edges")
    _require_string_fields(
        observed_edges,
        ("source", "target", "kind"),
        path="observations.edges",
    )
    observed_edge_map = _index_rows(
        observed_edges,
        ("source", "target", "kind"),
        path="edges",
        duplicate_code="DUPLICATE_TOPOLOGY_EDGE",
        failures=failures,
    )
    edge_keys = set(observed_edge_map)

    for edge in observed_edges:
        source, target, kind = _edge_key(edge)
        for component_id in {source, target}:
            disposition = policy.unavailable_components.get(component_id)
            if disposition is not None:
                _failure(
                    failures,
                    f"{disposition.value.upper()}_COMPONENT_REACHABLE",
                    f"edges.{source}.{target}.{kind}",
                    f"no edge to {disposition.value} component",
                    "reachable",
                )

    forbidden_edge_rows = _require_rows(
        expectations.get("forbidden_edges", []),
        "expectations.forbidden_edges",
    )
    _require_string_fields(
        forbidden_edge_rows,
        ("source", "target", "kind"),
        path="expectations.forbidden_edges",
    )
    forbidden_edges = set(
        _index_rows(
            forbidden_edge_rows,
            ("source", "target", "kind"),
            path="forbidden_edges",
            duplicate_code="DUPLICATE_FORBIDDEN_EDGE",
            failures=failures,
        )
    )
    for edge in sorted(
        edge_keys & forbidden_edges,
        key=lambda value: tuple(map(str, value)),
    ):
        _failure(
            failures,
            "DISABLED_FUNCTIONALITY_REACHABLE",
            f"edges.{edge[0]}.{edge[1]}.{edge[2]}",
            "absent",
            "reachable",
        )

    if profile_kind == "profile1":
        profile2_components = expectations.get("profile2_components", [])
        if not isinstance(profile2_components, list):
            raise DeploymentAssertionInputError(
                "expectations.profile2_components must be an array"
            )
        if not all(
            isinstance(value, str) and value for value in profile2_components
        ):
            raise DeploymentAssertionInputError(
                "expectations.profile2_components must contain nonempty strings"
            )
        prohibited = set(profile2_components)
        reachable = {
            component_id
            for edge in observed_edges
            for component_id in (edge.get("source"), edge.get("target"))
        } | {key[0] for key in observed_components}
        for component_id in sorted(prohibited & reachable):
            _failure(
                failures,
                "PROFILE2_REACHABLE_FROM_PROFILE1",
                f"profile2_components.{component_id}",
                "unreachable",
                "reachable",
            )

    expected_sources = _require_mapping(
        expectations.get("configuration_sources", {}),
        "expectations.configuration_sources",
    )
    observed_sources = _require_mapping(
        observations.get("configuration_sources", {}),
        "observations.configuration_sources",
    )
    for path, sources in (
        ("expectations.configuration_sources", expected_sources),
        ("observations.configuration_sources", observed_sources),
    ):
        for field, source in sources.items():
            _require_string(field, f"{path}.key")
            _require_string(source, f"{path}.{field}")

    for field in sorted(set(expected_sources) | set(observed_sources)):
        expected_source = expected_sources.get(field)
        actual_source = observed_sources.get(field)
        if expected_source is None:
            _failure(
                failures,
                "UNEXPECTED_CONFIGURATION_SOURCE",
                f"configuration_sources.{field}",
                "absent",
                actual_source,
            )
        elif actual_source != expected_source:
            _failure(
                failures,
                "CONFIGURATION_SOURCE_MISMATCH",
                f"configuration_sources.{field}",
                expected_source,
                actual_source if actual_source is not None else "missing",
            )
        if str(field).startswith("Deleverage.") and str(actual_source).startswith(
            "base-"
        ):
            _failure(
                failures,
                "DELEVERAGE_BASE_CONFIG_REUSE",
                f"configuration_sources.{field}",
                expected_profile,
                actual_source,
            )

    expected_plan_contract = expectations.get("plan_contract")
    observed_plan_contract = observations.get("plan_contract")
    if expected_plan_contract is not None or observed_plan_contract is not None:
        expected_plan_contract = _require_mapping(
            expected_plan_contract, "expectations.plan_contract"
        )
        observed_plan_contract = _require_mapping(
            observed_plan_contract, "observations.plan_contract"
        )
        if expected_plan_contract != observed_plan_contract:
            _failure(
                failures,
                "PLAN_EXPECTATION_MISMATCH",
                "plan_contract",
                json.dumps(expected_plan_contract, sort_keys=True),
                json.dumps(observed_plan_contract, sort_keys=True),
            )

    return AssertionReport(
        mode=mode,
        profile_id=observed_profile,
        failures=tuple(sorted(set(failures))),
    )
