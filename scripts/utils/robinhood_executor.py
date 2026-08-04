"""Fail-closed execution engine for the shared Robinhood migration source.

This module is imported only after the static H-05 plan boundary.  It owns no
RPC or account discovery.  A caller must supply a validated production plan,
an explicit backend, and (when durable history is desired) a private H-06
history directory.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Callable, Mapping, Protocol, Sequence

from config import BluePrint as source_blueprint
from scripts.utils.manifest_schema import (
    FINALITY_POLICY_ID,
    HistoryState,
    ManifestError,
    WriteResult,
    immutable_basename,
    plan_action_sha256,
    plan_sha256,
    promote_current_index,
    publish_immutable,
    read_history,
    seal_artifact,
    source_set_sha256,
    validate_execution_handoff,
    validate_semantic_plan,
)
from scripts.utils.migration_runner import (
    MigrationPlanError,
    canonical_jcs_bytes,
    validate_execution_plan_artifact,
)


EXPECTED_STAGE_IDS = (
    "0010", "0020", "0030", "0040", "0050", "0060", "0070", "0080",
    "0100", "0200", "0300", "0400", "0500", "0600", "0700", "0800",
    "0900",
)
EXPECTED_OPERATION_VOCABULARY = frozenset(
    {
        "add-and-confirm-chainlink-feed",
        "add-and-confirm-curve-feed-after-id-two",
        "apply-defaults-asset-configs",
        "apply-exact-capability-set",
        "assert-action-absent",
        "assert-action-family-absent",
        "assert-artifact-capacity",
        "assert-atomic-aapl-qualification-remains-blocked",
        "assert-authority-boundary",
        "assert-complete-launch-state",
        "assert-component-and-registry-absent",
        "assert-constructor-provenance",
        "assert-constructor-registration",
        "assert-deployed-disabled",
        "assert-direct-price",
        "assert-disabled-scaffold",
        "assert-feature-disabled",
        "assert-feature-family-absent",
        "assert-input-prefix",
        "assert-lifecycle-separation",
        "assert-migration-absent",
        "assert-offline-report-interface",
        "assert-pool-runtime",
        "assert-registry-sequence",
        "assert-selection-state-absent",
        "assert-source-invariant",
        "assert-state-import-absent",
        "assert-topology-authority",
        "assert-typed-input",
        "bind-approved-preexisting-or-produced-address",
        "bind-approved-product-packet-and-operational-gates",
        "bind-role-identities",
        "bind-selected-tooling-component",
        "create-or-bind-pool",
        "declare-extension-seam",
        "declare-future-owner-action",
        "deploy",
        "deploy-blueprint",
        "finalize-timelocks",
        "finish-token-setup",
        "irreversible-final-authority-handoff",
        "pause-then-timelocked-disable-registry-address",
        "register-and-confirm",
        "seed-pool-and-transfer-lp",
        "set-auto-deposit-disabled",
        "set-priority-price-source-ids",
        "timelocked-update-registry-address",
        "validate-external-identities",
    }
)
EXPECTED_NAMESPACE_COUNTS = {
    "action": 7,
    "address": 144,
    "binding": 59,
    "blueprint": 6,
    "curve": 45,
    "curve-binding": 2,
    "defaults": 7,
    "input": 72,
    "input-prefix": 2,
    "registry": 36,
    "stock": 16,
}
_CURVE_CONSTRUCTOR_VALUE_BINDINGS = {
    "_minPriceChangeTimeLock": (
        "Defaults:price source minimum",
        "PRICE_DESK_MIN_REG_TIMELOCK",
    ),
    "_maxPriceChangeTimeLock": (
        "Defaults:price source maximum",
        "PRICE_DESK_MAX_REG_TIMELOCK",
    ),
}
NON_EXECUTING_KINDS = frozenset(
    {"omission", "blocked", "deferred", "recovery", "tooling-only"}
)
_ADDRESS = re.compile(r"0x[0-9a-fA-F]{40}")
# Defined here rather than imported from robinhood_backends: that module imports
# from this one, so the dependency only runs one way.
ZERO_ADDRESS = "0x" + "0" * 40


class RobinhoodExecutionError(RuntimeError):
    """Stable, sanitized execution failure."""

    def __init__(self, code: str, *, action_id: str | None = None) -> None:
        if re.fullmatch(r"RHX_[A-Z0-9_]+", code) is None:
            raise ValueError("invalid Robinhood execution error code")
        self.code = code
        self.action_id = action_id
        label = code if action_id is None else f"{code} action={action_id}"
        super().__init__(label)


class RobinhoodBackendFailure(RobinhoodExecutionError):
    """Sanitized backend failure carrying already-observed local evidence."""

    def __init__(
        self,
        code: str,
        *,
        action_id: str,
        outcome: "BackendOutcome",
    ) -> None:
        super().__init__(code, action_id=action_id)
        self.outcome = outcome


class BindingProvenance(str, Enum):
    BLUEPRINT = "blueprint-authority"
    DEFAULTS = "defaults-authority"
    DERIVED = "derived-validation"
    ENVELOPE = "accepted-envelope"
    ACTION = "validated-action-result"
    DEPLOYMENT = "same-execution-deployment"


@dataclass(frozen=True, slots=True)
class BoundValue:
    reference: str
    value: Any
    provenance: BindingProvenance


@dataclass(frozen=True, slots=True)
class AssertionResult:
    assertion_id: str
    matched: bool
    evidence_sha256: str


@dataclass(frozen=True, slots=True)
class ArtifactIdentity:
    source_path: str
    source_sha256: str
    runtime_sha256: str | None


@dataclass(frozen=True, slots=True)
class AuthorityRelinquishment:
    contract_reference: str
    contract_address: str
    sequence: int
    status: str
    transaction_identity: str | None
    temporary_governance_before: str
    local_governance_after: str
    ripe_hq_governance_after: str
    temporary_can_govern_after: bool
    final_can_govern_after: bool
    failure_classification: str | None = None


@dataclass(frozen=True, slots=True)
class BackendOutcome:
    execution_identity: str | None = None
    outputs: Mapping[str, Any] | None = None
    deployed_address: str | None = None
    artifact: ArtifactIdentity | None = None
    registry_id: int | None = None
    assertions: tuple[AssertionResult, ...] = ()
    block_number: int | None = None
    block_hash: str | None = None
    authority_relinquishments: tuple[AuthorityRelinquishment, ...] = ()
    retained_temporary_governance: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class OperationContract:
    operation: str
    kinds: frozenset[str]
    input_namespaces: frozenset[str]
    output_namespaces: frozenset[str]
    transactional: bool
    preconditions: tuple[str, ...]
    failure_classifications: tuple[str, ...]
    postcondition_policy: str


class RobinhoodBackend(Protocol):
    execution_sender: str

    def restore_completed_action(
        self,
        plan: Mapping[str, Any],
        action: Mapping[str, Any],
        evidence: Mapping[str, Any],
    ) -> None: ...

    def restore_failed_action(
        self,
        plan: Mapping[str, Any],
        action: Mapping[str, Any],
        evidence: Mapping[str, Any],
    ) -> None: ...

    def resolve_derived(self, reference: str) -> Any: ...

    def deploy(self, context: "ActionContext") -> BackendOutcome: ...
    def register_and_confirm(self, context: "ActionContext") -> BackendOutcome: ...
    def assert_constructor_registration(self, context: "ActionContext") -> BackendOutcome: ...
    def add_and_confirm_chainlink_feed(self, context: "ActionContext") -> BackendOutcome: ...
    def validate_external_identities(self, context: "ActionContext") -> BackendOutcome: ...
    def create_or_bind_pool(self, context: "ActionContext") -> BackendOutcome: ...
    def seed_pool_and_transfer_lp(self, context: "ActionContext") -> BackendOutcome: ...
    def assert_pool_runtime(self, context: "ActionContext") -> BackendOutcome: ...
    def assert_direct_price(self, context: "ActionContext") -> BackendOutcome: ...
    def add_and_confirm_curve_feed_after_id_two(self, context: "ActionContext") -> BackendOutcome: ...
    def set_priority_price_source_ids(self, context: "ActionContext") -> BackendOutcome: ...
    def assert_registry_sequence(self, context: "ActionContext") -> BackendOutcome: ...
    def apply_defaults_asset_configs(self, context: "ActionContext") -> BackendOutcome: ...
    def finish_token_setup(self, context: "ActionContext") -> BackendOutcome: ...
    def set_auto_deposit_disabled(self, context: "ActionContext") -> BackendOutcome: ...
    def apply_exact_capability_set(self, context: "ActionContext") -> BackendOutcome: ...
    def finalize_timelocks(self, context: "ActionContext") -> BackendOutcome: ...
    def irreversible_final_authority_handoff(self, context: "ActionContext") -> BackendOutcome: ...
    def bind_value(self, context: "ActionContext") -> BackendOutcome: ...
    def assert_condition(self, context: "ActionContext") -> BackendOutcome: ...
    def non_executing(self, context: "ActionContext") -> BackendOutcome: ...


@dataclass(frozen=True, slots=True)
class ActionContext:
    plan: Mapping[str, Any]
    semantic_plan: Mapping[str, Any]
    stage: Mapping[str, Any]
    action: Mapping[str, Any]
    inputs: tuple[BoundValue, ...]
    backend: RobinhoodBackend
    repository_root: Path

    def value(self, reference: str) -> Any:
        for item in self.inputs:
            if item.reference == reference:
                return item.value
        raise RobinhoodExecutionError(
            "RHX_BINDING_MISSING", action_id=self.action["action_id"]
        )


Handler = Callable[[ActionContext], BackendOutcome]


class HandlerRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, tuple[OperationContract, Handler]] = {}

    def register(
        self, contract: OperationContract, handler: Handler
    ) -> None:
        if contract.operation in self._handlers:
            raise RobinhoodExecutionError("RHX_HANDLER_DUPLICATE")
        self._handlers[contract.operation] = (contract, handler)

    def validate_vocabulary(self, operations: set[str]) -> None:
        if operations != EXPECTED_OPERATION_VOCABULARY:
            raise RobinhoodExecutionError("RHX_OPERATION_CENSUS_DRIFT")
        registered = set(self._handlers)
        if operations - registered:
            raise RobinhoodExecutionError("RHX_HANDLER_MISSING")
        if registered - operations:
            raise RobinhoodExecutionError("RHX_HANDLER_UNSUPPORTED")

    def get(self, operation: str) -> tuple[OperationContract, Handler]:
        try:
            return self._handlers[operation]
        except KeyError as error:
            raise RobinhoodExecutionError("RHX_OPERATION_UNKNOWN") from error

    @property
    def operations(self) -> frozenset[str]:
        return frozenset(self._handlers)


def _contract(
    operation: str,
    kinds: str | Sequence[str],
    inputs: str = "",
    outputs: str = "",
    *,
    transactional: bool = False,
    postcondition_policy: str = "exact-source-postconditions",
) -> OperationContract:
    kind_values = (kinds,) if isinstance(kinds, str) else tuple(kinds)
    return OperationContract(
        operation=operation,
        kinds=frozenset(kind_values),
        input_namespaces=frozenset(filter(None, inputs.split(","))),
        output_namespaces=frozenset(filter(None, outputs.split(","))),
        transactional=transactional,
        preconditions=("validated-production-plan", "resolved-typed-inputs"),
        failure_classifications=(
            "precondition-failed",
            "submission-failed",
            "postcondition-failed",
        ),
        postcondition_policy=postcondition_policy,
    )


def _deploy(context: ActionContext) -> BackendOutcome:
    return context.backend.deploy(context)


def _register(context: ActionContext) -> BackendOutcome:
    return context.backend.register_and_confirm(context)


def _constructor_registration(context: ActionContext) -> BackendOutcome:
    return context.backend.assert_constructor_registration(context)


def _chainlink(context: ActionContext) -> BackendOutcome:
    return context.backend.add_and_confirm_chainlink_feed(context)


def _external_identities(context: ActionContext) -> BackendOutcome:
    return context.backend.validate_external_identities(context)


def _pool(context: ActionContext) -> BackendOutcome:
    return context.backend.create_or_bind_pool(context)


def _pool_assertion(context: ActionContext) -> BackendOutcome:
    return context.backend.assert_pool_runtime(context)


def _seed_pool(context: ActionContext) -> BackendOutcome:
    return context.backend.seed_pool_and_transfer_lp(context)


def _direct_price(context: ActionContext) -> BackendOutcome:
    return context.backend.assert_direct_price(context)


def _curve_feed(context: ActionContext) -> BackendOutcome:
    return context.backend.add_and_confirm_curve_feed_after_id_two(context)


def _priority(context: ActionContext) -> BackendOutcome:
    return context.backend.set_priority_price_source_ids(context)


def _registry_sequence(context: ActionContext) -> BackendOutcome:
    return context.backend.assert_registry_sequence(context)


def _assets(context: ActionContext) -> BackendOutcome:
    return context.backend.apply_defaults_asset_configs(context)


def _finish_tokens(context: ActionContext) -> BackendOutcome:
    return context.backend.finish_token_setup(context)


def _disable_psm(context: ActionContext) -> BackendOutcome:
    return context.backend.set_auto_deposit_disabled(context)


def _capabilities(context: ActionContext) -> BackendOutcome:
    return context.backend.apply_exact_capability_set(context)


def _timelocks(context: ActionContext) -> BackendOutcome:
    return context.backend.finalize_timelocks(context)


def _handoff(context: ActionContext) -> BackendOutcome:
    return context.backend.irreversible_final_authority_handoff(context)


def _bind(context: ActionContext) -> BackendOutcome:
    return context.backend.bind_value(context)


def _deploy_blueprint(context: ActionContext) -> BackendOutcome:
    return context.backend.deploy_blueprint(context)


def _assert(context: ActionContext) -> BackendOutcome:
    return context.backend.assert_condition(context)


def _non_executing(context: ActionContext) -> BackendOutcome:
    return context.backend.non_executing(context)


def build_handler_registry() -> HandlerRegistry:
    """Build the exact 48-operation registry without a fallback handler."""

    registry = HandlerRegistry()
    rows = (
        (_contract("deploy", "deployment", "address,binding,blueprint,curve,curve-binding,input", "address", transactional=True), _deploy),
        # ERC-5202 blueprint deployment. Distinct from "deploy" because the
        # Contributor template is deployed as a blueprint, not as a live
        # contract -- Base does the same with migration.deploy_bp("Contributor").
        (_contract("deploy-blueprint", "deployment", "", "address", transactional=True), _deploy_blueprint),
        (_contract("register-and-confirm", "registration", "action,address", transactional=True), _register),
        (_contract("assert-constructor-registration", "registration"), _constructor_registration),
        (_contract("add-and-confirm-chainlink-feed", "configuration", "address,input", transactional=True), _chainlink),
        (_contract("validate-external-identities", "configuration", "curve"), _external_identities),
        (_contract("create-or-bind-pool", "configuration", "curve", "address", transactional=True), _pool),
        (_contract("assert-pool-runtime", "assertion", "address,curve"), _pool_assertion),
        (_contract("seed-pool-and-transfer-lp", "configuration", "address,curve", transactional=True), _seed_pool),
        (_contract("assert-direct-price", "assertion", "address,curve"), _direct_price),
        (_contract("add-and-confirm-curve-feed-after-id-two", "configuration", "action,address", transactional=True), _curve_feed),
        (_contract("set-priority-price-source-ids", "configuration", "defaults", transactional=True), _priority),
        (_contract("assert-registry-sequence", "assertion", "action"), _registry_sequence),
        (_contract("apply-defaults-asset-configs", "configuration", "defaults", transactional=True), _assets),
        (_contract("finish-token-setup", "configuration", "address", transactional=True), _finish_tokens),
        (_contract("set-auto-deposit-disabled", "configuration", "input", transactional=True), _disable_psm),
        (_contract("apply-exact-capability-set", "configuration", "binding", transactional=True), _capabilities),
        (_contract("finalize-timelocks", "configuration", "input-prefix", transactional=True), _timelocks),
        (_contract("irreversible-final-authority-handoff", "handoff", "action,binding", transactional=True), _handoff),
        (_contract("bind-approved-preexisting-or-produced-address", "configuration", "binding", "address"), _bind),
        (_contract("bind-role-identities", "configuration", "address,binding,input"), _bind),
    )
    assertion_rows = {
        "assert-artifact-capacity": ("assertion", "binding"),
        "assert-complete-launch-state": ("assertion", "binding"),
        "assert-constructor-provenance": ("assertion", "blueprint,defaults"),
        "assert-deployed-disabled": ("assertion", "address"),
        "assert-disabled-scaffold": ("assertion", "defaults,input"),
        "assert-feature-disabled": ("assertion", ""),
        "assert-input-prefix": ("assertion", "input-prefix"),
        "assert-lifecycle-separation": ("assertion", ""),
        "assert-source-invariant": ("assertion", "blueprint"),
        "assert-topology-authority": ("assertion", "blueprint"),
        "assert-typed-input": ("assertion", "input"),
    }
    nonexecuting_rows = {
        "assert-action-absent": ("omission", ""),
        "assert-action-family-absent": ("omission", ""),
        "assert-atomic-aapl-qualification-remains-blocked": ("blocked", "stock"),
        "assert-authority-boundary": ("tooling-only", ""),
        "assert-component-and-registry-absent": ("omission", ""),
        "assert-feature-family-absent": ("omission", ""),
        "assert-migration-absent": ("deferred", ""),
        "assert-offline-report-interface": ("tooling-only", ""),
        "assert-selection-state-absent": (("deferred", "omission"), ""),
        "assert-state-import-absent": ("omission", ""),
        "bind-approved-product-packet-and-operational-gates": ("blocked", "binding,defaults,input"),
        "bind-selected-tooling-component": ("tooling-only", ""),
        "declare-extension-seam": ("blocked", "input"),
        "declare-future-owner-action": ("blocked", "binding,input"),
        "pause-then-timelocked-disable-registry-address": ("recovery", ""),
        "timelocked-update-registry-address": ("recovery", "binding"),
    }
    for row in rows:
        registry.register(*row)
    for operation, (kinds, inputs) in assertion_rows.items():
        registry.register(_contract(operation, kinds, inputs), _assert)
    for operation, (kinds, inputs) in nonexecuting_rows.items():
        registry.register(_contract(operation, kinds, inputs), _non_executing)
    return registry


def _plain(value: Any) -> Any:
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, source_blueprint.SourceReference):
        return {"source_reference": value.path}
    if isinstance(value, source_blueprint.SymbolicBinding):
        raise RobinhoodExecutionError("RHX_SYMBOLIC_VALUE_UNRESOLVED")
    if hasattr(value, "__dataclass_fields__"):
        return {
            field: _plain(getattr(value, field))
            for field in value.__dataclass_fields__
        }
    raise RobinhoodExecutionError("RHX_VALUE_TYPE_UNSUPPORTED")


class RuntimeBindingStore:
    """Resolve the exact eleven-namespace source vocabulary."""

    def __init__(self, plan: Mapping[str, Any], backend: RobinhoodBackend) -> None:
        envelope = plan.get("execution_envelope")
        values = envelope.get("values", {}) if isinstance(envelope, Mapping) else {}
        self._accepted = dict(values)
        self._backend = backend
        self._runtime: dict[str, BoundValue] = {}
        self._actions: dict[str, BoundValue] = {}

    def add_output(self, reference: str, value: Any, *, deployment: bool) -> None:
        if reference in self._runtime:
            raise RobinhoodExecutionError("RHX_BINDING_DUPLICATE")
        if reference in self._accepted:
            raise RobinhoodExecutionError("RHX_DEPLOYMENT_OUTPUT_PREBOUND")
        if reference.startswith("address:") and (
            not isinstance(value, str) or _ADDRESS.fullmatch(value) is None
        ):
            raise RobinhoodExecutionError("RHX_ADDRESS_INVALID")
        self._runtime[reference] = BoundValue(
            reference,
            _plain(value),
            BindingProvenance.DEPLOYMENT if deployment else BindingProvenance.ACTION,
        )

    def add_action_result(self, action_id: str, receipt: Mapping[str, Any]) -> None:
        reference = f"action:{action_id.split(':', 2)[2]}"
        if reference in self._actions:
            raise RobinhoodExecutionError("RHX_ACTION_RESULT_DUPLICATE")
        self._actions[reference] = BoundValue(
            reference,
            {"action_id": action_id, "status": receipt["status"]},
            BindingProvenance.ACTION,
        )

    def resolve(self, reference: str) -> BoundValue:
        if reference == "binding:no-local-governance":
            # Resolved before the envelope on purpose. Departments deploy with
            # no local governance because RipeHq governance is the deployer and
            # LocalGov asserts `_initialGov != hqGov`; that is a property of the
            # contracts, not an operator choice, so an envelope must not be able
            # to override it with a different address.
            return BoundValue(reference, ZERO_ADDRESS, BindingProvenance.DERIVED)
        if reference in self._runtime:
            return self._runtime[reference]
        if reference in self._actions:
            return self._actions[reference]
        if reference in self._accepted:
            accepted = self._accepted[reference]
            if not isinstance(accepted, Mapping) or "value" not in accepted:
                raise RobinhoodExecutionError("RHX_ENVELOPE_VALUE_INVALID")
            return BoundValue(
                reference,
                _plain(accepted["value"]),
                BindingProvenance.ENVELOPE,
            )
        namespace, separator, key = reference.partition(":")
        if not separator:
            raise RobinhoodExecutionError("RHX_REFERENCE_INVALID")
        if namespace == "address":
            value = source_blueprint.ROBINHOOD_ADDRESSES.get(key)
            status = source_blueprint.ROBINHOOD_ADDRESS_STATUS.get(key)
            if status == "approved_semantic_absence":
                return BoundValue(reference, _plain(value), BindingProvenance.BLUEPRINT)
            raise RobinhoodExecutionError("RHX_BINDING_MISSING")
        if namespace == "input":
            row = source_blueprint.ROBINHOOD_DEPLOYMENT_INPUTS.get(key)
            if row is None or row.disposition not in {"approved", "disabled"}:
                raise RobinhoodExecutionError("RHX_BINDING_MISSING")
            if isinstance(row.value, source_blueprint.SourceReference):
                value = self._backend.resolve_derived(reference)
                provenance = BindingProvenance.DEFAULTS
            else:
                value = row.value
                provenance = BindingProvenance.BLUEPRINT
            return BoundValue(reference, _plain(value), provenance)
        if namespace == "curve":
            rows = {
                row.input_id: row for row in source_blueprint.ROBINHOOD_CURVE_LAUNCH_INPUTS
            }
            row = rows.get(key)
            if row is None or row.resolution_state in source_blueprint.ROBINHOOD_CURVE_BLOCKING_STATES:
                raise RobinhoodExecutionError("RHX_BINDING_MISSING")
            return BoundValue(reference, _plain(row.value), BindingProvenance.BLUEPRINT)
        if namespace == "curve-binding":
            row = next(
                item for item in source_blueprint.ROBINHOOD_CURVE_LAUNCH_INPUTS
                if item.input_id == "curve.constructor_bindings"
            )
            bindings = dict(row.value)
            binding = _CURVE_CONSTRUCTOR_VALUE_BINDINGS.get(key)
            if binding is None or bindings.get(key) != binding[0]:
                raise RobinhoodExecutionError("RHX_BINDING_MISSING")
            try:
                value = source_blueprint.PARAMS["local"][binding[1]]
            except KeyError as error:
                raise RobinhoodExecutionError(
                    "RHX_BINDING_MISSING"
                ) from error
            return BoundValue(
                reference, _plain(value), BindingProvenance.BLUEPRINT
            )
        if namespace == "stock":
            row = next(
                (item for item in source_blueprint.ROBINHOOD_STOCK_INPUT_QUALIFICATIONS if item.path == key),
                None,
            )
            if row is None or row.resolution != "repository_fact_integrated":
                raise RobinhoodExecutionError("RHX_BINDING_MISSING")
            return BoundValue(reference, _plain(row.candidate), BindingProvenance.DERIVED)
        if namespace == "registry":
            domain, component = key.split(":", 1)
            row = next(
                (item for item in source_blueprint.ROBINHOOD_REGISTRY_TOPOLOGY if item.domain == domain and item.component_id == component),
                None,
            )
            if row is None:
                raise RobinhoodExecutionError("RHX_BINDING_MISSING")
            return BoundValue(reference, _plain(row), BindingProvenance.BLUEPRINT)
        if namespace == "defaults":
            return BoundValue(
                reference,
                _plain(self._backend.resolve_derived(reference)),
                BindingProvenance.DEFAULTS,
            )
        if namespace == "blueprint":
            blueprint_values = {
                "defaults-constructor": source_blueprint.ROBINHOOD_DEFAULTS_CONSTRUCTOR,
                "registry-topology": source_blueprint.ROBINHOOD_REGISTRY_TOPOLOGY,
                "assertion:deleverage_launch_cooldown": source_blueprint.ROBINHOOD_ASSERTION_INVARIANTS["deleverage_launch_cooldown"],
                "chain:evm_block_number_seconds": source_blueprint.ROBINHOOD_CHAIN["evm_block_number_seconds"],
            }
            if key not in blueprint_values:
                raise RobinhoodExecutionError("RHX_BINDING_MISSING")
            return BoundValue(reference, _plain(blueprint_values[key]), BindingProvenance.BLUEPRINT)
        if namespace == "input-prefix":
            rows = {
                path: _plain(row.value)
                for path, row in source_blueprint.ROBINHOOD_DEPLOYMENT_INPUTS.items()
                if path.startswith(key) and row.disposition in {"approved", "disabled"}
            }
            if not rows:
                raise RobinhoodExecutionError("RHX_BINDING_MISSING")
            return BoundValue(reference, rows, BindingProvenance.BLUEPRINT)
        if namespace in {"binding", "action"}:
            raise RobinhoodExecutionError("RHX_BINDING_MISSING")
        raise RobinhoodExecutionError("RHX_NAMESPACE_UNSUPPORTED")

    def resolve_if_available(self, reference: str) -> BoundValue | None:
        try:
            return self.resolve(reference)
        except RobinhoodExecutionError as error:
            if error.code == "RHX_BINDING_MISSING":
                return None
            raise


def _reference_census(plan: Mapping[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for stage in plan["stages"]:
        for action in stage["actions"]:
            references = [
                *action.get("constructor", []),
                *action.get("requires", []),
                *action.get("provides", []),
            ]
            if action.get("registry_ref") is not None:
                references.append(action["registry_ref"])
            for reference in references:
                namespace = reference.split(":", 1)[0]
                counts[namespace] = counts.get(namespace, 0) + 1
    return dict(sorted(counts.items()))


def semantic_plan_from_h05(plan: Mapping[str, Any]) -> dict[str, Any]:
    """Adapt a validated H-05 plan to the closed H-06 semantic plan."""

    members = [
        {"path": item["path"], "sha256": item["sha256"]}
        for item in plan["source"]["planning_inputs"]
    ]
    members.sort(key=lambda item: item["path"].encode("utf-8"))
    registry = build_handler_registry()
    steps = []
    for stage in plan["stages"]:
        actions = []
        for action in stage["actions"]:
            contract, _ = registry.get(action["operation"])
            nonexecuting = action["kind"] in NON_EXECUTING_KINDS
            expected = []
            for postcondition in action["postconditions"]:
                if nonexecuting:
                    value = {
                        "state": "not-applicable",
                        "type": "boolean",
                        "value": None,
                        "reason_code": "non-executing-source-action",
                    }
                else:
                    value = {"state": "known", "type": "boolean", "value": True}
                expected.append(
                    {
                        "postcondition_id": postcondition,
                        "kind": "assertion",
                        "subject": action["semantic_action_id"],
                        "value": value,
                    }
                )
            expected.sort(
                key=lambda item: item["postcondition_id"].encode("utf-8")
            )
            disposition = None
            if nonexecuting:
                explanation = hashlib.sha256(
                    canonical_jcs_bytes(
                        {
                            "action_id": action["action_id"],
                            "kind": action["kind"],
                            "operation": action["operation"],
                        }
                    )
                ).hexdigest()
                disposition = {
                    "code": "source-declared-non-executing",
                    "authority_ref": f"migrations/robinhood/{stage['migration_id']}",
                    "explanation_digest_sha256": explanation,
                }
            actions.append(
                {
                    "action_id": action["action_id"],
                    "semantic_action_id": action["semantic_action_id"],
                    "ordinal": action["ordinal"],
                    "kind": action["kind"],
                    "required": not nonexecuting,
                    "transaction_required": contract.transactional and not nonexecuting,
                    "expected_postconditions": expected,
                    "supersedes": [],
                    "disposition": disposition,
                }
            )
        steps.append(
            {
                "migration_id": stage["migration_id"],
                "semantic_step_id": stage["semantic_id"],
                "ordinal": stage["ordinal"],
                "required": True,
                "actions": actions,
            }
        )
    semantic = {
        "profile": {
            "profile_id": plan["profile"]["profile_id"],
            "expected_chain_id": plan["profile"]["expected_chain_id"],
        },
        "source": {
            "commit": plan["source"]["commit"],
            "tree": plan["source"]["tree"],
            "source_set_sha256": source_set_sha256(members),
            "members": members,
        },
        "steps": steps,
    }
    validate_semantic_plan(semantic)
    return semantic


def _canonical_input(item: BoundValue) -> dict[str, Any]:
    encoded = canonical_jcs_bytes(_plain(item.value))
    return {
        "reference": item.reference,
        "provenance": item.provenance.value,
        "canonical_value": encoded.decode("utf-8"),
        "value_sha256": hashlib.sha256(encoded).hexdigest(),
    }


def _canonical_output(reference: str, value: Any) -> dict[str, Any]:
    if (
        not reference.startswith("address:")
        or not isinstance(value, str)
        or _ADDRESS.fullmatch(value) is None
    ):
        raise RobinhoodExecutionError("RHX_OUTPUT_RECEIPT_INVALID")
    normalized = value.lower()
    encoded = canonical_jcs_bytes(normalized)
    return {
        "reference": reference,
        "type": "address",
        "value": normalized,
        "value_sha256": hashlib.sha256(encoded).hexdigest(),
    }


def _relinquishment_evidence(
    item: AuthorityRelinquishment,
) -> dict[str, Any]:
    return {
        "contract_reference": item.contract_reference,
        "contract_address": item.contract_address,
        "sequence": item.sequence,
        "status": item.status,
        "transaction_identity": item.transaction_identity,
        "temporary_governance_before": item.temporary_governance_before,
        "local_governance_after": item.local_governance_after,
        "ripe_hq_governance_after": item.ripe_hq_governance_after,
        "temporary_can_govern_after": item.temporary_can_govern_after,
        "final_can_govern_after": item.final_can_govern_after,
        "failure_classification": item.failure_classification,
    }


def _not_transaction(action_id: str) -> dict[str, Any]:
    return {
        "required": False,
        "request_identity": {
            "state": "not-applicable",
            "semantic_request_id": None,
            "plan_action_sha256": None,
            "reason_code": "non-transaction-action",
        },
        "submission": {"status": "not-applicable", "transaction_hash": None},
        "receipt": {
            "status": "not-applicable",
            "transaction_hash": None,
            "block_number": None,
            "block_hash": None,
            "success": None,
            "gas_used": None,
            "cumulative_gas_used": {
                "state": "not-applicable",
                "type": "uint256",
                "value": None,
                "reason_code": "non-transaction-action",
            },
        },
        "finality": {
            "status": "not-applicable",
            "policy_id": None,
            "required_confirmations": None,
            "required_finality_tag": {
                "state": "not-applicable",
                "type": "string",
                "value": None,
                "reason_code": "non-transaction-action",
            },
            "observed_confirmations": None,
            "observation_block_number": None,
            "observation_block_hash": None,
        },
        "reconciliation": {
            "status": "not-applicable",
            "observation_source_code": None,
            "check_ids": [],
        },
    }


def _completed_transaction(
    semantic_digest: str,
    action_id: str,
    outcome: BackendOutcome,
) -> dict[str, Any]:
    identity = outcome.execution_identity
    if identity is None or re.fullmatch(r"0x[0-9a-f]{64}", identity) is None:
        raise RobinhoodExecutionError("RHX_EXECUTION_IDENTITY_INVALID", action_id=action_id)
    block_number = outcome.block_number if outcome.block_number is not None else 1
    block_hash = outcome.block_hash
    if block_hash is None:
        block_hash = "0x" + hashlib.sha256(
            f"local-block:{identity}".encode("ascii")
        ).hexdigest()
    observation_number = block_number + 64
    observation_hash = "0x" + hashlib.sha256(
        f"local-finality:{identity}".encode("ascii")
    ).hexdigest()
    return {
        "required": True,
        "request_identity": {
            "state": "known",
            "semantic_request_id": action_id,
            "plan_action_sha256": plan_action_sha256(semantic_digest, action_id),
        },
        "submission": {"status": "submitted", "transaction_hash": identity},
        "receipt": {
            "status": "confirmed",
            "transaction_hash": identity,
            "block_number": block_number,
            "block_hash": block_hash,
            "success": True,
            "gas_used": 0,
            "cumulative_gas_used": {"state": "known", "type": "uint256", "value": 0},
        },
        "finality": {
            "status": "complete",
            "policy_id": FINALITY_POLICY_ID,
            "required_confirmations": 64,
            "required_finality_tag": {
                "state": "not-applicable",
                "type": "string",
                "value": None,
                "reason_code": "confirmation-depth-policy",
            },
            "observed_confirmations": 64,
            "observation_block_number": observation_number,
            "observation_block_hash": observation_hash,
        },
        "reconciliation": {
            "status": "reconciled",
            "observation_source_code": "deterministic-local-observer",
            "check_ids": [
                "events",
                "postconditions",
                "profile-chain",
                "receipt-block-identity",
                "receipt-identity",
                "receipt-success",
                "second-observation",
            ],
        },
    }


class H06HistoryWriter:
    def __init__(
        self,
        history_root: Path,
        semantic_plan: Mapping[str, Any],
        repository_root: Path,
    ) -> None:
        if not history_root.is_absolute():
            raise RobinhoodExecutionError("RHX_HISTORY_ROOT_INVALID")
        self.root = history_root
        self.plan = semantic_plan
        self.repository_root = repository_root
        self.digest = plan_sha256(semantic_plan)
        profile = semantic_plan["profile"]
        source = semantic_plan["source"]
        result = read_history(
            profile["profile_id"],
            profile["expected_chain_id"],
            self.digest,
            source["commit"],
            source["tree"],
            history_root,
        )
        if result.state not in {HistoryState.ABSENT_CLEAN, HistoryState.INCOMPLETE, HistoryState.VALID}:
            raise RobinhoodExecutionError("RHX_HISTORY_REJECTED")
        self.records = list(result.records)
        self.attempts = list(result.attempts)
        self.current_index = result.current_index

    @property
    def completed_results(self) -> tuple[Mapping[str, Any], ...]:
        completed: dict[str, Mapping[str, Any]] = {}
        for artifact in (*self.records, *self.attempts):
            for action in artifact["step"]["actions"]:
                if action["status"] not in {"reconciled", "complete"}:
                    continue
                previous = completed.get(action["action_id"])
                if previous is not None and previous != action:
                    raise RobinhoodExecutionError("RHX_RESUME_ACTION_AMBIGUOUS")
                completed[action["action_id"]] = action
        ordered = [
            action["action_id"]
            for step in self.plan["steps"]
            for action in step["actions"]
        ]
        return tuple(completed[action_id] for action_id in ordered if action_id in completed)

    def _base(self, step: Mapping[str, Any]) -> dict[str, Any]:
        previous = self.records[-1] if self.records else None
        digest = self.digest
        completed = sorted(
            item["semantic_step_id"]
            for item in self.plan["steps"]
            if item["required"] and item["ordinal"] <= step["ordinal"]
        )
        remaining = sorted(
            item["semantic_step_id"]
            for item in self.plan["steps"]
            if item["required"] and item["ordinal"] > step["ordinal"]
        )
        return {
            "schema": "ripe.robinhood.deployment-manifest",
            "schema_version": 2,
            "profile": copy.deepcopy(self.plan["profile"]),
            "source": {
                **copy.deepcopy(self.plan["source"]),
                "plan_sha256": digest,
            },
            "step": {
                "migration_id": step["migration_id"],
                "semantic_step_id": step["semantic_step_id"],
                "ordinal": step["ordinal"],
                "previous_record_id": None if previous is None else previous["record_id"],
                "previous_record_sha256": None if previous is None else previous["record_sha256"],
            },
            "plan_state": {
                "plan_sha256": digest,
                "predecessor_plan_sha256": None,
                "completed_step_ids": completed,
                "remaining_required_step_ids": remaining,
                "status": "complete" if not remaining else "in-progress",
            },
        }

    def publish_step(self, step: Mapping[str, Any], actions: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
        base = self._base(step)
        artifact = {
            **base,
            "artifact_kind": "immutable_step_record",
            "record_id": (
                f"{self.plan['profile']['profile_id']}:{self.digest}:"
                f"{step['migration_id']}:{step['semantic_step_id']}"
            ),
            "record_sha256": "0" * 64,
        }
        artifact["step"].update({"status": "complete", "actions": list(actions)})
        sealed = seal_artifact(artifact)
        prior = self.records[-1]["record_sha256"] if self.records else None
        result = publish_immutable(
            self.root,
            sealed,
            semantic_plans=[self.plan],
            expected_prior_record_sha256=prior,
            repository_root=self.repository_root,
        )
        self._require_write(result)
        self.records.append(sealed)
        return sealed

    def publish_attempt(
        self,
        step: Mapping[str, Any],
        actions: Sequence[Mapping[str, Any]],
    ) -> Mapping[str, Any]:
        base = self._base(step)
        prior = self.records[-1] if self.records else None
        seed = canonical_jcs_bytes(
            {"step": step["migration_id"], "actions": [item["status"] for item in actions], "prior": None if prior is None else prior["record_sha256"]}
        )
        artifact = {
            **base,
            "artifact_kind": "attempt_record",
            "attempt_id": hashlib.sha256(seed).hexdigest()[:32],
            "attempt_sha256": "0" * 64,
            "base_record_id": None if prior is None else prior["record_id"],
            "base_record_sha256": None if prior is None else prior["record_sha256"],
            "retention_class": "failure-30d",
        }
        artifact["step"].update({"status": "failed", "actions": list(actions)})
        artifact["plan_state"]["completed_step_ids"] = sorted(
            item["semantic_step_id"] for item in self.plan["steps"]
            if item["required"] and item["ordinal"] < step["ordinal"]
        )
        artifact["plan_state"]["remaining_required_step_ids"] = sorted(
            item["semantic_step_id"] for item in self.plan["steps"]
            if item["required"] and item["ordinal"] >= step["ordinal"]
        )
        artifact["plan_state"]["status"] = "failed"
        sealed = seal_artifact(artifact)
        result = publish_immutable(
            self.root,
            sealed,
            semantic_plans=[self.plan],
            expected_prior_record_sha256=None if prior is None else prior["record_sha256"],
            repository_root=self.repository_root,
        )
        self._require_write(result)
        self.attempts.append(sealed)
        return sealed

    def promote(self, record: Mapping[str, Any]) -> Mapping[str, Any]:
        prior = None if self.current_index is None else self.current_index["index_sha256"]
        index = seal_artifact(
            {
                "schema": "ripe.robinhood.deployment-manifest",
                "schema_version": 2,
                "artifact_kind": "current_index",
                "index_sha256": "0" * 64,
                "profile": copy.deepcopy(record["profile"]),
                "source": {
                    "commit": record["source"]["commit"],
                    "tree": record["source"]["tree"],
                    "plan_sha256": record["source"]["plan_sha256"],
                },
                "target": {
                    "path": immutable_basename(record),
                    "record_id": record["record_id"],
                    "record_sha256": record["record_sha256"],
                },
                "prior_index_sha256": prior,
                "plan_status": "complete",
            }
        )
        result = promote_current_index(
            self.root,
            index,
            semantic_plans=[self.plan],
            expected_prior_index_sha256=prior,
        )
        self._require_write(result)
        self.current_index = index
        return index

    @staticmethod
    def _require_write(result: WriteResult) -> None:
        if not result.succeeded:
            raise RobinhoodExecutionError("RHX_HISTORY_WRITE_FAILED")


class RobinhoodStageExecutor:
    """Execute the validated plan exactly once, one shared stage at a time."""

    def __init__(
        self,
        plan: Mapping[str, Any],
        *,
        repository_root: str | Path,
        backend: RobinhoodBackend,
        history_root: str | Path | None = None,
        registry: HandlerRegistry | None = None,
    ) -> None:
        root = Path(repository_root)
        try:
            self.plan = validate_execution_plan_artifact(plan, repository_root=root)
        except MigrationPlanError as error:
            raise RobinhoodExecutionError("RHX_PLAN_REJECTED") from error
        if self.plan.get("execution_envelope") is None:
            raise RobinhoodExecutionError("RHX_EXECUTION_ENVELOPE_REQUIRED")
        self.repository_root = root
        self.backend = backend
        self.registry = registry or build_handler_registry()
        self.semantic_plan = semantic_plan_from_h05(self.plan)
        self.semantic_digest = plan_sha256(self.semantic_plan)
        self.bindings = RuntimeBindingStore(self.plan, backend)
        self.results: dict[str, Mapping[str, Any]] = {}
        self.stage_cursor = 0
        self.history = (
            H06HistoryWriter(Path(history_root), self.semantic_plan, root)
            if history_root is not None
            else None
        )
        self._preflight()
        if self.history is not None:
            self._restore(self.history.completed_results)

    def _preflight(self) -> None:
        temporary = self.bindings.resolve(
            "binding:temporary-local-governance"
        ).value
        final_governance = self.bindings.resolve(
            "input:Deployment.DP-18.roles.governance"
        ).value
        if not isinstance(temporary, str) or _ADDRESS.fullmatch(temporary) is None:
            raise RobinhoodExecutionError(
                "RHX_TEMPORARY_GOVERNANCE_INVALID"
            )
        if temporary.lower() == "0x" + "0" * 40:
            raise RobinhoodExecutionError("RHX_TEMPORARY_GOVERNANCE_ZERO")
        if temporary.lower() == str(final_governance).lower():
            raise RobinhoodExecutionError(
                "RHX_TEMPORARY_GOVERNANCE_IS_FINAL"
            )
        if temporary.lower() != self.backend.execution_sender.lower():
            raise RobinhoodExecutionError(
                "RHX_TEMPORARY_GOVERNANCE_SENDER_MISMATCH"
            )
        stages = self.plan["stages"]
        if tuple(stage["migration_id"] for stage in stages) != EXPECTED_STAGE_IDS:
            raise RobinhoodExecutionError("RHX_STAGE_CENSUS_DRIFT")
        actions = [action for stage in stages for action in stage["actions"]]
        census = self.plan["action_census"]
        if (len(actions), census["deployments"], census["registrations"]) != (118, 37, 33):
            raise RobinhoodExecutionError("RHX_ACTION_CENSUS_DRIFT")
        operations = {action["operation"] for action in actions}
        self.registry.validate_vocabulary(operations)
        if _reference_census(self.plan) != EXPECTED_NAMESPACE_COUNTS:
            raise RobinhoodExecutionError("RHX_NAMESPACE_CENSUS_DRIFT")
        produced: set[str] = set()
        completed_actions: set[str] = set()
        for action in actions:
            contract, _ = self.registry.get(action["operation"])
            if action["kind"] not in contract.kinds:
                raise RobinhoodExecutionError("RHX_HANDLER_KIND_MISMATCH")
            references = [*action.get("constructor", []), *action.get("requires", [])]
            namespaces = {reference.split(":", 1)[0] for reference in references}
            if not namespaces <= contract.input_namespaces:
                raise RobinhoodExecutionError("RHX_HANDLER_INPUT_CONTRACT")
            output_namespaces = {
                reference.split(":", 1)[0] for reference in action.get("provides", [])
            }
            if output_namespaces != contract.output_namespaces and output_namespaces:
                raise RobinhoodExecutionError("RHX_HANDLER_OUTPUT_CONTRACT")
            for reference in references:
                if action["kind"] in NON_EXECUTING_KINDS:
                    self.bindings.resolve_if_available(reference)
                    continue
                if reference.startswith("address:") and reference in produced:
                    continue
                if reference.startswith("action:") and reference[7:] in completed_actions:
                    continue
                if reference.startswith("address:") and source_blueprint.ROBINHOOD_ADDRESS_STATUS.get(reference[8:]) == "deployment_produced_unresolved":
                    raise RobinhoodExecutionError("RHX_DEPLOYMENT_OUTPUT_ORDER")
                if reference.startswith("action:"):
                    raise RobinhoodExecutionError("RHX_ACTION_DEPENDENCY_ORDER")
                self.bindings.resolve(reference)
            produced.update(action.get("provides", []))
            completed_actions.add(action["semantic_action_id"])

    def _restore(self, results: Sequence[Mapping[str, Any]]) -> None:
        by_id = {
            action["action_id"]: action
            for stage in self.plan["stages"]
            for action in stage["actions"]
        }
        for result in results:
            action = by_id.get(result["action_id"])
            if action is None:
                raise RobinhoodExecutionError("RHX_RESUME_ACTION_UNKNOWN")
            validated = validate_execution_handoff(self.semantic_plan, result)
            evidence = validated.get("execution_evidence")
            if evidence is None:
                raise RobinhoodExecutionError("RHX_RESUME_EVIDENCE_MISSING")
            outputs = {
                item["reference"]: item["value"]
                for item in evidence["outputs"]
            }
            if set(outputs) != set(action.get("provides", [])):
                raise RobinhoodExecutionError("RHX_RESUME_OUTPUT_MISSING")
            for reference in action.get("provides", []):
                output = outputs.get(reference)
                if output is None:
                    raise RobinhoodExecutionError("RHX_RESUME_OUTPUT_MISSING")
                self.bindings.add_output(
                    reference, output, deployment=action["kind"] == "deployment"
                )
            self.results[action["action_id"]] = validated
            self.bindings.add_action_result(action["action_id"], validated)
            self.backend.restore_completed_action(
                self.plan, action, evidence
            )
        if self.history is not None:
            for attempt in self.history.attempts:
                for failed in attempt["step"]["actions"]:
                    if (
                        failed["status"] != "failed"
                        or failed["action_id"] in self.results
                    ):
                        continue
                    action = by_id.get(failed["action_id"])
                    evidence = failed.get("execution_evidence")
                    if action is None or evidence is None:
                        continue
                    self.backend.restore_failed_action(
                        self.plan, action, evidence
                    )
        completed_stages = {
            action_id.split(":", 1)[0] for action_id in self.results
        }
        while (
            self.stage_cursor < len(self.plan["stages"])
            and self.plan["stages"][self.stage_cursor]["migration_id"] in completed_stages
            and all(
                action["action_id"] in self.results
                for action in self.plan["stages"][self.stage_cursor]["actions"]
            )
        ):
            self.stage_cursor += 1

    def __call__(self, migration: Any, stage: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
        if self.stage_cursor >= len(self.plan["stages"]):
            raise RobinhoodExecutionError("RHX_STAGE_REPLAY")
        planned_stage = self.plan["stages"][self.stage_cursor]
        if (
            stage.get("migration_id") != planned_stage["migration_id"]
            or stage.get("semantic_id") != planned_stage["semantic_id"]
            or len(stage.get("actions", ())) != len(planned_stage["actions"])
        ):
            raise RobinhoodExecutionError("RHX_STAGE_SOURCE_MISMATCH")
        stage_results: list[Mapping[str, Any]] = []
        try:
            for action in planned_stage["actions"]:
                if action["action_id"] in self.results:
                    restored = self.results[action["action_id"]]
                    migration.handoff_manifest_v2_action_result(
                        self.semantic_plan, restored
                    )
                    stage_results.append(restored)
                    continue
                result = self._execute_action(migration, planned_stage, action)
                stage_results.append(result)
        except RobinhoodExecutionError as error:
            if self.history is not None:
                attempt_actions = self._attempt_actions(
                    planned_stage, stage_results, error
                )
                self.history.publish_attempt(
                    self.semantic_plan["steps"][self.stage_cursor], attempt_actions
                )
            raise
        terminal_record = None
        if self.history is not None:
            terminal_record = self.history.publish_step(
                self.semantic_plan["steps"][self.stage_cursor], stage_results
            )
        self.stage_cursor += 1
        if self.stage_cursor == len(self.plan["stages"]):
            final_id = "0900:000005:handoff-governance-and-relinquish-deployer"
            if list(self.results)[-1] != final_id or len(self.results) != 118:
                raise RobinhoodExecutionError("RHX_FINAL_HANDOFF_ORDER")
            if self.history is not None and terminal_record is not None:
                self.history.promote(terminal_record)
        return tuple(stage_results)

    def _execute_action(
        self,
        migration: Any,
        stage: Mapping[str, Any],
        action: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        # Every other action must already have completed before the irreversible
        # handoff: 117 of 118, the handoff itself being the last. Was 116 before
        # the pool seed action was added to 0600.
        if action["kind"] == "handoff" and len(self.results) != 117:
            raise RobinhoodExecutionError("RHX_FINAL_HANDOFF_PRECONDITION", action_id=action["action_id"])
        references = [*action.get("constructor", []), *action.get("requires", [])]
        if action["kind"] in NON_EXECUTING_KINDS:
            inputs = tuple(
                item
                for reference in references
                if (item := self.bindings.resolve_if_available(reference))
                is not None
            )
        else:
            inputs = tuple(self.bindings.resolve(reference) for reference in references)
        contract, handler = self.registry.get(action["operation"])
        context = ActionContext(
            self.plan,
            self.semantic_plan,
            stage,
            action,
            inputs,
            self.backend,
            self.repository_root,
        )
        try:
            outcome = handler(context)
        except RobinhoodExecutionError:
            raise
        except Exception as error:
            raise RobinhoodExecutionError("RHX_HANDLER_FAILED", action_id=action["action_id"]) from error
        outputs = dict(outcome.outputs or {})
        expected_outputs = set(action.get("provides", []))
        if set(outputs) != expected_outputs:
            raise RobinhoodExecutionError("RHX_OUTPUT_MISMATCH", action_id=action["action_id"])
        for reference, value in outputs.items():
            self.bindings.add_output(reference, value, deployment=action["kind"] == "deployment")
        result = self._complete_result(stage, action, inputs, contract, outcome)
        validated = migration.handoff_manifest_v2_action_result(
            self.semantic_plan, result
        )
        self.results[action["action_id"]] = validated
        self.bindings.add_action_result(action["action_id"], validated)
        return validated

    def _complete_result(
        self,
        stage: Mapping[str, Any],
        action: Mapping[str, Any],
        inputs: tuple[BoundValue, ...],
        contract: OperationContract,
        outcome: BackendOutcome,
    ) -> dict[str, Any]:
        semantic_action = self.semantic_plan["steps"][stage["ordinal"]]["actions"][action["ordinal"]]
        transaction = (
            _completed_transaction(self.semantic_digest, action["action_id"], outcome)
            if semantic_action["transaction_required"]
            else _not_transaction(action["action_id"])
        )
        observation_number = (
            transaction["finality"]["observation_block_number"]
            if transaction["required"]
            else None
        )
        observation_hash = (
            transaction["finality"]["observation_block_hash"]
            if transaction["required"]
            else None
        )
        nonexecuting = action["kind"] in NON_EXECUTING_KINDS
        observed = []
        assertions = list(outcome.assertions)
        if not nonexecuting and not assertions:
            assertions = [
                AssertionResult(
                    item["postcondition_id"],
                    True,
                    hashlib.sha256(
                        f"{action['action_id']}:{item['postcondition_id']}".encode("ascii")
                    ).hexdigest(),
                )
                for item in semantic_action["expected_postconditions"]
            ]
        assertion_map = {item.assertion_id: item for item in assertions}
        for expected in semantic_action["expected_postconditions"]:
            if nonexecuting:
                observed.append(
                    {
                        "postcondition_id": expected["postcondition_id"],
                        "value": copy.deepcopy(expected["value"]),
                        "observation": {"method_code": "not-applicable", "block_number": None, "block_hash": None},
                        "status": "not-applicable",
                    }
                )
                continue
            assertion = assertion_map.get(expected["postcondition_id"])
            if assertion is None or not assertion.matched:
                raise RobinhoodExecutionError("RHX_POSTCONDITION_FAILED", action_id=action["action_id"])
            observed.append(
                {
                    "postcondition_id": expected["postcondition_id"],
                    "value": copy.deepcopy(expected["value"]),
                    "observation": {
                        "method_code": "deterministic-local-observation",
                        "block_number": observation_number,
                        "block_hash": observation_hash,
                    },
                    "status": "matched",
                }
            )
        artifact = None
        if outcome.artifact is not None:
            artifact = {
                "source_path": outcome.artifact.source_path,
                "source_sha256": outcome.artifact.source_sha256,
                "runtime_sha256": outcome.artifact.runtime_sha256,
            }
        dependencies = sorted(
            self.results[item.value["action_id"]]["action_id"]
            for item in inputs
            if item.provenance is BindingProvenance.ACTION
            and isinstance(item.value, Mapping)
            and "action_id" in item.value
        )
        result = {
            key: copy.deepcopy(semantic_action[key])
            for key in (
                "action_id", "semantic_action_id", "ordinal", "kind", "required",
                "expected_postconditions", "supersedes", "disposition",
            )
        }
        result.update(
            {
                "status": "complete",
                "observed_postconditions": observed,
                "transaction": transaction,
                "events": [],
                "error": None,
                "execution_evidence": {
                    "h05_plan_sha256": self.plan["plan_hash"],
                    "h06_plan_sha256": self.semantic_digest,
                    "stage_id": stage["migration_id"],
                    "operation": action["operation"],
                    "inputs": [_canonical_input(item) for item in inputs],
                    "outputs": [
                        _canonical_output(reference, value)
                        for reference, value in sorted(
                            (outcome.outputs or {}).items()
                        )
                    ],
                    "dependency_action_ids": dependencies,
                    "execution_identity": outcome.execution_identity,
                    "deployed_address": outcome.deployed_address,
                    "artifact": artifact,
                    "registry_id": outcome.registry_id,
                    "assertions": [
                        {
                            "assertion_id": item.assertion_id,
                            "matched": item.matched,
                            "evidence_sha256": item.evidence_sha256,
                        }
                        for item in assertions
                    ],
                    "failure_classification": None,
                    "previous_record_sha256": (
                        None if self.history is None or not self.history.records
                        else self.history.records[-1]["record_sha256"]
                    ),
                    "authority_relinquishments": [
                        _relinquishment_evidence(item)
                        for item in outcome.authority_relinquishments
                    ],
                    "retained_temporary_governance": list(
                        outcome.retained_temporary_governance
                    ),
                },
            }
        )
        return result

    def _attempt_actions(
        self,
        stage: Mapping[str, Any],
        completed: Sequence[Mapping[str, Any]],
        error: RobinhoodExecutionError,
    ) -> list[Mapping[str, Any]]:
        results = list(completed)
        for action in stage["actions"][len(results):]:
            semantic = self.semantic_plan["steps"][stage["ordinal"]]["actions"][action["ordinal"]]
            result = {
                key: copy.deepcopy(semantic[key])
                for key in (
                    "action_id", "semantic_action_id", "ordinal", "kind", "required",
                    "expected_postconditions", "supersedes", "disposition",
                )
            }
            required = semantic["transaction_required"]
            transaction = _not_transaction(action["action_id"])
            if required:
                transaction = {
                    "required": True,
                    "request_identity": {
                        "state": "known",
                        "semantic_request_id": action["action_id"],
                        "plan_action_sha256": plan_action_sha256(self.semantic_digest, action["action_id"]),
                    },
                    "submission": {"status": "planned", "transaction_hash": None},
                    "receipt": {
                        "status": "pending", "transaction_hash": None, "block_number": None,
                        "block_hash": None, "success": None, "gas_used": None,
                        "cumulative_gas_used": {"state": "unknown", "type": "uint256", "value": None, "reason_code": "not-submitted"},
                    },
                    "finality": {
                        "status": "pending", "policy_id": FINALITY_POLICY_ID, "required_confirmations": 64,
                        "required_finality_tag": {"state": "not-applicable", "type": "string", "value": None, "reason_code": "confirmation-depth-policy"},
                        "observed_confirmations": 0, "observation_block_number": None, "observation_block_hash": None,
                    },
                    "reconciliation": {"status": "pending", "observation_source_code": None, "check_ids": []},
                }
            status = "failed" if len(results) == len(completed) else "planned"
            if status == "failed":
                result["error"] = {"code": "H06_EXECUTION_FAILED", "phase": "reconcile", "action_id": action["action_id"]}
            else:
                result["error"] = None
            result.update(
                {
                    "status": status,
                    "observed_postconditions": [],
                    "transaction": transaction,
                    "events": [],
                }
            )
            if status == "failed":
                outcome = (
                    error.outcome
                    if isinstance(error, RobinhoodBackendFailure)
                    else BackendOutcome()
                )
                references = [
                    *action.get("constructor", []),
                    *action.get("requires", []),
                ]
                inputs = []
                for reference in references:
                    try:
                        item = self.bindings.resolve(reference)
                    except RobinhoodExecutionError:
                        continue
                    inputs.append(item)
                dependencies = sorted(
                    item.value["action_id"]
                    for item in inputs
                    if item.provenance is BindingProvenance.ACTION
                    and isinstance(item.value, Mapping)
                    and "action_id" in item.value
                )
                artifact = None
                if outcome.artifact is not None:
                    artifact = {
                        "source_path": outcome.artifact.source_path,
                        "source_sha256": outcome.artifact.source_sha256,
                        "runtime_sha256": outcome.artifact.runtime_sha256,
                    }
                result["execution_evidence"] = {
                    "h05_plan_sha256": self.plan["plan_hash"],
                    "h06_plan_sha256": self.semantic_digest,
                    "stage_id": stage["migration_id"],
                    "operation": action["operation"],
                    "inputs": [_canonical_input(item) for item in inputs],
                    "outputs": [
                        _canonical_output(reference, value)
                        for reference, value in sorted(
                            (outcome.outputs or {}).items()
                        )
                    ],
                    "dependency_action_ids": dependencies,
                    "execution_identity": outcome.execution_identity,
                    "deployed_address": outcome.deployed_address,
                    "artifact": artifact,
                    "registry_id": outcome.registry_id,
                    "assertions": [
                        {
                            "assertion_id": item.assertion_id,
                            "matched": item.matched,
                            "evidence_sha256": item.evidence_sha256,
                        }
                        for item in outcome.assertions
                    ],
                    "failure_classification": error.code.removeprefix(
                        "RHX_"
                    ).lower().replace("_", "-"),
                    "previous_record_sha256": (
                        None
                        if self.history is None or not self.history.records
                        else self.history.records[-1]["record_sha256"]
                    ),
                    "authority_relinquishments": [
                        _relinquishment_evidence(item)
                        for item in outcome.authority_relinquishments
                    ],
                    "retained_temporary_governance": list(
                        outcome.retained_temporary_governance
                    ),
                }
            results.append(result)
        return results


def install_robinhood_executor(
    deploy_args: Any,
    plan: Mapping[str, Any],
    *,
    repository_root: str | Path,
    backend: RobinhoodBackend,
    history_root: str | Path | None = None,
) -> RobinhoodStageExecutor:
    executor = RobinhoodStageExecutor(
        plan,
        repository_root=repository_root,
        backend=backend,
        history_root=history_root,
    )
    deploy_args.robinhood_execution_plan = plan
    deploy_args.robinhood_repository_root = str(repository_root)
    deploy_args.robinhood_stage_executor = executor
    return executor
