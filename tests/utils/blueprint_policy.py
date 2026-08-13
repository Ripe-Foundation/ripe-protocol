"""Registry topology and disposition-policy views over ROBINHOOD_BLUEPRINT.

Extracted from the retired deployment_assertions.py checker: the blueprint's
own test suite (tests/deployment/test_robinhood_omissions.py) needs a
canonical registry-slot lookup and an aggregated required/reserved-registry
view to prove the blueprint fails closed, but none of the checker's
observation/assertion-envelope machinery that module also carried.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from config.robinhood_blueprint import (
    ROBINHOOD_BLUEPRINT,
    Disposition,
    RegistryDomain,
    RegistryExpectation,
    RobinhoodBlueprint,
)

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


class BlueprintPolicyError(ValueError):
    """Raised when the blueprint's disposition policy is malformed."""


@dataclass(frozen=True)
class BlueprintPolicy:
    canonical_registries: Mapping[tuple[str, int], str]
    required_registries: frozenset[tuple[str, int]]
    reserved_registries: frozenset[tuple[str, int]]
    required_components: frozenset[str]
    unavailable_components: Mapping[str, Disposition]


def blueprint_registry_map(
    blueprint: RobinhoodBlueprint = ROBINHOOD_BLUEPRINT,
) -> Mapping[tuple[RegistryDomain, int], RegistryExpectation]:
    """Return the one canonical registry derivation used by the blueprint's tests."""
    registries: dict[tuple[RegistryDomain, int], RegistryExpectation] = {}
    for component in blueprint.components:
        for row in component.registry_expectations:
            key = (row.domain, row.registry_id)
            if key in registries:
                raise BlueprintPolicyError(
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
        raise BlueprintPolicyError(
            "blueprint disposition policy is incomplete: "
            + ", ".join(sorted(value.value for value in unsupported))
        )

    required_components: set[str] = set()
    unavailable_components: dict[str, Disposition] = {}
    for component in blueprint.components:
        if component.deployment in REQUIRED_DISPOSITIONS:
            required_components.add(component.component_id)
            continue
        if component.deployment in UNAVAILABLE_DISPOSITIONS:
            unavailable_components[component.component_id] = component.deployment
            continue
        raise BlueprintPolicyError(
            "blueprint component disposition is unsupported: "
            f"{component.deployment!r}"
        )

    canonical: dict[tuple[str, int], str] = {}
    required: set[tuple[str, int]] = set()
    reserved: set[tuple[str, int]] = set()
    for (domain, registry_id), row in blueprint_registry_map(blueprint).items():
        key = (domain.value, registry_id)
        canonical[key] = row.component_id
        if row.disposition in REQUIRED_DISPOSITIONS:
            required.add(key)
        elif row.disposition in UNAVAILABLE_DISPOSITIONS:
            reserved.add(key)
        else:  # Defensive even if a non-Enum value bypasses type construction.
            raise BlueprintPolicyError(
                "blueprint registry disposition is unsupported: "
                f"{row.disposition!r}"
            )

    return BlueprintPolicy(
        canonical_registries=canonical,
        required_registries=frozenset(required),
        reserved_registries=frozenset(reserved),
        required_components=frozenset(required_components),
        unavailable_components=unavailable_components,
    )
