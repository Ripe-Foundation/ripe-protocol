"""Robinhood deployment-manifest v2 schema, hashes, history, and writers.

This module deliberately uses only the Python standard library.  It is the
authoritative schema construction and validation implementation; the committed
JSON schema is a deterministic rendering of :func:`build_manifest_schema`.

The filesystem writer is intentionally narrow.  Immutable publication is
supported only on local APFS on macOS through
``renameatx_np(..., RENAME_EXCL)``.  Other platforms and filesystems fail
closed.  ``os.replace`` is used only by the separately validated current-index
promotion protocol.
"""

from __future__ import annotations

import copy
import ctypes
import errno
import fcntl
import hashlib
import hmac
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import stat
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Iterable, Mapping, Sequence

from scripts.utils import json_file


SCHEMA_ID = "ripe.robinhood.deployment-manifest"
SCHEMA_VERSION = 2
FINALITY_POLICY_ID = "robinhood-confirmations-64-v1"
EVENT_EVIDENCE_DOMAIN = b"ripe-manifest-v2-event-evidence"
SOURCE_SET_DOMAIN = b"ripe-manifest-v2-source"
PLAN_DOMAIN = b"ripe-manifest-v2-plan"
PLAN_ACTION_DOMAIN = b"ripe-manifest-v2-plan-action"
RENAME_EXCL = 0x00000004
F_FULLFSYNC = 51

_HEX40 = r"^[0-9a-f]{40}$"
_HEX64 = r"^[0-9a-f]{64}$"
_HEX32 = r"^[0-9a-f]{32}$"
_PUBLIC_ADDRESS = r"^0x[0-9a-f]{40}$"
_PUBLIC_BYTES32 = r"^0x[0-9a-f]{64}$"
_PUBLIC_BYTES = r"^0x(?:[0-9a-f]{2})*$"
_MIGRATION_ID = r"^[0-9]{4}$"
_SLUG = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
_ACTION_ID = r"^[0-9]{4}:[0-9]{6}:[a-z0-9]+(?:-[a-z0-9]+)*$"
_RECORD_ID = (
    r"^robinhood-(?:mainnet|testnet):[0-9a-f]{64}:"
    r"[0-9]{4}:[a-z0-9]+(?:-[a-z0-9]+)*$"
)
_IMMUTABLE_NAME = re.compile(
    r"^(?P<migration_id>[0-9]{4})-"
    r"(?P<step_id>[a-z0-9]+(?:-[a-z0-9]+)*)-"
    r"(?P<digest>[0-9a-f]{64})\.manifest-v2\.json$"
)
_ATTEMPT_NAME = re.compile(
    r"^\.attempt-(?P<profile>robinhood-(?:mainnet|testnet))-"
    r"(?P<attempt>[0-9a-f]{32})-(?P<digest>[0-9a-f]{64})\.json$"
)
_PROFILE_CHAINS = {
    "robinhood-mainnet": 4663,
    "robinhood-testnet": 46630,
}
_ACTION_KINDS = (
    "deployment",
    "configuration",
    "assertion",
    "omission",
    "blocked",
    "deferred",
    "rejected",
    "tooling-only",
)
_ACTION_STATUSES = (
    "planned",
    "submitted",
    "confirmed",
    "finality-pending",
    "reconciled",
    "failed",
    "blocked",
    "complete",
)
_NON_EXECUTABLE_KINDS = {
    "omission",
    "blocked",
    "deferred",
    "rejected",
    "tooling-only",
}
_VALUE_TYPES = (
    "boolean",
    "uint256",
    "int256",
    "address",
    "bytes",
    "bytes32",
    "string",
    "address-array",
    "uint256-array",
    "bytes32-array",
)
_FORBIDDEN_FIELD_NAMES = {
    "account",
    "account_backend",
    "authorization",
    "calldata",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "endpoint",
    "env",
    "environment",
    "exception",
    "exception_class",
    "exception_text",
    "from",
    "header",
    "headers",
    "keystore",
    "message",
    "mnemonic",
    "nonce",
    "password",
    "private_key",
    "provider",
    "provider_payload",
    "raw_transaction",
    "rpc",
    "rpc_url",
    "seed",
    "seed_phrase",
    "signature",
    "signed_transaction",
    "signer",
    "stderr",
    "stdout",
    "token",
    "traceback",
    "unsigned_transaction",
    "url",
}
_SENSITIVE_STRING_PATTERNS = (
    re.compile(r"://", re.ASCII),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----", re.ASCII),
    re.compile(r"(?:api[_-]?key|password|private[_-]?key|seed[_-]?phrase)=", re.I),
    re.compile(r"^(?:/Users/|/home/|[A-Za-z]:[\\/]|\\\\|~[/\\])"),
    re.compile(r"Traceback \(most recent call last\):"),
)
_MAX_INT = (1 << 256) - 1
_MIN_INT = -(1 << 255)


class ManifestError(ValueError):
    """A stable, sanitized H-06 validation or filesystem error."""

    def __init__(self, code: str):
        if not re.fullmatch(r"H06_[A-Z0-9_]+", code):
            raise ValueError("invalid H-06 error code")
        self.code = code
        super().__init__(code)


class HistoryState(str, Enum):
    VALID = "valid"
    ABSENT_CLEAN = "absent-clean"
    INCOMPLETE = "incomplete"
    CORRUPT = "corrupt"
    STALE = "stale"
    WRONG_PROFILE = "wrong-profile"
    WRONG_CHAIN = "wrong-chain"
    WRONG_PLAN = "wrong-plan"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class HistoryReadResult:
    state: HistoryState
    code: str
    records: tuple[Mapping[str, Any], ...] = ()
    head: Mapping[str, Any] | None = None
    current_index: Mapping[str, Any] | None = None
    action_ids: tuple[str, ...] = ()


class WriteState(str, Enum):
    DURABLE = "durable"
    ALREADY_PRESENT = "already-present"
    PRE_PUBLICATION_FAILURE = "pre-publication-failure"
    COLLISION = "collision"
    PUBLICATION_AMBIGUITY = "publication-ambiguity"
    CLEANUP_AMBIGUITY = "cleanup-ambiguity"
    DURABILITY_AMBIGUITY = "durability-ambiguity"
    FINAL_IDENTITY_MISMATCH = "final-identity-mismatch"
    STALE_PRIOR = "stale-prior"


@dataclass(frozen=True)
class WriteResult:
    state: WriteState
    code: str
    basename: str | None
    digest: str | None

    @property
    def succeeded(self) -> bool:
        return self.state in {
            WriteState.DURABLE,
            WriteState.ALREADY_PRESENT,
        }


def _string(
    *,
    pattern: str | None = None,
    enum: Sequence[str] | None = None,
    const: str | None = None,
    min_length: int | None = None,
) -> dict[str, Any]:
    schema: dict[str, Any] = {"type": "string"}
    if pattern is not None:
        schema["pattern"] = pattern
    if enum is not None:
        schema["enum"] = list(enum)
    if const is not None:
        schema["const"] = const
    if min_length is not None:
        schema["minLength"] = min_length
    return schema


def _integer(
    *, minimum: int = 0, maximum: int = _MAX_INT
) -> dict[str, Any]:
    return {
        "type": "integer",
        "minimum": minimum,
        "maximum": maximum,
    }


def _nullable(schema: Mapping[str, Any]) -> dict[str, Any]:
    return {"oneOf": [copy.deepcopy(dict(schema)), {"type": "null"}]}


def _array(
    items: Mapping[str, Any],
    *,
    min_items: int | None = None,
    unique: bool = False,
) -> dict[str, Any]:
    schema: dict[str, Any] = {"type": "array", "items": dict(items)}
    if min_items is not None:
        schema["minItems"] = min_items
    if unique:
        schema["uniqueItems"] = True
    return schema


def _closed(
    properties: Mapping[str, Mapping[str, Any]],
    *,
    required: Sequence[str] | None = None,
) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            key: copy.deepcopy(dict(value))
            for key, value in properties.items()
        },
        "required": list(required if required is not None else properties),
        "additionalProperties": False,
    }


def _typed_value_schema() -> dict[str, Any]:
    value_schema: dict[str, Mapping[str, Any]] = {
        "boolean": {"type": "boolean"},
        "uint256": _integer(),
        "int256": _integer(
            minimum=_MIN_INT, maximum=(1 << 255) - 1
        ),
        "address": _string(pattern=_PUBLIC_ADDRESS),
        "bytes": _string(pattern=_PUBLIC_BYTES),
        "bytes32": _string(pattern=_PUBLIC_BYTES32),
        "string": _string(),
        "address-array": _array(_string(pattern=_PUBLIC_ADDRESS)),
        "uint256-array": _array(_integer()),
        "bytes32-array": _array(_string(pattern=_PUBLIC_BYTES32)),
    }
    branches: list[dict[str, Any]] = []
    for type_name in _VALUE_TYPES:
        branches.append(
            _closed(
                {
                    "state": _string(const="known"),
                    "type": _string(const=type_name),
                    "value": value_schema[type_name],
                }
            )
        )
        branches.append(
            _closed(
                {
                    "state": _string(const="explicit-null"),
                    "type": _string(const=type_name),
                    "value": {"type": "null"},
                }
            )
        )
        for state_name in ("unknown", "not-applicable"):
            branches.append(
                _closed(
                    {
                        "state": _string(const=state_name),
                        "type": _string(const=type_name),
                        "value": {"type": "null"},
                        "reason_code": _string(
                            pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
                        ),
                    }
                )
            )
    return {"oneOf": branches}


def _request_identity_schema() -> dict[str, Any]:
    return {
        "oneOf": [
            _closed(
                {
                    "state": _string(const="known"),
                    "semantic_request_id": _string(pattern=_ACTION_ID),
                    "plan_action_sha256": _string(pattern=_HEX64),
                }
            ),
            _closed(
                {
                    "state": _string(const="not-applicable"),
                    "semantic_request_id": {"type": "null"},
                    "plan_action_sha256": {"type": "null"},
                    "reason_code": _string(
                        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
                    ),
                }
            ),
        ]
    }


def _submission_schema() -> dict[str, Any]:
    return {
        "oneOf": [
            _closed(
                {
                    "status": _string(const="submitted"),
                    "transaction_hash": _string(pattern=_PUBLIC_BYTES32),
                }
            ),
            *[
                _closed(
                    {
                        "status": _string(const=status_name),
                        "transaction_hash": {"type": "null"},
                    }
                )
                for status_name in ("not-applicable", "planned")
            ],
        ]
    }


def _receipt_schema() -> dict[str, Any]:
    confirmed = _closed(
        {
            "status": _string(const="confirmed"),
            "transaction_hash": _string(pattern=_PUBLIC_BYTES32),
            "block_number": _integer(),
            "block_hash": _string(pattern=_PUBLIC_BYTES32),
            "success": {"type": "boolean"},
            "gas_used": _integer(),
            "cumulative_gas_used": {"$ref": "#/$defs/typedValue"},
        }
    )
    empty = []
    for status_name in ("not-applicable", "pending"):
        empty.append(
            _closed(
                {
                    "status": _string(const=status_name),
                    "transaction_hash": {"type": "null"},
                    "block_number": {"type": "null"},
                    "block_hash": {"type": "null"},
                    "success": {"type": "null"},
                    "gas_used": {"type": "null"},
                    "cumulative_gas_used": {
                        "$ref": "#/$defs/typedValue"
                    },
                }
            )
        )
    return {"oneOf": [confirmed, *empty]}


def _finality_schema() -> dict[str, Any]:
    properties = {
        "status": _string(
            enum=("not-applicable", "pending", "complete", "failed")
        ),
        "policy_id": _nullable(_string()),
        "required_confirmations": _nullable(_integer()),
        "required_finality_tag": {"$ref": "#/$defs/typedValue"},
        "observed_confirmations": _nullable(_integer()),
        "observation_block_number": _nullable(_integer()),
        "observation_block_hash": _nullable(
            _string(pattern=_PUBLIC_BYTES32)
        ),
    }
    return _closed(properties)


def _reconciliation_schema() -> dict[str, Any]:
    return _closed(
        {
            "status": _string(
                enum=("not-applicable", "pending", "reconciled", "failed")
            ),
            "observation_source_code": _nullable(
                _string(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
            ),
            "check_ids": _array(
                _string(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"),
                unique=True,
            ),
        }
    )


def build_manifest_schema() -> dict[str, Any]:
    """Return the complete authoritative deployment-manifest v2 schema."""

    profile = _closed(
        {
            "profile_id": _string(enum=tuple(_PROFILE_CHAINS)),
            "expected_chain_id": _integer(minimum=1),
        }
    )
    source_member = _closed(
        {
            "path": _string(min_length=1),
            "sha256": _string(pattern=_HEX64),
        }
    )
    source = _closed(
        {
            "commit": _string(pattern=_HEX40),
            "tree": _string(pattern=_HEX40),
            "plan_sha256": _string(pattern=_HEX64),
            "source_set_sha256": _string(pattern=_HEX64),
            "members": _array(
                {"$ref": "#/$defs/sourceMember"}, min_items=1
            ),
        }
    )
    plan_source = _closed(
        {
            "commit": _string(pattern=_HEX40),
            "tree": _string(pattern=_HEX40),
            "source_set_sha256": _string(pattern=_HEX64),
            "members": _array(
                {"$ref": "#/$defs/sourceMember"}, min_items=1
            ),
        }
    )
    disposition = _closed(
        {
            "code": _string(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"),
            "authority_ref": _string(
                pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$"
            ),
            "explanation_digest_sha256": _string(pattern=_HEX64),
        }
    )
    expected_postcondition = _closed(
        {
            "postcondition_id": _string(pattern=_SLUG),
            "kind": _string(
                enum=(
                    "code-hash",
                    "storage-value",
                    "role-membership",
                    "configuration-value",
                    "balance",
                    "assertion",
                )
            ),
            "subject": _string(
                pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$"
            ),
            "value": {"$ref": "#/$defs/typedValue"},
        }
    )
    observation = _closed(
        {
            "method_code": _string(
                pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
            ),
            "block_number": _nullable(_integer()),
            "block_hash": _nullable(_string(pattern=_PUBLIC_BYTES32)),
        }
    )
    observed_postcondition = _closed(
        {
            "postcondition_id": _string(pattern=_SLUG),
            "value": {"$ref": "#/$defs/typedValue"},
            "observation": {"$ref": "#/$defs/observation"},
            "status": _string(
                enum=("matched", "mismatched", "unknown", "not-applicable")
            ),
        }
    )
    event_field = _closed(
        {
            "name": _string(
                pattern=r"^[A-Za-z_][A-Za-z0-9_]*$"
            ),
            "value": {"$ref": "#/$defs/typedValue"},
        }
    )
    event = _closed(
        {
            "event_id": _string(pattern=_SLUG),
            "log_index": _integer(),
            "emitter": _string(pattern=_PUBLIC_ADDRESS),
            "signature_topic": _nullable(
                _string(pattern=_PUBLIC_BYTES32)
            ),
            "fields": _array({"$ref": "#/$defs/eventField"}),
            "event_evidence_sha256": _string(pattern=_HEX64),
        }
    )
    event_projection = _closed(
        {
            "expected_chain_id": _integer(minimum=1),
            "transaction_hash": _string(pattern=_PUBLIC_BYTES32),
            "block_number": _integer(),
            "block_hash": _string(pattern=_PUBLIC_BYTES32),
            "log_index": _integer(),
            "emitter": _string(pattern=_PUBLIC_ADDRESS),
            "topics": _array(_string(pattern=_PUBLIC_BYTES32)),
            "data": _string(pattern=_PUBLIC_BYTES),
        }
    )
    supersedes = _closed(
        {
            "record_sha256": _string(pattern=_HEX64),
            "action_id": _string(pattern=_ACTION_ID),
            "postcondition_id": {"$ref": "#/$defs/typedValue"},
            "reason_code": _string(
                pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
            ),
            "authority_ref": _string(
                pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$"
            ),
        }
    )
    transaction = _closed(
        {
            "required": {"type": "boolean"},
            "request_identity": {"$ref": "#/$defs/requestIdentity"},
            "submission": {"$ref": "#/$defs/submission"},
            "receipt": {"$ref": "#/$defs/receipt"},
            "finality": {"$ref": "#/$defs/finality"},
            "reconciliation": {"$ref": "#/$defs/reconciliation"},
        }
    )
    action = _closed(
        {
            "action_id": _string(pattern=_ACTION_ID),
            "ordinal": _integer(),
            "semantic_action_id": _string(pattern=_SLUG),
            "kind": _string(enum=_ACTION_KINDS),
            "required": {"type": "boolean"},
            "status": _string(enum=_ACTION_STATUSES),
            "expected_postconditions": _array(
                {"$ref": "#/$defs/expectedPostcondition"}
            ),
            "observed_postconditions": _array(
                {"$ref": "#/$defs/observedPostcondition"}
            ),
            "transaction": {"$ref": "#/$defs/transaction"},
            "events": _array({"$ref": "#/$defs/event"}),
            "supersedes": _array({"$ref": "#/$defs/supersedes"}),
            "disposition": _nullable(
                {"$ref": "#/$defs/disposition"}
            ),
            "error": _nullable({"$ref": "#/$defs/error"}),
        }
    )
    error = _closed(
        {
            "code": _string(pattern=r"^H06_[A-Z0-9_]+$"),
            "phase": _string(
                enum=(
                    "validate",
                    "read",
                    "write",
                    "publish",
                    "durability",
                    "promote",
                    "reconcile",
                )
            ),
            "action_id": _nullable(_string(pattern=_ACTION_ID)),
        }
    )
    step = _closed(
        {
            "migration_id": _string(pattern=_MIGRATION_ID),
            "semantic_step_id": _string(pattern=_SLUG),
            "ordinal": _integer(),
            "previous_record_id": _nullable(
                _string(pattern=_RECORD_ID)
            ),
            "previous_record_sha256": _nullable(
                _string(pattern=_HEX64)
            ),
            "status": _string(
                enum=(
                    "planned",
                    "submitted",
                    "confirmed",
                    "finality-pending",
                    "reconciled",
                    "failed",
                    "blocked",
                    "complete",
                )
            ),
            "actions": _array({"$ref": "#/$defs/action"}),
        }
    )
    plan_state = _closed(
        {
            "plan_sha256": _string(pattern=_HEX64),
            "predecessor_plan_sha256": _nullable(
                _string(pattern=_HEX64)
            ),
            "completed_step_ids": _array(
                _string(pattern=_SLUG), unique=True
            ),
            "remaining_required_step_ids": _array(
                _string(pattern=_SLUG), unique=True
            ),
            "status": _string(
                enum=("in-progress", "complete", "failed", "blocked", "ambiguous")
            ),
        }
    )
    plan_action = _closed(
        {
            "action_id": _string(pattern=_ACTION_ID),
            "semantic_action_id": _string(pattern=_SLUG),
            "ordinal": _integer(),
            "kind": _string(enum=_ACTION_KINDS),
            "required": {"type": "boolean"},
            "transaction_required": {"type": "boolean"},
            "expected_postconditions": _array(
                {"$ref": "#/$defs/expectedPostcondition"}
            ),
            "supersedes": _array({"$ref": "#/$defs/supersedes"}),
            "disposition": _nullable(
                {"$ref": "#/$defs/disposition"}
            ),
        }
    )
    plan_step = _closed(
        {
            "migration_id": _string(pattern=_MIGRATION_ID),
            "semantic_step_id": _string(pattern=_SLUG),
            "ordinal": _integer(),
            "required": {"type": "boolean"},
            "actions": _array({"$ref": "#/$defs/planAction"}),
        }
    )
    semantic_plan = _closed(
        {
            "profile": {"$ref": "#/$defs/profile"},
            "source": {"$ref": "#/$defs/planSource"},
            "steps": _array(
                {"$ref": "#/$defs/planStep"}, min_items=1
            ),
        }
    )
    immutable = _closed(
        {
            "schema": _string(const=SCHEMA_ID),
            "schema_version": {
                "type": "integer",
                "const": SCHEMA_VERSION,
            },
            "artifact_kind": _string(const="immutable_step_record"),
            "record_id": _string(pattern=_RECORD_ID),
            "record_sha256": _string(pattern=_HEX64),
            "profile": {"$ref": "#/$defs/profile"},
            "source": {"$ref": "#/$defs/source"},
            "step": {"$ref": "#/$defs/step"},
            "plan_state": {"$ref": "#/$defs/planState"},
        }
    )
    attempt = _closed(
        {
            "schema": _string(const=SCHEMA_ID),
            "schema_version": {
                "type": "integer",
                "const": SCHEMA_VERSION,
            },
            "artifact_kind": _string(const="attempt_record"),
            "attempt_id": _string(pattern=_HEX32),
            "attempt_sha256": _string(pattern=_HEX64),
            "base_record_id": _nullable(
                _string(pattern=_RECORD_ID)
            ),
            "base_record_sha256": _nullable(
                _string(pattern=_HEX64)
            ),
            "retention_class": _string(
                enum=(
                    "success-7d",
                    "failure-30d",
                    "ambiguity-until-resolved-30d",
                )
            ),
            "profile": {"$ref": "#/$defs/profile"},
            "source": {"$ref": "#/$defs/source"},
            "step": {"$ref": "#/$defs/step"},
            "plan_state": {"$ref": "#/$defs/planState"},
        }
    )
    index_source = _closed(
        {
            "commit": _string(pattern=_HEX40),
            "tree": _string(pattern=_HEX40),
            "plan_sha256": _string(pattern=_HEX64),
        }
    )
    index_target = _closed(
        {
            "path": _string(min_length=1),
            "record_id": _string(pattern=_RECORD_ID),
            "record_sha256": _string(pattern=_HEX64),
        }
    )
    current_index = _closed(
        {
            "schema": _string(const=SCHEMA_ID),
            "schema_version": {
                "type": "integer",
                "const": SCHEMA_VERSION,
            },
            "artifact_kind": _string(const="current_index"),
            "index_sha256": _string(pattern=_HEX64),
            "profile": {"$ref": "#/$defs/profile"},
            "source": {"$ref": "#/$defs/indexSource"},
            "target": {"$ref": "#/$defs/indexTarget"},
            "prior_index_sha256": _nullable(
                _string(pattern=_HEX64)
            ),
            "plan_status": _string(const="complete"),
        }
    )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://ripe.finance/schemas/deployment-manifest-v2.schema.json",
        "title": "Ripe Robinhood deployment manifest v2",
        "oneOf": [
            {"$ref": "#/$defs/immutableStepRecord"},
            {"$ref": "#/$defs/attemptRecord"},
            {"$ref": "#/$defs/currentIndex"},
        ],
        "$defs": {
            "action": action,
            "attemptRecord": attempt,
            "currentIndex": current_index,
            "disposition": disposition,
            "error": error,
            "event": event,
            "eventEvidenceProjection": event_projection,
            "eventField": event_field,
            "expectedPostcondition": expected_postcondition,
            "finality": _finality_schema(),
            "immutableStepRecord": immutable,
            "indexSource": index_source,
            "indexTarget": index_target,
            "observation": observation,
            "observedPostcondition": observed_postcondition,
            "planAction": plan_action,
            "planSource": plan_source,
            "planState": plan_state,
            "planStep": plan_step,
            "profile": profile,
            "receipt": _receipt_schema(),
            "reconciliation": _reconciliation_schema(),
            "requestIdentity": _request_identity_schema(),
            "semanticPlan": semantic_plan,
            "source": source,
            "sourceMember": source_member,
            "step": step,
            "submission": _submission_schema(),
            "supersedes": supersedes,
            "transaction": transaction,
            "typedValue": _typed_value_schema(),
        },
        "additionalProperties": False,
    }


def _json_type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return False


def _schema_at_ref(root: Mapping[str, Any], reference: str) -> Mapping[str, Any]:
    if not reference.startswith("#/"):
        raise ManifestError("H06_SCHEMA_UNSUPPORTED_REF")
    current: Any = root
    for component in reference[2:].split("/"):
        component = component.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, Mapping) or component not in current:
            raise ManifestError("H06_SCHEMA_INVALID_REF")
        current = current[component]
    if not isinstance(current, Mapping):
        raise ManifestError("H06_SCHEMA_INVALID_REF")
    return current


def _validate_against_schema(
    value: Any,
    schema: Mapping[str, Any],
    root: Mapping[str, Any],
) -> None:
    if "$ref" in schema:
        _validate_against_schema(
            value, _schema_at_ref(root, schema["$ref"]), root
        )
        return
    if "oneOf" in schema:
        matches = 0
        for branch in schema["oneOf"]:
            try:
                _validate_against_schema(value, branch, root)
            except ManifestError:
                continue
            matches += 1
        if matches != 1:
            raise ManifestError("H06_SCHEMA_ONE_OF")
        return
    if "const" in schema and value != schema["const"]:
        raise ManifestError("H06_SCHEMA_CONST")
    if "enum" in schema and value not in schema["enum"]:
        raise ManifestError("H06_SCHEMA_ENUM")
    expected_type = schema.get("type")
    if expected_type is not None:
        if not _json_type_matches(value, expected_type):
            raise ManifestError("H06_SCHEMA_TYPE")
    if expected_type == "object":
        properties = schema.get("properties", {})
        required = schema.get("required", ())
        for key in required:
            if key not in value:
                raise ManifestError("H06_SCHEMA_REQUIRED")
        if schema.get("additionalProperties") is False:
            if any(key not in properties for key in value):
                raise ManifestError("H06_SCHEMA_ADDITIONAL_PROPERTY")
        for key, child in value.items():
            if key in properties:
                _validate_against_schema(child, properties[key], root)
    elif expected_type == "array":
        if len(value) < schema.get("minItems", 0):
            raise ManifestError("H06_SCHEMA_MIN_ITEMS")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise ManifestError("H06_SCHEMA_MAX_ITEMS")
        if schema.get("uniqueItems"):
            canonical = [canonical_json_bytes(item) for item in value]
            if len(canonical) != len(set(canonical)):
                raise ManifestError("H06_SCHEMA_UNIQUE_ITEMS")
        for item in value:
            _validate_against_schema(item, schema["items"], root)
    elif expected_type == "string":
        if len(value) < schema.get("minLength", 0):
            raise ManifestError("H06_SCHEMA_MIN_LENGTH")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            raise ManifestError("H06_SCHEMA_PATTERN")
    elif expected_type == "integer":
        if value < schema.get("minimum", _MIN_INT):
            raise ManifestError("H06_SCHEMA_MINIMUM")
        if value > schema.get("maximum", _MAX_INT):
            raise ManifestError("H06_SCHEMA_MAXIMUM")


def _validate_unicode(value: str) -> None:
    if unicodedata.normalize("NFC", value) != value:
        raise ManifestError("H06_UNICODE_NOT_NFC")
    for character in value:
        codepoint = ord(character)
        if 0xD800 <= codepoint <= 0xDFFF:
            raise ManifestError("H06_UNICODE_INVALID_SCALAR")


def _reject_sensitive_material(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = key.casefold().replace("-", "_")
            if normalized in _FORBIDDEN_FIELD_NAMES:
                raise ManifestError("H06_SENSITIVE_FIELD")
            _reject_sensitive_material(child)
    elif isinstance(value, list):
        for child in value:
            _reject_sensitive_material(child)
    elif isinstance(value, str):
        for pattern in _SENSITIVE_STRING_PATTERNS:
            if pattern.search(value):
                raise ManifestError("H06_SENSITIVE_LITERAL")


def _validate_json_domain(value: Any, *, sensitivity: bool = False) -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        if value < _MIN_INT or value > _MAX_INT:
            raise ManifestError("H06_INTEGER_RANGE")
        return
    if isinstance(value, float):
        raise ManifestError("H06_FLOAT_FORBIDDEN")
    if isinstance(value, str):
        _validate_unicode(value)
        return
    if isinstance(value, list):
        for item in value:
            _validate_json_domain(item, sensitivity=sensitivity)
        if sensitivity:
            _reject_sensitive_material(value)
        return
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ManifestError("H06_OBJECT_KEY_TYPE")
            _validate_unicode(key)
            _validate_json_domain(child, sensitivity=sensitivity)
        if sensitivity:
            _reject_sensitive_material(value)
        return
    raise ManifestError("H06_JSON_TYPE")


def _escape_string(value: str) -> bytes:
    pieces = ['"']
    for character in value:
        codepoint = ord(character)
        if character == '"':
            pieces.append('\\"')
        elif character == "\\":
            pieces.append("\\\\")
        elif codepoint <= 0x1F:
            pieces.append(f"\\u00{codepoint:02x}")
        else:
            pieces.append(character)
    pieces.append('"')
    return "".join(pieces).encode("utf-8")


def _emit_canonical(value: Any, output: bytearray) -> None:
    if value is None:
        output.extend(b"null")
    elif value is True:
        output.extend(b"true")
    elif value is False:
        output.extend(b"false")
    elif isinstance(value, int) and not isinstance(value, bool):
        output.extend(str(value).encode("ascii"))
    elif isinstance(value, str):
        output.extend(_escape_string(value))
    elif isinstance(value, list):
        output.extend(b"[")
        for index, item in enumerate(value):
            if index:
                output.extend(b",")
            _emit_canonical(item, output)
        output.extend(b"]")
    elif isinstance(value, dict):
        output.extend(b"{")
        ordered_keys = sorted(value, key=lambda item: item.encode("utf-8"))
        for index, key in enumerate(ordered_keys):
            if index:
                output.extend(b",")
            output.extend(_escape_string(key))
            output.extend(b":")
            _emit_canonical(value[key], output)
        output.extend(b"}")
    else:
        raise ManifestError("H06_JSON_TYPE")


def canonical_json_bytes(value: Any) -> bytes:
    """Return the exact H-06 canonical JSON bytes including one terminal LF."""

    _validate_json_domain(value)
    output = bytearray()
    _emit_canonical(value, output)
    output.extend(b"\n")
    return bytes(output)


def schema_json_bytes() -> bytes:
    return canonical_json_bytes(build_manifest_schema())


def normalize_evidence_path(value: str, *, basename_only: bool = False) -> str:
    _validate_unicode(value)
    if not value or "\\" in value or "\x00" in value:
        raise ManifestError("H06_PATH_INVALID")
    if any(ord(character) < 0x20 for character in value):
        raise ManifestError("H06_PATH_INVALID")
    if value.startswith(("/", "~")) or re.match(r"^[A-Za-z]:", value):
        raise ManifestError("H06_PATH_ABSOLUTE")
    if "://" in value or value.endswith("/"):
        raise ManifestError("H06_PATH_INVALID")
    parts = value.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise ManifestError("H06_PATH_ESCAPE")
    if basename_only and len(parts) != 1:
        raise ManifestError("H06_PATH_NOT_BASENAME")
    normalized = str(PurePosixPath(*parts))
    if normalized != value:
        raise ManifestError("H06_PATH_NONCANONICAL")
    return normalized


def _require_sorted_unique(
    values: Sequence[Any], key: Callable[[Any], Any], code: str
) -> None:
    keys = [key(value) for value in values]
    if keys != sorted(keys) or len(keys) != len(set(keys)):
        raise ManifestError(code)


def _validate_profile(profile: Mapping[str, Any]) -> None:
    expected = _PROFILE_CHAINS.get(profile["profile_id"])
    if expected != profile["expected_chain_id"]:
        raise ManifestError("H06_PROFILE_CHAIN_MISMATCH")


def _validate_typed_value(value: Mapping[str, Any]) -> None:
    state_name = value["state"]
    type_name = value["type"]
    actual = value["value"]
    if state_name == "known":
        if actual is None:
            raise ManifestError("H06_KNOWN_VALUE_NULL")
        if type_name.endswith("-array"):
            canonical = [canonical_json_bytes(item) for item in actual]
            if canonical != sorted(canonical):
                raise ManifestError("H06_VALUE_ARRAY_ORDER")
    elif state_name == "explicit-null":
        if type_name not in _VALUE_TYPES or actual is not None:
            raise ManifestError("H06_EXPLICIT_NULL_TYPE")
    elif actual is not None:
        raise ManifestError("H06_NULL_STATE_VALUE")


def _validate_source(source: Mapping[str, Any], *, has_plan: bool) -> None:
    members = source["members"]
    for member in members:
        normalize_evidence_path(member["path"])
    _require_sorted_unique(
        members,
        lambda member: member["path"].encode("utf-8"),
        "H06_SOURCE_MEMBER_ORDER",
    )
    if source_set_sha256(members) != source["source_set_sha256"]:
        raise ManifestError("H06_SOURCE_SET_MISMATCH")
    if has_plan and source["plan_sha256"] == "0" * 64:
        raise ManifestError("H06_PLAN_HASH_PLACEHOLDER")


def _validate_postconditions(
    expected: Sequence[Mapping[str, Any]],
    observed: Sequence[Mapping[str, Any]],
    *,
    complete: bool,
) -> None:
    _require_sorted_unique(
        expected,
        lambda item: item["postcondition_id"].encode("utf-8"),
        "H06_EXPECTED_POSTCONDITION_ORDER",
    )
    _require_sorted_unique(
        observed,
        lambda item: item["postcondition_id"].encode("utf-8"),
        "H06_OBSERVED_POSTCONDITION_ORDER",
    )
    for item in expected:
        _validate_typed_value(item["value"])
    for item in observed:
        _validate_typed_value(item["value"])
    if complete:
        if [item["postcondition_id"] for item in observed] != [
            item["postcondition_id"] for item in expected
        ]:
            raise ManifestError("H06_POSTCONDITION_IDENTITY")
        if any(item["status"] != "matched" for item in observed):
            raise ManifestError("H06_POSTCONDITION_INCOMPLETE")


def _validate_transaction(
    transaction: Mapping[str, Any],
    *,
    action_id: str,
    complete: bool,
) -> None:
    request = transaction["request_identity"]
    submission = transaction["submission"]
    receipt = transaction["receipt"]
    finality = transaction["finality"]
    reconciliation = transaction["reconciliation"]
    check_ids = reconciliation["check_ids"]
    if check_ids != sorted(check_ids):
        raise ManifestError("H06_RECONCILIATION_CHECK_ORDER")
    _validate_typed_value(receipt["cumulative_gas_used"])
    _validate_typed_value(finality["required_finality_tag"])
    if receipt["cumulative_gas_used"]["type"] != "uint256":
        raise ManifestError("H06_RECEIPT_GAS_TYPE")
    if finality["required_finality_tag"]["type"] != "string":
        raise ManifestError("H06_FINALITY_TAG_TYPE")
    if transaction["required"]:
        if request["state"] != "known":
            raise ManifestError("H06_REQUEST_IDENTITY_INCOMPLETE")
        if request["semantic_request_id"] != action_id:
            raise ManifestError("H06_REQUEST_IDENTITY_MISMATCH")
        if complete:
            if submission["status"] != "submitted":
                raise ManifestError("H06_SUBMISSION_INCOMPLETE")
            if receipt["status"] != "confirmed" or not receipt["success"]:
                raise ManifestError("H06_RECEIPT_INCOMPLETE")
            if receipt["transaction_hash"] != submission["transaction_hash"]:
                raise ManifestError("H06_RECEIPT_TRANSACTION_MISMATCH")
            if finality["status"] != "complete":
                raise ManifestError("H06_FINALITY_INCOMPLETE")
            if finality["policy_id"] != FINALITY_POLICY_ID:
                raise ManifestError("H06_FINALITY_POLICY")
            if finality["required_confirmations"] != 64:
                raise ManifestError("H06_FINALITY_CONFIRMATIONS")
            if finality["required_finality_tag"] != {
                "state": "not-applicable",
                "type": "string",
                "value": None,
                "reason_code": "confirmation-depth-policy",
            }:
                raise ManifestError("H06_FINALITY_TAG_POLICY")
            if finality["observed_confirmations"] is None:
                raise ManifestError("H06_FINALITY_OBSERVATION")
            if finality["observed_confirmations"] < 64:
                raise ManifestError("H06_FINALITY_PENDING")
            if finality["observation_block_number"] is None:
                raise ManifestError("H06_FINALITY_OBSERVATION")
            if (
                finality["observation_block_number"]
                < receipt["block_number"] + 64
            ):
                raise ManifestError("H06_FINALITY_BLOCK_DEPTH")
            if finality["observation_block_hash"] is None:
                raise ManifestError("H06_FINALITY_OBSERVATION")
            if reconciliation["status"] != "reconciled":
                raise ManifestError("H06_RECONCILIATION_INCOMPLETE")
            required_checks = {
                "events",
                "postconditions",
                "profile-chain",
                "receipt-block-identity",
                "receipt-identity",
                "receipt-success",
                "second-observation",
            }
            if set(check_ids) != required_checks:
                raise ManifestError("H06_RECONCILIATION_CHECKS")
    else:
        if request["state"] != "not-applicable":
            raise ManifestError("H06_NON_TRANSACTION_REQUEST")
        if submission["status"] != "not-applicable":
            raise ManifestError("H06_NON_TRANSACTION_SUBMISSION")
        if receipt["status"] != "not-applicable":
            raise ManifestError("H06_NON_TRANSACTION_RECEIPT")
        if finality["status"] != "not-applicable":
            raise ManifestError("H06_NON_TRANSACTION_FINALITY")
        if reconciliation["status"] != "not-applicable":
            raise ManifestError("H06_NON_TRANSACTION_RECONCILIATION")


def _supersedes_key(item: Mapping[str, Any]) -> tuple[str, str, str]:
    postcondition = item["postcondition_id"]
    known = postcondition["value"] if postcondition["state"] == "known" else ""
    return item["record_sha256"], item["action_id"], known


def _validate_action(
    action: Mapping[str, Any],
    migration_id: str,
    ordinal: int,
    *,
    immutable: bool,
) -> None:
    expected_id = (
        f"{migration_id}:{ordinal:06d}:{action['semantic_action_id']}"
    )
    if action["ordinal"] != ordinal or action["action_id"] != expected_id:
        raise ManifestError("H06_ACTION_IDENTITY")
    if action["events"] != sorted(
        action["events"], key=lambda item: item["log_index"]
    ):
        raise ManifestError("H06_EVENT_ORDER")
    if len({item["log_index"] for item in action["events"]}) != len(
        action["events"]
    ):
        raise ManifestError("H06_EVENT_DUPLICATE")
    for event in action["events"]:
        _require_sorted_unique(
            event["fields"],
            lambda field: field["name"].encode("utf-8"),
            "H06_EVENT_FIELD_ORDER",
        )
        for field in event["fields"]:
            _validate_typed_value(field["value"])
    supersedes = action["supersedes"]
    if supersedes != sorted(supersedes, key=_supersedes_key):
        raise ManifestError("H06_SUPERSEDES_ORDER")
    for item in supersedes:
        postcondition = item["postcondition_id"]
        _validate_typed_value(postcondition)
        if postcondition["type"] != "string":
            raise ManifestError("H06_SUPERSEDES_POSTCONDITION_TYPE")
        if postcondition["state"] not in ("known", "not-applicable"):
            raise ManifestError("H06_SUPERSEDES_POSTCONDITION_STATE")
    non_executable = action["kind"] in _NON_EXECUTABLE_KINDS
    if non_executable:
        if action["transaction"]["required"]:
            raise ManifestError("H06_NON_EXECUTABLE_TRANSACTION")
        if action["disposition"] is None:
            raise ManifestError("H06_DISPOSITION_REQUIRED")
        if not action["expected_postconditions"]:
            raise ManifestError("H06_NON_EXECUTABLE_EFFECT_REQUIRED")
        if any(
            item["value"]["state"] != "not-applicable"
            for item in action["expected_postconditions"]
        ):
            raise ManifestError("H06_NON_EXECUTABLE_EFFECT")
        if immutable:
            if [
                item["postcondition_id"]
                for item in action["observed_postconditions"]
            ] != [
                item["postcondition_id"]
                for item in action["expected_postconditions"]
            ]:
                raise ManifestError("H06_NON_EXECUTABLE_EFFECT")
            if any(
                item["status"] != "not-applicable"
                or item["value"]["state"] != "not-applicable"
                for item in action["observed_postconditions"]
            ):
                raise ManifestError("H06_NON_EXECUTABLE_EFFECT")
    elif action["required"] and not action["expected_postconditions"]:
        raise ManifestError("H06_POSTCONDITION_REQUIRED")
    complete = immutable and action["required"] and not non_executable
    _validate_postconditions(
        action["expected_postconditions"],
        action["observed_postconditions"],
        complete=complete,
    )
    _validate_transaction(
        action["transaction"],
        action_id=action["action_id"],
        complete=complete and action["transaction"]["required"],
    )
    if (
        not immutable
        and action["transaction"]["required"]
        and not non_executable
    ):
        transaction = action["transaction"]
        status_name = action["status"]
        if status_name == "planned":
            if (
                transaction["submission"]["status"] != "planned"
                or transaction["receipt"]["status"] != "pending"
                or transaction["finality"]["status"] != "pending"
                or transaction["reconciliation"]["status"] != "pending"
            ):
                raise ManifestError("H06_ACTION_STATUS_INCONSISTENT")
        elif status_name == "submitted":
            if (
                transaction["submission"]["status"] != "submitted"
                or transaction["receipt"]["status"] != "pending"
                or transaction["finality"]["status"] != "pending"
                or transaction["reconciliation"]["status"] != "pending"
            ):
                raise ManifestError("H06_ACTION_STATUS_INCONSISTENT")
        elif status_name in ("confirmed", "finality-pending"):
            if (
                transaction["submission"]["status"] != "submitted"
                or transaction["receipt"]["status"] != "confirmed"
                or not transaction["receipt"]["success"]
                or transaction["finality"]["status"] != "pending"
                or transaction["reconciliation"]["status"] != "pending"
            ):
                raise ManifestError("H06_ACTION_STATUS_INCONSISTENT")
        elif status_name in ("reconciled", "complete"):
            _validate_transaction(
                transaction,
                action_id=action["action_id"],
                complete=True,
            )
            _validate_postconditions(
                action["expected_postconditions"],
                action["observed_postconditions"],
                complete=True,
            )
        elif status_name == "failed":
            if action["error"] is None:
                raise ManifestError("H06_FAILED_ERROR_REQUIRED")
        elif status_name == "blocked":
            if action["error"] is None and action["disposition"] is None:
                raise ManifestError("H06_BLOCKED_REASON_REQUIRED")
    if complete and action["transaction"]["required"]:
        finality = action["transaction"]["finality"]
        for observed in action["observed_postconditions"]:
            observation = observed["observation"]
            if (
                observation["block_number"]
                != finality["observation_block_number"]
                or observation["block_hash"]
                != finality["observation_block_hash"]
            ):
                raise ManifestError(
                    "H06_POSTCONDITION_FINALITY_IDENTITY"
                )
    if action["error"] is not None and (
        action["error"]["action_id"] != action["action_id"]
    ):
        raise ManifestError("H06_ERROR_ACTION_IDENTITY")
    if immutable:
        if action["error"] is not None:
            raise ManifestError("H06_COMPLETE_ERROR")
        if action["required"] and action["status"] not in (
            "reconciled",
            "complete",
        ):
            raise ManifestError("H06_ACTION_INCOMPLETE")
        if action["kind"] == "blocked" and action["required"]:
            raise ManifestError("H06_REQUIRED_BLOCKED_ACTION")


def _validate_artifact_semantics(value: Mapping[str, Any]) -> None:
    _validate_profile(value["profile"])
    kind = value["artifact_kind"]
    if kind == "current_index":
        normalize_evidence_path(value["target"]["path"], basename_only=True)
        match = _IMMUTABLE_NAME.fullmatch(value["target"]["path"])
        if match is None:
            raise ManifestError("H06_INDEX_TARGET_NAME")
        if match.group("digest") != value["target"]["record_sha256"]:
            raise ManifestError("H06_INDEX_TARGET_HASH")
        if value["source"]["plan_sha256"] not in value["target"]["record_id"]:
            raise ManifestError("H06_INDEX_PLAN_IDENTITY")
        return
    _validate_source(value["source"], has_plan=True)
    step = value["step"]
    plan_state = value["plan_state"]
    if value["source"]["plan_sha256"] != plan_state["plan_sha256"]:
        raise ManifestError("H06_PLAN_IDENTITY")
    previous_pair = (
        step["previous_record_id"],
        step["previous_record_sha256"],
    )
    if (previous_pair[0] is None) != (previous_pair[1] is None):
        raise ManifestError("H06_PRIOR_IDENTITY")
    if kind == "attempt_record":
        if (
            value["base_record_id"],
            value["base_record_sha256"],
        ) != previous_pair:
            raise ManifestError("H06_ATTEMPT_BASE_IDENTITY")
    immutable = kind == "immutable_step_record"
    if immutable:
        expected_record_id = (
            f"{value['profile']['profile_id']}:"
            f"{value['source']['plan_sha256']}:"
            f"{step['migration_id']}:{step['semantic_step_id']}"
        )
        if value["record_id"] != expected_record_id:
            raise ManifestError("H06_RECORD_IDENTITY")
        if step["status"] != "complete":
            raise ManifestError("H06_STEP_INCOMPLETE")
        if plan_state["status"] not in ("in-progress", "complete"):
            raise ManifestError("H06_PLAN_STATE_INCOMPLETE")
    for ordinal, action in enumerate(step["actions"]):
        _validate_action(
            action,
            step["migration_id"],
            ordinal,
            immutable=immutable,
        )
    if kind == "attempt_record":
        required_statuses = {
            action["status"]
            for action in step["actions"]
            if action["required"]
        }
        if step["status"] == "complete" and not required_statuses <= {
            "reconciled",
            "complete",
        }:
            raise ManifestError("H06_STEP_STATUS_INCONSISTENT")
        if step["status"] == "failed" and "failed" not in required_statuses:
            raise ManifestError("H06_STEP_STATUS_INCONSISTENT")
        if (
            step["status"] == "finality-pending"
            and "finality-pending" not in required_statuses
        ):
            raise ManifestError("H06_STEP_STATUS_INCONSISTENT")
        if step["status"] == "blocked" and "blocked" not in required_statuses:
            raise ManifestError("H06_STEP_STATUS_INCONSISTENT")
    for key in ("completed_step_ids", "remaining_required_step_ids"):
        values = plan_state[key]
        if values != sorted(values):
            raise ManifestError("H06_PLAN_STEP_ORDER")
    if set(plan_state["completed_step_ids"]) & set(
        plan_state["remaining_required_step_ids"]
    ):
        raise ManifestError("H06_PLAN_STEP_OVERLAP")
    if immutable and step["semantic_step_id"] not in plan_state[
        "completed_step_ids"
    ]:
        raise ManifestError("H06_STEP_NOT_COMPLETED")
    if plan_state["status"] == "complete":
        if plan_state["remaining_required_step_ids"]:
            raise ManifestError("H06_TERMINAL_PLAN_REMAINING")


def validate_manifest(value: Any) -> Mapping[str, Any]:
    _validate_json_domain(value, sensitivity=True)
    if not isinstance(value, dict):
        raise ManifestError("H06_SCHEMA_TYPE")
    schema = build_manifest_schema()
    _validate_against_schema(value, schema, schema)
    _validate_artifact_semantics(value)
    return value


def validate_semantic_plan(value: Any) -> Mapping[str, Any]:
    _validate_json_domain(value, sensitivity=True)
    if not isinstance(value, dict):
        raise ManifestError("H06_SCHEMA_TYPE")
    schema = build_manifest_schema()
    _validate_against_schema(
        value, schema["$defs"]["semanticPlan"], schema
    )
    _validate_profile(value["profile"])
    _validate_source(value["source"], has_plan=False)
    step_ids: set[str] = set()
    migration_ids: set[str] = set()
    for ordinal, step in enumerate(value["steps"]):
        if step["ordinal"] != ordinal:
            raise ManifestError("H06_PLAN_STEP_ORDINAL")
        if (
            step["semantic_step_id"] in step_ids
            or step["migration_id"] in migration_ids
        ):
            raise ManifestError("H06_PLAN_STEP_IDENTITY")
        step_ids.add(step["semantic_step_id"])
        migration_ids.add(step["migration_id"])
        for action_ordinal, action in enumerate(step["actions"]):
            expected = (
                f"{step['migration_id']}:{action_ordinal:06d}:"
                f"{action['semantic_action_id']}"
            )
            if action["ordinal"] != action_ordinal:
                raise ManifestError("H06_PLAN_ACTION_ORDINAL")
            if action["action_id"] != expected:
                raise ManifestError("H06_PLAN_ACTION_IDENTITY")
            _validate_postconditions(
                action["expected_postconditions"], (), complete=False
            )
            if action["supersedes"] != sorted(
                action["supersedes"], key=_supersedes_key
            ):
                raise ManifestError("H06_SUPERSEDES_ORDER")
            non_executable = action["kind"] in _NON_EXECUTABLE_KINDS
            if non_executable != (not action["transaction_required"]):
                if action["kind"] != "assertion":
                    raise ManifestError("H06_PLAN_TRANSACTION_POLICY")
            if non_executable and action["disposition"] is None:
                raise ManifestError("H06_DISPOSITION_REQUIRED")
            if non_executable and (
                not action["expected_postconditions"]
                or any(
                    item["value"]["state"] != "not-applicable"
                    for item in action["expected_postconditions"]
                )
            ):
                raise ManifestError("H06_NON_EXECUTABLE_EFFECT")
    return value


def load_json_bytes(data: bytes) -> Any:
    try:
        return json_file.loads_strict(
            data,
            min_integer=_MIN_INT,
            max_integer=_MAX_INT,
        )
    except (UnicodeDecodeError, ValueError) as error:
        raise ManifestError("H06_JSON_PARSE") from error


def parse_canonical_manifest(data: bytes) -> Mapping[str, Any]:
    value = load_json_bytes(data)
    validate_manifest(value)
    if canonical_json_bytes(value) != data:
        raise ManifestError("H06_CANONICAL_BYTES")
    verify_self_hash(value)
    return value


def _self_hash_field(value: Mapping[str, Any]) -> str:
    kind = value.get("artifact_kind")
    fields = {
        "immutable_step_record": "record_sha256",
        "attempt_record": "attempt_sha256",
        "current_index": "index_sha256",
    }
    try:
        return fields[kind]
    except KeyError as error:
        raise ManifestError("H06_ARTIFACT_KIND") from error


def compute_self_hash(value: Mapping[str, Any]) -> str:
    field = _self_hash_field(value)
    if field not in value or value[field] is None:
        raise ManifestError("H06_SELF_HASH_FIELD")
    unsigned = copy.deepcopy(dict(value))
    del unsigned[field]
    return hashlib.sha256(canonical_json_bytes(unsigned)).hexdigest()


def seal_artifact(value: Mapping[str, Any]) -> dict[str, Any]:
    sealed = copy.deepcopy(dict(value))
    field = _self_hash_field(sealed)
    if field not in sealed:
        raise ManifestError("H06_SELF_HASH_FIELD")
    sealed[field] = "0" * 64
    validate_manifest(sealed)
    sealed[field] = compute_self_hash(sealed)
    validate_manifest(sealed)
    return sealed


def verify_self_hash(value: Mapping[str, Any]) -> None:
    field = _self_hash_field(value)
    expected = compute_self_hash(value)
    if not hmac.compare_digest(value[field], expected):
        raise ManifestError("H06_SELF_HASH_MISMATCH")


def source_set_sha256(members: Sequence[Mapping[str, Any]]) -> str:
    if not members:
        raise ManifestError("H06_SOURCE_SET_EMPTY")
    normalized: list[tuple[str, str]] = []
    for member in members:
        path = normalize_evidence_path(member["path"])
        digest = member["sha256"]
        if re.fullmatch(_HEX64, digest) is None:
            raise ManifestError("H06_SOURCE_MEMBER_HASH")
        normalized.append((path, digest))
    if normalized != sorted(
        normalized, key=lambda item: item[0].encode("utf-8")
    ):
        raise ManifestError("H06_SOURCE_MEMBER_ORDER")
    if len({path for path, _ in normalized}) != len(normalized):
        raise ManifestError("H06_SOURCE_MEMBER_ORDER")
    payload = bytearray(SOURCE_SET_DOMAIN)
    payload.append(0)
    for path, digest in normalized:
        payload.extend(path.encode("utf-8"))
        payload.append(0)
        payload.extend(bytes.fromhex(digest))
        payload.append(0)
    return hashlib.sha256(payload).hexdigest()


def validate_git_source_identity(
    repository_root: str | os.PathLike[str],
    source: Mapping[str, Any],
) -> None:
    """Validate commit/tree/member bytes using only local committed Git data."""

    root = Path(repository_root)
    if not root.is_absolute():
        raise ManifestError("H06_SOURCE_REPOSITORY_UNAVAILABLE")
    try:
        root_info = root.lstat()
    except OSError as error:
        raise ManifestError("H06_SOURCE_REPOSITORY_UNAVAILABLE") from error
    if stat.S_ISLNK(root_info.st_mode) or not stat.S_ISDIR(root_info.st_mode):
        raise ManifestError("H06_SOURCE_REPOSITORY_UNAVAILABLE")
    try:
        root_fd = _open_absolute_directory_no_symlinks(root)
    except (ManifestError, OSError) as error:
        raise ManifestError("H06_SOURCE_REPOSITORY_UNAVAILABLE") from error
    try:
        opened = os.fstat(root_fd)
        if (opened.st_dev, opened.st_ino) != (
            root_info.st_dev,
            root_info.st_ino,
        ):
            raise ManifestError("H06_SOURCE_REPOSITORY_UNAVAILABLE")
    finally:
        os.close(root_fd)
    commit = source["commit"]
    tree = source["tree"]
    try:
        commit_result = subprocess.run(
            ["git", "rev-parse", "--verify", f"{commit}^{{commit}}"],
            cwd=root,
            capture_output=True,
            check=False,
        )
        tree_result = subprocess.run(
            ["git", "rev-parse", f"{commit}^{{tree}}"],
            cwd=root,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise ManifestError("H06_SOURCE_GIT_UNAVAILABLE") from error
    if (
        commit_result.returncode != 0
        or commit_result.stdout.strip() != commit.encode("ascii")
        or tree_result.returncode != 0
        or tree_result.stdout.strip() != tree.encode("ascii")
    ):
        raise ManifestError("H06_SOURCE_GIT_IDENTITY")
    for member in source["members"]:
        path = normalize_evidence_path(member["path"])
        result = subprocess.run(
            ["git", "cat-file", "blob", f"{commit}:{path}"],
            cwd=root,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise ManifestError("H06_SOURCE_MEMBER_MISSING")
        if not hmac.compare_digest(
            hashlib.sha256(result.stdout).hexdigest(),
            member["sha256"],
        ):
            raise ManifestError("H06_SOURCE_MEMBER_MISMATCH")


def plan_sha256(plan: Mapping[str, Any]) -> str:
    validate_semantic_plan(plan)
    payload = PLAN_DOMAIN + b"\x00" + canonical_json_bytes(plan)
    return hashlib.sha256(payload).hexdigest()


def plan_action_sha256(plan_digest: str, action_id: str) -> str:
    if re.fullmatch(_HEX64, plan_digest) is None:
        raise ManifestError("H06_PLAN_HASH")
    if re.fullmatch(_ACTION_ID, action_id) is None:
        raise ManifestError("H06_ACTION_IDENTITY")
    payload = (
        PLAN_ACTION_DOMAIN
        + b"\x00"
        + bytes.fromhex(plan_digest)
        + b"\x00"
        + action_id.encode("utf-8")
    )
    return hashlib.sha256(payload).hexdigest()


_PLAN_ACTION_FIELDS = (
    "action_id",
    "semantic_action_id",
    "ordinal",
    "kind",
    "required",
    "expected_postconditions",
    "supersedes",
    "disposition",
)


def _validated_semantic_plan_map(
    semantic_plans: Sequence[Mapping[str, Any]],
) -> dict[str, Mapping[str, Any]]:
    if (
        isinstance(semantic_plans, (str, bytes, bytearray, Mapping))
        or not isinstance(semantic_plans, Sequence)
        or not semantic_plans
    ):
        raise ManifestError("H06_PLAN_PROOF_REQUIRED")
    validated: dict[str, Mapping[str, Any]] = {}
    for plan in semantic_plans:
        validate_semantic_plan(plan)
        digest = plan_sha256(plan)
        if digest in validated:
            raise ManifestError("H06_PLAN_PROOF_DUPLICATE")
        validated[digest] = plan
    return validated


def _plan_for_digest(
    plans: Mapping[str, Mapping[str, Any]],
    digest: str,
) -> Mapping[str, Any]:
    plan = plans.get(digest)
    if plan is None:
        if len(plans) == 1:
            raise ManifestError("H06_PLAN_HASH_MISMATCH")
        raise ManifestError("H06_PLAN_PROOF_REQUIRED")
    return plan


def _result_action_semantics(
    action: Mapping[str, Any],
) -> dict[str, Any]:
    result = {
        key: copy.deepcopy(action[key])
        for key in _PLAN_ACTION_FIELDS
    }
    result["transaction_required"] = action["transaction"]["required"]
    return result


def _required_plan_step_ids(
    plan: Mapping[str, Any],
) -> tuple[str, ...]:
    return tuple(
        step["semantic_step_id"]
        for step in plan["steps"]
        if step["required"]
    )


def _validate_plan_state_binding(
    artifact: Mapping[str, Any],
    plan: Mapping[str, Any],
    plan_step: Mapping[str, Any],
) -> None:
    state = artifact["plan_state"]
    required_ids = _required_plan_step_ids(plan)
    required_set = set(required_ids)
    completed = state["completed_step_ids"]
    remaining = state["remaining_required_step_ids"]
    completed_set = set(completed)
    remaining_set = set(remaining)
    if len(completed) != len(completed_set) or len(remaining) != len(
        remaining_set
    ):
        raise ManifestError("H06_PLAN_STATE_DUPLICATE_STEP")
    if (
        completed != sorted(completed)
        or remaining != sorted(remaining)
        or completed_set & remaining_set
    ):
        raise ManifestError("H06_PLAN_STATE_MISMATCH")
    if not completed_set <= required_set or not remaining_set <= required_set:
        raise ManifestError("H06_PLAN_STATE_UNKNOWN_STEP")
    if completed_set | remaining_set != required_set:
        raise ManifestError("H06_PLAN_STATE_MISMATCH")

    step = artifact["step"]
    step_complete = (
        artifact["artifact_kind"] == "immutable_step_record"
        or step["status"] == "complete"
    )
    expected_completed = {
        candidate["semantic_step_id"]
        for candidate in plan["steps"]
        if candidate["required"]
        and (
            candidate["ordinal"] < plan_step["ordinal"]
            or (
                candidate["ordinal"] == plan_step["ordinal"]
                and step_complete
            )
        )
    }
    expected_remaining = required_set - expected_completed
    if completed != sorted(expected_completed) or remaining != sorted(
        expected_remaining
    ):
        raise ManifestError("H06_PLAN_STATE_MISMATCH")

    if artifact["artifact_kind"] == "immutable_step_record":
        if not plan_step["required"]:
            raise ManifestError("H06_PLAN_STEP_NOT_REQUIRED")
        expected_status = (
            "complete" if not expected_remaining else "in-progress"
        )
        if state["status"] != expected_status:
            raise ManifestError("H06_PLAN_STATE_MISMATCH")
    elif state["status"] == "complete" and expected_remaining:
        raise ManifestError("H06_PLAN_STATE_MISMATCH")
    elif state["status"] == "complete" and not step_complete:
        raise ManifestError("H06_PLAN_STATE_MISMATCH")


def _validate_artifact_plan_binding(
    artifact: Mapping[str, Any],
    plans: Mapping[str, Mapping[str, Any]],
) -> None:
    digest = artifact["source"]["plan_sha256"]
    plan = _plan_for_digest(plans, digest)
    if plan_sha256(plan) != digest:
        raise ManifestError("H06_PLAN_HASH_MISMATCH")
    if artifact["profile"] != plan["profile"]:
        raise ManifestError("H06_PLAN_PROFILE_MISMATCH")
    expected_source = {
        **copy.deepcopy(plan["source"]),
        "plan_sha256": digest,
    }
    if artifact["source"] != expected_source:
        raise ManifestError("H06_PLAN_SOURCE_MISMATCH")

    step = artifact["step"]
    ordinal = step["ordinal"]
    if ordinal >= len(plan["steps"]):
        raise ManifestError("H06_PLAN_STEP_UNKNOWN")
    plan_step = plan["steps"][ordinal]
    if (
        step["migration_id"] != plan_step["migration_id"]
        or step["semantic_step_id"] != plan_step["semantic_step_id"]
        or ordinal != plan_step["ordinal"]
    ):
        raise ManifestError("H06_PLAN_STEP_IDENTITY")
    if len(step["actions"]) != len(plan_step["actions"]):
        raise ManifestError("H06_PLAN_ACTION_UNKNOWN")
    for action, plan_action in zip(
        step["actions"], plan_step["actions"], strict=True
    ):
        if action["action_id"] != plan_action["action_id"]:
            raise ManifestError("H06_PLAN_ACTION_UNKNOWN")
        if _result_action_semantics(action) != plan_action:
            raise ManifestError("H06_PLAN_ACTION_MISMATCH")
        transaction = action["transaction"]
        if transaction["required"]:
            expected_action_hash = plan_action_sha256(
                digest, action["action_id"]
            )
            supplied_action_hash = transaction["request_identity"][
                "plan_action_sha256"
            ]
            if not isinstance(
                supplied_action_hash, str
            ) or not hmac.compare_digest(
                supplied_action_hash, expected_action_hash
            ):
                raise ManifestError("H06_PLAN_ACTION_HASH")
    _validate_plan_state_binding(artifact, plan, plan_step)


def _validate_index_plan_binding(
    index: Mapping[str, Any],
    plans: Mapping[str, Mapping[str, Any]],
) -> None:
    digest = index["source"]["plan_sha256"]
    plan = _plan_for_digest(plans, digest)
    if index["profile"] != plan["profile"]:
        raise ManifestError("H06_PLAN_PROFILE_MISMATCH")
    if index["source"] != {
        "commit": plan["source"]["commit"],
        "tree": plan["source"]["tree"],
        "plan_sha256": digest,
    }:
        raise ManifestError("H06_PLAN_SOURCE_MISMATCH")


def _validate_chain_plan_binding(
    chain: Sequence[Mapping[str, Any]],
    plans: Mapping[str, Mapping[str, Any]],
) -> None:
    prior: Mapping[str, Any] | None = None
    for record in chain:
        _validate_artifact_plan_binding(record, plans)
        if prior is not None:
            prior_digest = prior["source"]["plan_sha256"]
            current_digest = record["source"]["plan_sha256"]
            if current_digest == prior_digest:
                prior_completed = set(
                    prior["plan_state"]["completed_step_ids"]
                )
                current_completed = set(
                    record["plan_state"]["completed_step_ids"]
                )
                prior_remaining = set(
                    prior["plan_state"]["remaining_required_step_ids"]
                )
                current_remaining = set(
                    record["plan_state"]["remaining_required_step_ids"]
                )
                current_step = record["step"]["semantic_step_id"]
                if (
                    not prior_completed < current_completed
                    or current_completed - prior_completed != {current_step}
                    or not current_remaining < prior_remaining
                    or prior_remaining - current_remaining != {current_step}
                ):
                    raise ManifestError("H06_PLAN_STATE_TRANSITION")
            elif prior["plan_state"]["status"] != "complete":
                raise ManifestError("H06_PLAN_TRANSITION_INCOMPLETE")
        prior = record


def _validate_event_projection(
    projection: Mapping[str, Any],
    *,
    profile: Mapping[str, Any],
    submission: Mapping[str, Any],
    receipt: Mapping[str, Any],
    event: Mapping[str, Any],
    allow_anonymous: bool,
) -> None:
    expected_keys = {
        "expected_chain_id",
        "transaction_hash",
        "block_number",
        "block_hash",
        "log_index",
        "emitter",
        "topics",
        "data",
    }
    if set(projection) != expected_keys:
        raise ManifestError("H06_EVENT_PROJECTION_KEYS")
    _validate_json_domain(projection)
    schema = build_manifest_schema()
    _validate_against_schema(
        projection,
        schema["$defs"]["eventEvidenceProjection"],
        schema,
    )
    for key in ("transaction_hash", "block_hash"):
        if not isinstance(projection[key], str) or re.fullmatch(
            _PUBLIC_BYTES32, projection[key]
        ) is None:
            raise ManifestError("H06_EVENT_HEX")
    if not isinstance(projection["emitter"], str) or re.fullmatch(
        _PUBLIC_ADDRESS, projection["emitter"]
    ) is None:
        raise ManifestError("H06_EVENT_HEX")
    if not isinstance(projection["data"], str) or re.fullmatch(
        _PUBLIC_BYTES, projection["data"]
    ) is None:
        raise ManifestError("H06_EVENT_HEX")
    topics = projection["topics"]
    if not isinstance(topics, list):
        raise ManifestError("H06_EVENT_TOPICS")
    if any(
        not isinstance(topic, str)
        or re.fullmatch(_PUBLIC_BYTES32, topic) is None
        for topic in topics
    ):
        raise ManifestError("H06_EVENT_TOPICS")
    for key in ("expected_chain_id", "block_number", "log_index"):
        if (
            not isinstance(projection[key], int)
            or isinstance(projection[key], bool)
            or projection[key] < (1 if key == "expected_chain_id" else 0)
        ):
            raise ManifestError("H06_EVENT_INTEGER")
    _validate_profile(profile)
    if projection["expected_chain_id"] != profile["expected_chain_id"]:
        raise ManifestError("H06_EVENT_CHAIN_MISMATCH")
    if submission.get("status") != "submitted":
        raise ManifestError("H06_EVENT_SUBMISSION_LINK")
    if receipt.get("status") != "confirmed":
        raise ManifestError("H06_EVENT_RECEIPT_LINK")
    if projection["transaction_hash"] != submission.get("transaction_hash"):
        raise ManifestError("H06_EVENT_TRANSACTION_MISMATCH")
    for projection_key, receipt_key in (
        ("transaction_hash", "transaction_hash"),
        ("block_number", "block_number"),
        ("block_hash", "block_hash"),
    ):
        if projection[projection_key] != receipt.get(receipt_key):
            raise ManifestError("H06_EVENT_RECEIPT_MISMATCH")
    if projection["log_index"] != event.get("log_index"):
        raise ManifestError("H06_EVENT_LOG_INDEX_MISMATCH")
    if projection["emitter"] != event.get("emitter"):
        raise ManifestError("H06_EVENT_EMITTER_MISMATCH")
    if projection["topics"] != event.get("topics"):
        raise ManifestError("H06_EVENT_TOPICS_MISMATCH")
    if projection["data"] != event.get("data"):
        raise ManifestError("H06_EVENT_DATA_MISMATCH")
    signature_topic = event.get("signature_topic")
    if topics:
        if signature_topic != topics[0]:
            raise ManifestError("H06_EVENT_SIGNATURE_TOPIC")
    elif not allow_anonymous or signature_topic is not None:
        raise ManifestError("H06_EVENT_SIGNATURE_TOPIC")


def event_evidence_sha256(
    projection: Mapping[str, Any],
    *,
    profile: Mapping[str, Any],
    submission: Mapping[str, Any],
    receipt: Mapping[str, Any],
    event: Mapping[str, Any],
    allow_anonymous: bool = False,
) -> str:
    _validate_event_projection(
        projection,
        profile=profile,
        submission=submission,
        receipt=receipt,
        event=event,
        allow_anonymous=allow_anonymous,
    )
    payload = (
        EVENT_EVIDENCE_DOMAIN
        + b"\x00"
        + canonical_json_bytes(projection)
    )
    return hashlib.sha256(payload).hexdigest()


def immutable_basename(record: Mapping[str, Any]) -> str:
    if record.get("artifact_kind") != "immutable_step_record":
        raise ManifestError("H06_ARTIFACT_KIND")
    return (
        f"{record['step']['migration_id']}-"
        f"{record['step']['semantic_step_id']}-"
        f"{record['record_sha256']}.manifest-v2.json"
    )


def attempt_basename(record: Mapping[str, Any]) -> str:
    if record.get("artifact_kind") != "attempt_record":
        raise ManifestError("H06_ARTIFACT_KIND")
    return (
        f".attempt-{record['profile']['profile_id']}-"
        f"{record['attempt_id']}-{record['attempt_sha256']}.json"
    )


def _open_absolute_directory_no_symlinks(root: Path) -> int:
    if not root.is_absolute():
        raise ManifestError("H06_HISTORY_ROOT_ABSOLUTE_REQUIRED")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    directory_fd = os.open("/", flags)
    try:
        for component in root.parts[1:]:
            if component in ("", ".", ".."):
                raise ManifestError("H06_PATH_ESCAPE")
            child_fd = os.open(component, flags, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = child_fd
        return directory_fd
    except Exception:
        os.close(directory_fd)
        raise


def _load_canonical_file_at(
    directory_fd: int, basename: str
) -> tuple[Mapping[str, Any], bytes, os.stat_result]:
    normalize_evidence_path(basename, basename_only=True)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(basename, flags, dir_fd=directory_fd)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise ManifestError("H06_PATH_NOT_REGULAR")
        data = json_file.read_all(fd)
        after = os.fstat(fd)
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
        ):
            raise ManifestError("H06_FILE_IDENTITY_CHANGED")
        return parse_canonical_manifest(data), data, after
    finally:
        os.close(fd)


def _root_lstat(root: Path) -> os.stat_result:
    try:
        info = root.lstat()
    except FileNotFoundError as error:
        raise ManifestError("H06_HISTORY_ROOT_ABSENT") from error
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise ManifestError("H06_HISTORY_ROOT_INVALID")
    return info


def _validate_lock_identity(directory_fd: int, lock_fd: int) -> None:
    parent = os.fstat(directory_fd)
    held = os.fstat(lock_fd)
    try:
        entry = os.stat(
            ".manifest-v2.lock",
            dir_fd=directory_fd,
            follow_symlinks=False,
        )
    except FileNotFoundError:
        raise ManifestError("H06_LOCK_INVALID")
    if (
        not stat.S_ISREG(held.st_mode)
        or not stat.S_ISREG(entry.st_mode)
        or stat.S_IMODE(held.st_mode) != 0o600
        or stat.S_IMODE(entry.st_mode) != 0o600
        or held.st_uid != os.geteuid()
        or entry.st_uid != os.geteuid()
        or held.st_nlink != 1
        or entry.st_nlink != 1
        or held.st_dev != parent.st_dev
        or (entry.st_dev, entry.st_ino) != (held.st_dev, held.st_ino)
    ):
        raise ManifestError("H06_LOCK_INVALID")


def _read_lock_state(directory_fd: int) -> tuple[int | None, bool]:
    try:
        fd = os.open(
            ".manifest-v2.lock",
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=directory_fd,
        )
    except FileNotFoundError:
        return None, False
    except OSError as error:
        raise ManifestError("H06_LOCK_INVALID") from error
    try:
        _validate_lock_identity(directory_fd, fd)
        fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        return None, True
    except Exception:
        os.close(fd)
        raise
    _validate_lock_identity(directory_fd, fd)
    return fd, False


def _chain_records(
    records_by_hash: Mapping[str, Mapping[str, Any]]
) -> tuple[Mapping[str, Any], ...]:
    if not records_by_hash:
        return ()
    referenced: set[str] = set()
    for record in records_by_hash.values():
        previous = record["step"]["previous_record_sha256"]
        if previous is not None:
            if previous not in records_by_hash:
                raise ManifestError("H06_PRIOR_RECORD_MISSING")
            referenced.add(previous)
    heads = set(records_by_hash) - referenced
    if len(heads) != 1:
        raise ManifestError("H06_MULTIPLE_HEADS")
    ordered: list[Mapping[str, Any]] = []
    seen: set[str] = set()
    current = records_by_hash[next(iter(heads))]
    while True:
        digest = current["record_sha256"]
        if digest in seen:
            raise ManifestError("H06_CHAIN_CYCLE")
        seen.add(digest)
        ordered.append(current)
        previous = current["step"]["previous_record_sha256"]
        if previous is None:
            break
        prior = records_by_hash[previous]
        if current["step"]["previous_record_id"] != prior["record_id"]:
            raise ManifestError("H06_PRIOR_RECORD_ID")
        if current["profile"] != prior["profile"]:
            raise ManifestError("H06_CHAIN_PROFILE")
        current_plan = current["source"]["plan_sha256"]
        prior_plan = prior["source"]["plan_sha256"]
        if current_plan == prior_plan:
            if current["source"] != prior["source"]:
                raise ManifestError("H06_CHAIN_SOURCE")
            if (
                current["plan_state"]["predecessor_plan_sha256"]
                != prior["plan_state"]["predecessor_plan_sha256"]
            ):
                raise ManifestError("H06_CHAIN_PREDECESSOR_PLAN")
        else:
            if current["step"]["ordinal"] != 0:
                raise ManifestError("H06_PLAN_TRANSITION_ORDINAL")
            if prior["plan_state"]["status"] != "complete":
                raise ManifestError("H06_PLAN_TRANSITION_INCOMPLETE")
            if (
                current["plan_state"]["predecessor_plan_sha256"]
                != prior_plan
            ):
                raise ManifestError("H06_PLAN_TRANSITION_IDENTITY")
        current = prior
    if len(seen) != len(records_by_hash):
        raise ManifestError("H06_MULTIPLE_HEADS")
    ordered.reverse()
    record_ids = [record["record_id"] for record in ordered]
    if len(record_ids) != len(set(record_ids)):
        raise ManifestError("H06_DUPLICATE_RECORD_ID")
    genesis = ordered[0]
    if genesis["step"]["previous_record_sha256"] is not None:
        raise ManifestError("H06_GENESIS_PRIOR")
    if genesis["plan_state"]["predecessor_plan_sha256"] is not None:
        raise ManifestError("H06_GENESIS_PREDECESSOR_PLAN")
    seen_action_ids: set[str] = set()
    plan_ordinals: dict[str, list[int]] = {}
    completed_plan_segments: set[str] = set()
    active_plan: str | None = None
    for record_index, record in enumerate(ordered):
        record_plan = record["source"]["plan_sha256"]
        if active_plan is None:
            active_plan = record_plan
        elif record_plan != active_plan:
            completed_plan_segments.add(active_plan)
            if record_plan in completed_plan_segments:
                raise ManifestError("H06_PLAN_REENTRY")
            active_plan = record_plan
        plan_ordinals.setdefault(record_plan, []).append(
            record["step"]["ordinal"]
        )
        ancestor_records = {
            ancestor["record_sha256"]: ancestor
            for ancestor in ordered[:record_index]
        }
        for action in record["step"]["actions"]:
            if action["action_id"] in seen_action_ids:
                raise ManifestError("H06_DUPLICATE_ACTION_ID")
            seen_action_ids.add(action["action_id"])
            for reference in action["supersedes"]:
                referenced_record = ancestor_records.get(
                    reference["record_sha256"]
                )
                if referenced_record is None:
                    raise ManifestError("H06_SUPERSEDES_ANCESTRY")
                referenced_action = next(
                    (
                        candidate
                        for candidate in referenced_record["step"]["actions"]
                        if candidate["action_id"] == reference["action_id"]
                    ),
                    None,
                )
                if referenced_action is None:
                    raise ManifestError("H06_SUPERSEDES_ACTION")
                postcondition = reference["postcondition_id"]
                if postcondition["state"] == "known":
                    postcondition_ids = {
                        candidate["postcondition_id"]
                        for candidate in (
                            referenced_action["expected_postconditions"]
                            + referenced_action["observed_postconditions"]
                        )
                    }
                    if postcondition["value"] not in postcondition_ids:
                        raise ManifestError("H06_SUPERSEDES_POSTCONDITION")
    for ordinals in plan_ordinals.values():
        if ordinals != list(range(len(ordinals))):
            raise ManifestError("H06_PLAN_STEP_ORDINAL")
    return tuple(ordered)


def _scan_history(
    root: Path,
    *,
    take_shared_lock: bool,
) -> tuple[
    tuple[Mapping[str, Any], ...],
    Mapping[str, Any] | None,
    tuple[Mapping[str, Any], ...],
    bool,
]:
    info = _root_lstat(root)
    if info.st_uid != os.geteuid():
        raise ManifestError("H06_HISTORY_ROOT_OWNER")
    if stat.S_IMODE(info.st_mode) != 0o700:
        raise ManifestError("H06_HISTORY_ROOT_MODE")
    directory_fd = _open_absolute_directory_no_symlinks(root)
    lock_fd: int | None = None
    try:
        if take_shared_lock:
            lock_fd, held = _read_lock_state(directory_fd)
            if held:
                raise ManifestError("H06_LOCK_HELD")
        records_by_hash: dict[str, Mapping[str, Any]] = {}
        attempts: list[Mapping[str, Any]] = []
        current_index: Mapping[str, Any] | None = None
        operational = False
        for basename in sorted(os.listdir(directory_fd)):
            if basename == ".manifest-v2.lock":
                continue
            match = _IMMUTABLE_NAME.fullmatch(basename)
            attempt_match = _ATTEMPT_NAME.fullmatch(basename)
            if match:
                record, _, _ = _load_canonical_file_at(
                    directory_fd, basename
                )
                if record["artifact_kind"] != "immutable_step_record":
                    raise ManifestError("H06_FILENAME_ARTIFACT_KIND")
                if match.group("migration_id") != record["step"]["migration_id"]:
                    raise ManifestError("H06_FILENAME_IDENTITY")
                if match.group("step_id") != record["step"]["semantic_step_id"]:
                    raise ManifestError("H06_FILENAME_IDENTITY")
                if match.group("digest") != record["record_sha256"]:
                    raise ManifestError("H06_FILENAME_IDENTITY")
                if record["record_sha256"] in records_by_hash:
                    raise ManifestError("H06_DUPLICATE_RECORD_HASH")
                records_by_hash[record["record_sha256"]] = record
            elif attempt_match:
                attempt, _, _ = _load_canonical_file_at(
                    directory_fd, basename
                )
                if attempt["artifact_kind"] != "attempt_record":
                    raise ManifestError("H06_FILENAME_ARTIFACT_KIND")
                if (
                    attempt_match.group("profile")
                    != attempt["profile"]["profile_id"]
                    or attempt_match.group("attempt") != attempt["attempt_id"]
                    or attempt_match.group("digest")
                    != attempt["attempt_sha256"]
                ):
                    raise ManifestError("H06_FILENAME_IDENTITY")
                attempts.append(attempt)
            elif basename == "current-manifest.json":
                if current_index is not None:
                    raise ManifestError("H06_DUPLICATE_CURRENT")
                current_index, _, _ = _load_canonical_file_at(
                    directory_fd, basename
                )
                if current_index["artifact_kind"] != "current_index":
                    raise ManifestError("H06_FILENAME_ARTIFACT_KIND")
            elif ".tmp." in basename:
                operational = True
            else:
                raise ManifestError("H06_HISTORY_UNKNOWN_FILE")
        chain = _chain_records(records_by_hash)
        for attempt in attempts:
            base_hash = attempt["base_record_sha256"]
            if base_hash is None:
                if chain:
                    genesis = chain[0]
                    if (
                        attempt["profile"] != genesis["profile"]
                        or attempt["source"] != genesis["source"]
                        or attempt["step"]["migration_id"]
                        != genesis["step"]["migration_id"]
                        or attempt["step"]["semantic_step_id"]
                        != genesis["step"]["semantic_step_id"]
                    ):
                        raise ManifestError("H06_ATTEMPT_BASE_MISSING")
                continue
            base = records_by_hash.get(base_hash)
            if base is None:
                raise ManifestError("H06_ATTEMPT_BASE_MISSING")
            if attempt["base_record_id"] != base["record_id"]:
                raise ManifestError("H06_ATTEMPT_BASE_IDENTITY")
            if attempt["profile"] != base["profile"]:
                raise ManifestError("H06_ATTEMPT_BASE_PROFILE")
        return chain, current_index, tuple(attempts), operational
    finally:
        if lock_fd is not None:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            os.close(lock_fd)
        os.close(directory_fd)


def _attempt_is_unresolved(attempt: Mapping[str, Any]) -> bool:
    return (
        attempt["step"]["status"] != "complete"
        or attempt["plan_state"]["status"] != "complete"
        or any(
            action["required"]
            and action["status"] not in ("reconciled", "complete")
            for action in attempt["step"]["actions"]
        )
    )


def read_history(
    configured_profile_id: str,
    configured_expected_chain_id: int,
    expected_plan_sha256: str,
    expected_source_commit: str,
    expected_source_tree: str,
    configured_history_root: str | os.PathLike[str],
) -> HistoryReadResult:
    """Read and classify a Robinhood v2 history without any write or repair."""

    root = Path(configured_history_root)
    try:
        root.lstat()
    except FileNotFoundError:
        return HistoryReadResult(
            HistoryState.ABSENT_CLEAN, "H06_HISTORY_ABSENT_CLEAN"
        )
    except OSError:
        return HistoryReadResult(
            HistoryState.CORRUPT, "H06_HISTORY_IO_FAILURE"
        )
    try:
        chain, current, attempts, operational = _scan_history(
            root, take_shared_lock=True
        )
    except OSError:
        return HistoryReadResult(
            HistoryState.CORRUPT, "H06_HISTORY_IO_FAILURE"
        )
    except ManifestError as error:
        if error.code == "H06_LOCK_HELD":
            return HistoryReadResult(
                HistoryState.AMBIGUOUS, "H06_HISTORY_LOCKED"
            )
        if error.code == "H06_MULTIPLE_HEADS":
            return HistoryReadResult(
                HistoryState.AMBIGUOUS, "H06_HISTORY_MULTIPLE_HEADS"
            )
        return HistoryReadResult(HistoryState.CORRUPT, error.code)
    if not chain:
        if attempts or operational:
            return HistoryReadResult(
                HistoryState.INCOMPLETE, "H06_HISTORY_ATTEMPT_ONLY"
            )
        if current is not None:
            return HistoryReadResult(
                HistoryState.CORRUPT, "H06_CURRENT_WITHOUT_HISTORY"
            )
        return HistoryReadResult(
            HistoryState.ABSENT_CLEAN, "H06_HISTORY_ABSENT_CLEAN"
        )
    head = chain[-1]
    profile = head["profile"]
    if profile["profile_id"] != configured_profile_id:
        return HistoryReadResult(
            HistoryState.WRONG_PROFILE,
            "H06_HISTORY_WRONG_PROFILE",
            records=chain,
            head=head,
        )
    if profile["expected_chain_id"] != configured_expected_chain_id:
        return HistoryReadResult(
            HistoryState.WRONG_CHAIN,
            "H06_HISTORY_WRONG_CHAIN",
            records=chain,
            head=head,
        )
    active_plan = head["source"]["plan_sha256"]
    if active_plan != expected_plan_sha256:
        return HistoryReadResult(
            HistoryState.WRONG_PLAN,
            "H06_HISTORY_WRONG_PLAN",
            records=chain,
            head=head,
        )
    if (
        head["source"]["commit"] != expected_source_commit
        or head["source"]["tree"] != expected_source_tree
    ):
        return HistoryReadResult(
            HistoryState.CORRUPT,
            "H06_HISTORY_PLAN_SOURCE_INCONSISTENT",
            records=chain,
            head=head,
        )
    if current is None:
        state = HistoryState.INCOMPLETE
        code = "H06_HISTORY_CURRENT_ABSENT"
    else:
        if current["profile"] != head["profile"]:
            return HistoryReadResult(
                HistoryState.CORRUPT,
                "H06_CURRENT_PROFILE_INCONSISTENT",
                records=chain,
                head=head,
                current_index=current,
            )
        target_hash = current["target"]["record_sha256"]
        record_hashes = {record["record_sha256"] for record in chain}
        if target_hash not in record_hashes:
            return HistoryReadResult(
                HistoryState.CORRUPT,
                "H06_CURRENT_TARGET_MISSING",
                records=chain,
                head=head,
                current_index=current,
            )
        target = next(
            record for record in chain
            if record["record_sha256"] == target_hash
        )
        if current["target"]["record_id"] != target["record_id"]:
            return HistoryReadResult(
                HistoryState.CORRUPT,
                "H06_CURRENT_TARGET_IDENTITY",
                records=chain,
                head=head,
                current_index=current,
            )
        if current["target"]["path"] != immutable_basename(target):
            return HistoryReadResult(
                HistoryState.CORRUPT,
                "H06_CURRENT_TARGET_PATH",
                records=chain,
                head=head,
                current_index=current,
            )
        if current["source"] != {
            "commit": target["source"]["commit"],
            "tree": target["source"]["tree"],
            "plan_sha256": target["source"]["plan_sha256"],
        }:
            return HistoryReadResult(
                HistoryState.CORRUPT,
                "H06_CURRENT_SOURCE_INCONSISTENT",
                records=chain,
                head=head,
                current_index=current,
            )
        if target_hash != head["record_sha256"]:
            return HistoryReadResult(
                HistoryState.STALE,
                "H06_HISTORY_STALE_CURRENT",
                records=chain,
                head=head,
                current_index=current,
            )
        if (
            head["plan_state"]["status"] == "complete"
            and not any(_attempt_is_unresolved(item) for item in attempts)
            and not operational
        ):
            state = HistoryState.VALID
            code = "H06_HISTORY_VALID"
        else:
            state = HistoryState.INCOMPLETE
            code = "H06_HISTORY_INCOMPLETE"
    action_ids = tuple(
        action["action_id"]
        for record in chain
        for action in record["step"]["actions"]
    )
    return HistoryReadResult(
        state,
        code,
        records=chain,
        head=head,
        current_index=current,
        action_ids=action_ids,
    )


class _DarwinStatFs(ctypes.Structure):
    _fields_ = [
        ("f_bsize", ctypes.c_uint32),
        ("f_iosize", ctypes.c_int32),
        ("f_blocks", ctypes.c_uint64),
        ("f_bfree", ctypes.c_uint64),
        ("f_bavail", ctypes.c_uint64),
        ("f_files", ctypes.c_uint64),
        ("f_ffree", ctypes.c_uint64),
        ("f_fsid", ctypes.c_int32 * 2),
        ("f_owner", ctypes.c_uint32),
        ("f_type", ctypes.c_uint32),
        ("f_flags", ctypes.c_uint32),
        ("f_fssubtype", ctypes.c_uint32),
        ("f_fstypename", ctypes.c_char * 16),
        ("f_mntonname", ctypes.c_char * 1024),
        ("f_mntfromname", ctypes.c_char * 1024),
        ("f_flags_ext", ctypes.c_uint32),
        ("f_reserved", ctypes.c_uint32 * 7),
    ]


class _NativeMacOS:
    def __init__(self) -> None:
        if sys.platform != "darwin":
            raise ManifestError("H06_PLATFORM_UNSUPPORTED")
        self.libc = ctypes.CDLL(None, use_errno=True)
        try:
            self.renameatx_np = self.libc.renameatx_np
            self.fstatfs = self.libc.fstatfs
        except AttributeError as error:
            raise ManifestError("H06_NATIVE_PRIMITIVE_UNAVAILABLE") from error
        self.renameatx_np.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        self.renameatx_np.restype = ctypes.c_int
        self.fstatfs.argtypes = [
            ctypes.c_int,
            ctypes.POINTER(_DarwinStatFs),
        ]
        self.fstatfs.restype = ctypes.c_int

    def require_apfs(self, directory_fd: int) -> None:
        info = _DarwinStatFs()
        if self.fstatfs(directory_fd, ctypes.byref(info)) != 0:
            error_number = ctypes.get_errno()
            raise ManifestError("H06_FILESYSTEM_IDENTITY_FAILED") from OSError(
                error_number, os.strerror(error_number)
            )
        filesystem = bytes(info.f_fstypename).split(b"\x00", 1)[0]
        if filesystem != b"apfs":
            raise ManifestError("H06_FILESYSTEM_UNSUPPORTED")

    def publish_exclusive(
        self,
        directory_fd: int,
        temporary_basename: str,
        final_basename: str,
    ) -> None:
        result = self.renameatx_np(
            directory_fd,
            temporary_basename.encode("utf-8"),
            directory_fd,
            final_basename.encode("utf-8"),
            RENAME_EXCL,
        )
        if result != 0:
            error_number = ctypes.get_errno()
            raise OSError(error_number, os.strerror(error_number))

    @staticmethod
    def full_fsync(fd: int) -> None:
        fcntl.fcntl(fd, F_FULLFSYNC)


def _checkpoint(
    fault: Callable[[str], None] | None, name: str
) -> None:
    if fault is not None:
        fault(name)


def _validate_root_for_write(root: Path) -> tuple[int, _NativeMacOS]:
    if not root.is_absolute():
        raise ManifestError("H06_HISTORY_ROOT_ABSOLUTE_REQUIRED")
    info = _root_lstat(root)
    if info.st_uid != os.geteuid():
        raise ManifestError("H06_HISTORY_ROOT_OWNER")
    if stat.S_IMODE(info.st_mode) != 0o700:
        raise ManifestError("H06_HISTORY_ROOT_MODE")
    lowered_parts = {part.casefold() for part in root.parts}
    prohibited = {
        "dropbox",
        "icloud drive",
        "mobile documents",
        "onedrive",
    }
    if lowered_parts & prohibited or (
        len(root.parts) > 1 and root.parts[1] == "Volumes"
    ):
        raise ManifestError("H06_STORAGE_LOCATION_UNSUPPORTED")
    directory_fd = _open_absolute_directory_no_symlinks(root)
    native = _NativeMacOS()
    try:
        native.require_apfs(directory_fd)
        opened = os.fstat(directory_fd)
        if (
            opened.st_dev,
            opened.st_ino,
        ) != (
            info.st_dev,
            info.st_ino,
        ):
            raise ManifestError("H06_HISTORY_ROOT_IDENTITY")
    except Exception:
        os.close(directory_fd)
        raise
    return directory_fd, native


def _acquire_writer_lock(directory_fd: int) -> int:
    base_flags = os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
    for attempt in range(8):
        try:
            fd = os.open(
                ".manifest-v2.lock",
                base_flags | os.O_CREAT | os.O_EXCL,
                0o600,
                dir_fd=directory_fd,
            )
            break
        except FileExistsError:
            try:
                fd = os.open(
                    ".manifest-v2.lock",
                    base_flags,
                    dir_fd=directory_fd,
                )
                break
            except FileNotFoundError:
                if attempt == 7:
                    raise
                continue
        except InterruptedError:
            continue
    else:
        raise ManifestError("H06_LOCK_CREATE_RACE")
    info = os.fstat(fd)
    if (
        not stat.S_ISREG(info.st_mode)
        or stat.S_IMODE(info.st_mode) != 0o600
        or info.st_uid != os.geteuid()
    ):
        os.close(fd)
        raise ManifestError("H06_LOCK_INVALID")
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            break
        except InterruptedError:
            continue
    _validate_lock_identity(directory_fd, fd)
    return fd


def _existing_current_index(
    directory_fd: int,
) -> Mapping[str, Any] | None:
    try:
        value, _, _ = _load_canonical_file_at(
            directory_fd, "current-manifest.json"
        )
    except FileNotFoundError:
        return None
    if value["artifact_kind"] != "current_index":
        raise ManifestError("H06_CURRENT_KIND")
    return value


def _cleanup_temporary(
    directory_fd: int,
    temporary_basename: str,
    fault: Callable[[str], None] | None,
    expected_info: os.stat_result | None = None,
) -> bool:
    try:
        _checkpoint(fault, "before_cleanup")
        if expected_info is not None:
            entry = os.stat(
                temporary_basename,
                dir_fd=directory_fd,
                follow_symlinks=False,
            )
            if (
                not stat.S_ISREG(entry.st_mode)
                or entry.st_nlink != 1
                or (entry.st_dev, entry.st_ino)
                != (expected_info.st_dev, expected_info.st_ino)
            ):
                return False
        os.unlink(temporary_basename, dir_fd=directory_fd)
        os.fsync(directory_fd)
        _checkpoint(fault, "after_cleanup")
        return True
    except FileNotFoundError:
        return True
    except OSError:
        return False


def _write_temporary(
    directory_fd: int,
    final_basename: str,
    data: bytes,
    native: _NativeMacOS,
    fault: Callable[[str], None] | None,
) -> tuple[int, str, os.stat_result]:
    for _ in range(8):
        suffix = secrets.token_hex(16)
        temporary = f".{final_basename}.tmp.{suffix}"
        try:
            fd = os.open(
                temporary,
                os.O_RDWR
                | os.O_CREAT
                | os.O_EXCL
                | getattr(os, "O_NOFOLLOW", 0),
                0o600,
                dir_fd=directory_fd,
            )
            break
        except FileExistsError:
            continue
    else:
        raise ManifestError("H06_TEMP_NAME_COLLISION")
    try:
        info = os.fstat(fd)
        if (
            not stat.S_ISREG(info.st_mode)
            or stat.S_IMODE(info.st_mode) != 0o600
            or info.st_nlink != 1
        ):
            raise ManifestError("H06_TEMP_IDENTITY")
        _checkpoint(fault, "after_temp_create")
        json_file.write_all(fd, data)
        _checkpoint(fault, "after_write")
        os.fsync(fd)
        _checkpoint(fault, "after_file_fsync")
        native.full_fsync(fd)
        _checkpoint(fault, "after_file_fullfsync")
        os.lseek(fd, 0, os.SEEK_SET)
        reread = json_file.read_all(fd)
        if reread != data:
            raise ManifestError("H06_TEMP_BYTES_MISMATCH")
        parse_canonical_manifest(reread)
        after = os.fstat(fd)
        if (
            info.st_dev,
            info.st_ino,
            info.st_nlink,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_nlink,
        ):
            raise ManifestError("H06_TEMP_IDENTITY")
        _checkpoint(fault, "after_reread")
        return fd, temporary, after
    except Exception:
        os.close(fd)
        if not _cleanup_temporary(
            directory_fd, temporary, fault, info
        ):
            raise ManifestError("H06_CLEANUP_AMBIGUOUS")
        raise


def _verify_published_identity(
    directory_fd: int,
    final_basename: str,
    held_fd: int,
    expected_info: os.stat_result,
    expected_data: bytes,
) -> None:
    entry = os.stat(
        final_basename,
        dir_fd=directory_fd,
        follow_symlinks=False,
    )
    held = os.fstat(held_fd)
    if not stat.S_ISREG(entry.st_mode) or entry.st_nlink != 1:
        raise ManifestError("H06_FINAL_IDENTITY_MISMATCH")
    identity = (expected_info.st_dev, expected_info.st_ino)
    if (entry.st_dev, entry.st_ino) != identity:
        raise ManifestError("H06_FINAL_IDENTITY_MISMATCH")
    if (held.st_dev, held.st_ino) != identity or held.st_nlink != 1:
        raise ManifestError("H06_FINAL_IDENTITY_MISMATCH")
    os.lseek(held_fd, 0, os.SEEK_SET)
    if json_file.read_all(held_fd) != expected_data:
        raise ManifestError("H06_FINAL_IDENTITY_MISMATCH")
    parsed = parse_canonical_manifest(expected_data)
    expected_digest = parsed[_self_hash_field(parsed)]
    if not hmac.compare_digest(expected_digest, compute_self_hash(parsed)):
        raise ManifestError("H06_FINAL_IDENTITY_MISMATCH")


def _verify_temporary_entry(
    directory_fd: int,
    temporary_basename: str,
    final_basename: str,
    held_fd: int,
    expected_info: os.stat_result,
) -> None:
    if not temporary_basename.startswith(
        f".{final_basename}.tmp."
    ) or re.fullmatch(
        r"[0-9a-f]{32}", temporary_basename.rsplit(".", 1)[-1]
    ) is None:
        raise ManifestError("H06_TEMP_BASENAME")
    entry = os.stat(
        temporary_basename,
        dir_fd=directory_fd,
        follow_symlinks=False,
    )
    held = os.fstat(held_fd)
    identity = (expected_info.st_dev, expected_info.st_ino)
    if (
        not stat.S_ISREG(entry.st_mode)
        or entry.st_nlink != 1
        or (entry.st_dev, entry.st_ino) != identity
        or (held.st_dev, held.st_ino) != identity
        or held.st_nlink != 1
    ):
        raise ManifestError("H06_TEMP_IDENTITY")


def publish_immutable(
    history_root: str | os.PathLike[str],
    artifact: Mapping[str, Any],
    *,
    semantic_plans: Sequence[Mapping[str, Any]],
    expected_prior_record_sha256: str | None,
    repository_root: str | os.PathLike[str],
    fault: Callable[[str], None] | None = None,
) -> WriteResult:
    """Publish one immutable/attempt artifact with native APFS no-replace."""

    validate_manifest(artifact)
    verify_self_hash(artifact)
    plans = _validated_semantic_plan_map(semantic_plans)
    _validate_artifact_plan_binding(artifact, plans)
    validate_git_source_identity(repository_root, artifact["source"])
    kind = artifact["artifact_kind"]
    if kind == "immutable_step_record":
        basename = immutable_basename(artifact)
        digest = artifact["record_sha256"]
        actual_prior = artifact["step"]["previous_record_sha256"]
        if actual_prior != expected_prior_record_sha256:
            return WriteResult(
                WriteState.STALE_PRIOR,
                "H06_STALE_PRIOR_IDENTITY",
                basename,
                digest,
            )
    elif kind == "attempt_record":
        basename = attempt_basename(artifact)
        digest = artifact["attempt_sha256"]
        if artifact["base_record_sha256"] != expected_prior_record_sha256:
            return WriteResult(
                WriteState.STALE_PRIOR,
                "H06_STALE_PRIOR_IDENTITY",
                basename,
                digest,
            )
    else:
        raise ManifestError("H06_IMMUTABLE_KIND")
    data = canonical_json_bytes(artifact)
    root = Path(history_root)
    directory_fd, native = _validate_root_for_write(root)
    lock_fd: int | None = None
    temp_fd: int | None = None
    temp_name: str | None = None
    published = False
    io_phase = "lock"
    try:
        lock_fd = _acquire_writer_lock(directory_fd)
        _checkpoint(fault, "after_lock")
        io_phase = "history"
        chain, current, attempts, operational = _scan_history(
            root, take_shared_lock=False
        )
        _validate_chain_plan_binding(chain, plans)
        if operational:
            raise ManifestError("H06_OPERATIONAL_STATE_AMBIGUOUS")
        head = chain[-1] if chain else None
        head_hash = head["record_sha256"] if head is not None else None
        idempotent_head = (
            kind == "immutable_step_record" and head_hash == digest
        )
        if (
            not idempotent_head
            and head_hash != expected_prior_record_sha256
        ):
            return WriteResult(
                WriteState.STALE_PRIOR,
                "H06_STALE_PRIOR_IDENTITY",
                basename,
                digest,
            )
        if kind == "immutable_step_record":
            if not idempotent_head and head is not None and (
                artifact["step"]["previous_record_id"] != head["record_id"]
            ):
                return WriteResult(
                    WriteState.STALE_PRIOR,
                    "H06_STALE_PRIOR_IDENTITY",
                    basename,
                    digest,
                )
            if any(_attempt_is_unresolved(item) for item in attempts):
                raise ManifestError("H06_ATTEMPT_UNRESOLVED")
            if not idempotent_head:
                _validate_chain_plan_binding((*chain, artifact), plans)
        if current is not None:
            if (
                head is None
                or current["target"]["record_sha256"] != head_hash
            ):
                return WriteResult(
                    WriteState.STALE_PRIOR,
                    "H06_STALE_PRIOR_IDENTITY",
                    basename,
                    digest,
                )
        io_phase = "existing-target"
        try:
            existing, existing_data, existing_info = _load_canonical_file_at(
                directory_fd, basename
            )
        except FileNotFoundError:
            existing = None
        if existing is not None:
            if existing_data != data:
                return WriteResult(
                    WriteState.COLLISION,
                    "H06_IMMUTABLE_COLLISION",
                    basename,
                    digest,
                )
            existing_fd = os.open(
                basename,
                os.O_RDWR | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=directory_fd,
            )
            try:
                try:
                    native.full_fsync(existing_fd)
                    os.fsync(directory_fd)
                except OSError:
                    return WriteResult(
                        WriteState.DURABILITY_AMBIGUITY,
                        "H06_POST_RENAME_DURABILITY_AMBIGUOUS",
                        basename,
                        digest,
                    )
            finally:
                os.close(existing_fd)
            if existing_info.st_nlink != 1:
                raise ManifestError("H06_FINAL_IDENTITY_MISMATCH")
            return WriteResult(
                WriteState.ALREADY_PRESENT,
                "H06_IMMUTABLE_ALREADY_PRESENT",
                basename,
                digest,
            )
        _checkpoint(fault, "before_temp_create")
        try:
            temp_fd, temp_name, temp_info = _write_temporary(
                directory_fd, basename, data, native, fault
            )
        except ManifestError:
            raise
        except OSError:
            return WriteResult(
                WriteState.PRE_PUBLICATION_FAILURE,
                "H06_TEMP_WRITE_FAILURE",
                basename,
                digest,
            )
        _checkpoint(fault, "before_publish")
        _verify_temporary_entry(
            directory_fd,
            temp_name,
            basename,
            temp_fd,
            temp_info,
        )
        try:
            native.publish_exclusive(directory_fd, temp_name, basename)
            published = True
        except FileExistsError:
            if not _cleanup_temporary(
                directory_fd, temp_name, fault, temp_info
            ):
                return WriteResult(
                    WriteState.CLEANUP_AMBIGUITY,
                    "H06_CLEANUP_AMBIGUOUS",
                    basename,
                    digest,
                )
            temp_name = None
            return WriteResult(
                WriteState.COLLISION,
                "H06_IMMUTABLE_COLLISION",
                basename,
                digest,
            )
        except OSError:
            try:
                entry = os.stat(
                    basename,
                    dir_fd=directory_fd,
                    follow_symlinks=False,
                )
                if (entry.st_dev, entry.st_ino) == (
                    temp_info.st_dev,
                    temp_info.st_ino,
                ):
                    published = True
                    return WriteResult(
                        WriteState.PUBLICATION_AMBIGUITY,
                        "H06_PUBLICATION_AMBIGUOUS",
                        basename,
                        digest,
                    )
            except FileNotFoundError:
                pass
            if not _cleanup_temporary(
                directory_fd, temp_name, fault, temp_info
            ):
                return WriteResult(
                    WriteState.CLEANUP_AMBIGUITY,
                    "H06_CLEANUP_AMBIGUOUS",
                    basename,
                    digest,
                )
            temp_name = None
            return WriteResult(
                WriteState.PRE_PUBLICATION_FAILURE,
                "H06_NATIVE_PUBLICATION_FAILURE",
                basename,
                digest,
            )
        temp_name = None
        try:
            _checkpoint(fault, "after_publish")
        except OSError:
            return WriteResult(
                WriteState.PUBLICATION_AMBIGUITY,
                "H06_PUBLICATION_AMBIGUOUS",
                basename,
                digest,
            )
        try:
            os.fsync(directory_fd)
            _checkpoint(fault, "after_directory_fsync")
            native.full_fsync(temp_fd)
            _checkpoint(fault, "after_final_fullfsync")
        except OSError:
            return WriteResult(
                WriteState.DURABILITY_AMBIGUITY,
                "H06_POST_RENAME_DURABILITY_AMBIGUOUS",
                basename,
                digest,
            )
        try:
            _verify_published_identity(
                directory_fd,
                basename,
                temp_fd,
                temp_info,
                data,
            )
            _checkpoint(fault, "after_final_identity")
        except (ManifestError, OSError):
            return WriteResult(
                WriteState.FINAL_IDENTITY_MISMATCH,
                "H06_FINAL_IDENTITY_MISMATCH",
                basename,
                digest,
            )
        return WriteResult(
            WriteState.DURABLE,
            "H06_IMMUTABLE_DURABLE",
            basename,
            digest,
        )
    except (ManifestError, OSError) as error:
        if temp_name is not None:
            cleanup = _cleanup_temporary(
                directory_fd, temp_name, fault, temp_info
            )
            if not cleanup:
                return WriteResult(
                    WriteState.CLEANUP_AMBIGUITY,
                    "H06_CLEANUP_AMBIGUOUS",
                    basename,
                    digest,
                )
        if published:
            return WriteResult(
                WriteState.PUBLICATION_AMBIGUITY,
                "H06_PUBLICATION_AMBIGUOUS",
                basename,
                digest,
            )
        if isinstance(error, ManifestError) and (
            error.code == "H06_CLEANUP_AMBIGUOUS"
        ):
            return WriteResult(
                WriteState.CLEANUP_AMBIGUITY,
                "H06_CLEANUP_AMBIGUOUS",
                basename,
                digest,
            )
        if isinstance(error, ManifestError):
            raise
        if io_phase == "lock":
            if error.errno in (errno.EPERM, errno.EACCES):
                error_code = "H06_LOCK_PERMISSION_FAILURE"
            elif error.errno in (
                getattr(errno, "ENOTSUP", -1),
                getattr(errno, "EOPNOTSUPP", -1),
            ):
                error_code = "H06_LOCK_UNSUPPORTED"
            elif error.errno == errno.EBADF:
                error_code = "H06_LOCK_BAD_DESCRIPTOR"
            elif error.errno == errno.EINVAL:
                error_code = "H06_LOCK_INVALID_ARGUMENT"
            elif error.errno == errno.ENOENT:
                error_code = "H06_LOCK_PATH_MISSING"
            elif error.errno == errno.ELOOP:
                error_code = "H06_LOCK_SYMLINK"
            else:
                error_code = "H06_LOCK_IO_FAILURE"
        else:
            error_code = {
                "history": "H06_HISTORY_IO_FAILURE",
                "existing-target": "H06_TARGET_READ_FAILURE",
            }.get(io_phase, "H06_PRE_PUBLICATION_FAILURE")
        return WriteResult(
            WriteState.PRE_PUBLICATION_FAILURE,
            error_code,
            basename,
            digest,
        )
    finally:
        try:
            if temp_fd is not None:
                os.close(temp_fd)
        finally:
            try:
                if lock_fd is not None:
                    try:
                        fcntl.flock(lock_fd, fcntl.LOCK_UN)
                    finally:
                        os.close(lock_fd)
            finally:
                os.close(directory_fd)


def _validate_promotable_chain(
    chain: Sequence[Mapping[str, Any]],
    target: Mapping[str, Any],
) -> None:
    if not chain or chain[-1]["record_sha256"] != target["record_sha256"]:
        raise ManifestError("H06_PROMOTION_TARGET_NOT_HEAD")
    if target["plan_state"]["status"] != "complete":
        raise ManifestError("H06_PROMOTION_PLAN_INCOMPLETE")
    for record in chain:
        for action in record["step"]["actions"]:
            if action["required"] and action["status"] not in (
                "reconciled",
                "complete",
            ):
                raise ManifestError("H06_PROMOTION_ACTION_INCOMPLETE")


def promote_current_index(
    history_root: str | os.PathLike[str],
    index: Mapping[str, Any],
    *,
    semantic_plans: Sequence[Mapping[str, Any]],
    expected_prior_index_sha256: str | None,
    fault: Callable[[str], None] | None = None,
) -> WriteResult:
    """Atomically replace current only after full immutable-chain validation."""

    validate_manifest(index)
    verify_self_hash(index)
    plans = _validated_semantic_plan_map(semantic_plans)
    _validate_index_plan_binding(index, plans)
    if index["artifact_kind"] != "current_index":
        raise ManifestError("H06_CURRENT_KIND")
    root = Path(history_root)
    directory_fd, native = _validate_root_for_write(root)
    lock_fd: int | None = None
    temp_fd: int | None = None
    temp_name: str | None = None
    renamed = False
    data = canonical_json_bytes(index)
    digest = index["index_sha256"]
    try:
        lock_fd = _acquire_writer_lock(directory_fd)
        _checkpoint(fault, "after_lock")
        current = _existing_current_index(directory_fd)
        actual_prior = (
            current["index_sha256"] if current is not None else None
        )
        if (
            actual_prior != expected_prior_index_sha256
            or index["prior_index_sha256"] != expected_prior_index_sha256
        ):
            return WriteResult(
                WriteState.STALE_PRIOR,
                "H06_STALE_PRIOR_IDENTITY",
                "current-manifest.json",
                digest,
            )
        chain, scanned_current, attempts, operational = _scan_history(
            root, take_shared_lock=False
        )
        _validate_chain_plan_binding(chain, plans)
        if scanned_current != current:
            raise ManifestError("H06_CURRENT_CHANGED_UNDER_LOCK")
        if (
            any(_attempt_is_unresolved(item) for item in attempts)
            or operational
        ):
            raise ManifestError("H06_PROMOTION_INCOMPLETE_HISTORY")
        target_hash = index["target"]["record_sha256"]
        target = next(
            (
                record for record in chain
                if record["record_sha256"] == target_hash
            ),
            None,
        )
        if target is None:
            raise ManifestError("H06_PROMOTION_TARGET_MISSING")
        if index["target"]["path"] != immutable_basename(target):
            raise ManifestError("H06_PROMOTION_TARGET_PATH")
        if index["target"]["record_id"] != target["record_id"]:
            raise ManifestError("H06_PROMOTION_TARGET_IDENTITY")
        if index["profile"] != target["profile"]:
            raise ManifestError("H06_PROMOTION_PROFILE")
        if index["source"] != {
            "commit": target["source"]["commit"],
            "tree": target["source"]["tree"],
            "plan_sha256": target["source"]["plan_sha256"],
        }:
            raise ManifestError("H06_PROMOTION_SOURCE")
        _validate_promotable_chain(chain, target)
        temp_fd, temp_name, temp_info = _write_temporary(
            directory_fd,
            "current-manifest.json",
            data,
            native,
            fault,
        )
        _checkpoint(fault, "before_current_replace")
        _verify_temporary_entry(
            directory_fd,
            temp_name,
            "current-manifest.json",
            temp_fd,
            temp_info,
        )
        existing_info: os.stat_result | None = None
        try:
            existing_info = os.stat(
                "current-manifest.json",
                dir_fd=directory_fd,
                follow_symlinks=False,
            )
            if not stat.S_ISREG(existing_info.st_mode):
                raise ManifestError("H06_CURRENT_INVALID")
        except FileNotFoundError:
            if expected_prior_index_sha256 is not None:
                raise ManifestError("H06_CURRENT_MISSING")
        rechecked = _existing_current_index(directory_fd)
        if rechecked != current:
            raise ManifestError("H06_CURRENT_CHANGED_UNDER_LOCK")
        os.replace(
            temp_name,
            "current-manifest.json",
            src_dir_fd=directory_fd,
            dst_dir_fd=directory_fd,
        )
        renamed = True
        temp_name = None
        _checkpoint(fault, "after_current_replace")
        try:
            os.fsync(directory_fd)
            _checkpoint(fault, "after_current_directory_fsync")
        except OSError:
            return WriteResult(
                WriteState.DURABILITY_AMBIGUITY,
                "H06_CURRENT_PROMOTION_AMBIGUOUS",
                "current-manifest.json",
                digest,
            )
        try:
            _verify_published_identity(
                directory_fd,
                "current-manifest.json",
                temp_fd,
                temp_info,
                data,
            )
        except (ManifestError, OSError):
            return WriteResult(
                WriteState.FINAL_IDENTITY_MISMATCH,
                "H06_FINAL_IDENTITY_MISMATCH",
                "current-manifest.json",
                digest,
            )
        return WriteResult(
            WriteState.DURABLE,
            "H06_CURRENT_PROMOTED",
            "current-manifest.json",
            digest,
        )
    except (ManifestError, OSError):
        if temp_name is not None:
            if not _cleanup_temporary(
                directory_fd, temp_name, fault, temp_info
            ):
                return WriteResult(
                    WriteState.CLEANUP_AMBIGUITY,
                    "H06_CLEANUP_AMBIGUOUS",
                    "current-manifest.json",
                    digest,
                )
        if renamed:
            return WriteResult(
                WriteState.PUBLICATION_AMBIGUITY,
                "H06_CURRENT_PROMOTION_AMBIGUOUS",
                "current-manifest.json",
                digest,
            )
        raise
    finally:
        try:
            if temp_fd is not None:
                os.close(temp_fd)
        finally:
            try:
                if lock_fd is not None:
                    try:
                        fcntl.flock(lock_fd, fcntl.LOCK_UN)
                    finally:
                        os.close(lock_fd)
            finally:
                os.close(directory_fd)


def validate_execution_handoff(
    semantic_plan: Mapping[str, Any],
    action_result: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Accept a truthful typed result without owning submission or retries."""

    digest = plan_sha256(semantic_plan)
    if not isinstance(action_result, Mapping):
        raise ManifestError("H06_HANDOFF_RESULT_INCOMPLETE")
    action_id = action_result.get("action_id")
    planned = {
        action["action_id"]: action
        for step in semantic_plan["steps"]
        for action in step["actions"]
    }
    if action_id not in planned:
        raise ManifestError("H06_HANDOFF_ACTION_UNKNOWN")
    source_action = planned[action_id]
    migration_id = action_id.split(":", 1)[0]
    _validate_action(
        action_result,
        migration_id,
        action_result.get("ordinal", -1),
        immutable=True,
    )
    request = action_result["transaction"]["request_identity"]
    if action_result["transaction"]["required"]:
        expected = plan_action_sha256(digest, action_id)
        if request["plan_action_sha256"] != expected:
            raise ManifestError("H06_HANDOFF_PLAN_ACTION_HASH")
    for key in (
        "semantic_action_id",
        "ordinal",
        "kind",
        "required",
        "expected_postconditions",
        "supersedes",
        "disposition",
    ):
        if action_result[key] != source_action[key]:
            raise ManifestError("H06_HANDOFF_PLAN_MISMATCH")
    if action_result["status"] not in ("reconciled", "complete"):
        raise ManifestError("H06_HANDOFF_RESULT_INCOMPLETE")
    return copy.deepcopy(action_result)
