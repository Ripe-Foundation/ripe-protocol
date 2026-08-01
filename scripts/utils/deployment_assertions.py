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
            raise DeploymentAssertionInputError(
                "expectations.components cannot authorize "
                f"{disposition.value} blueprint component: {component_id}"
            )

    for (component_id,), row in sorted(observed_components.items()):
        disposition = policy.unavailable_components.get(component_id)
        if disposition is not None:
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

    return AssertionReport(
        mode=mode,
        profile_id=observed_profile,
        failures=tuple(sorted(set(failures))),
    )
