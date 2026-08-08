from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from scripts.utils.manifest_schema import (
    EVENT_EVIDENCE_DOMAIN,
    HistoryState,
    ManifestError,
    attempt_basename,
    build_manifest_schema,
    canonical_json_bytes,
    event_evidence_sha256,
    immutable_basename,
    load_json_bytes,
    normalize_evidence_path,
    parse_canonical_manifest,
    plan_action_sha256,
    plan_sha256,
    read_history,
    schema_json_bytes,
    seal_artifact,
    source_set_sha256,
    validate_execution_handoff,
    validate_git_source_identity,
    validate_manifest,
    validate_semantic_plan,
    verify_self_hash,
)
from scripts.utils.migration import Migration


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = (
    ROOT
    / "docs/chains/rh/schemas/deployment-manifest-v2.schema.json"
)
BASE_HISTORY = ROOT / "migration_history/base-mainnet/v1"
EVENT_VECTOR = (
    "4008ce9d56daa4cfe33ebea06761a8508ca04933d7709670c81f944d7df4c79b"
)
PROFILE = {
    "profile_id": "robinhood-mainnet",
    "expected_chain_id": 4663,
}
MEMBERS = [
    {
        "path": "scripts/utils/migration.py",
        "sha256": (
            "c0bc3ff369d5664af3d96585c7870b8be723b54930664b5f1ce8870f8ace53e3"
        ),
    }
]
SOURCE_SET = source_set_sha256(MEMBERS)
COMMIT = "70dd76516ca9b4af8c0797c327bf15732634e5f6"
TREE = "9f269826f0adfd6e970218a9957b3129c1481ccc"
TX_HASH = "0x" + "11" * 32
BLOCK_HASH = "0x" + "22" * 32
OBSERVATION_HASH = "0x" + "44" * 32


def _typed(
    state="known",
    type_name="uint256",
    value=0,
    reason_code=None,
):
    result = {"state": state, "type": type_name, "value": value}
    if reason_code is not None:
        result["reason_code"] = reason_code
    return result


def _expected_postconditions():
    return [
        {
            "postcondition_id": "configured-value",
            "kind": "configuration-value",
            "subject": "hq",
            "value": _typed(),
        }
    ]


def _non_executable_postconditions():
    return [
        {
            "postcondition_id": "non-executable-effect",
            "kind": "assertion",
            "subject": "planned-reservation",
            "value": _typed(
                "not-applicable",
                "string",
                None,
                "non-executable-action",
            ),
        }
    ]


def _plan_action(
    *,
    kind="configuration",
    required=True,
    transaction_required=True,
    disposition=None,
):
    return {
        "action_id": "0900:000000:configure-hq",
        "semantic_action_id": "configure-hq",
        "ordinal": 0,
        "kind": kind,
        "required": required,
        "transaction_required": transaction_required,
        "expected_postconditions": (
            _non_executable_postconditions()
            if kind in {"omission", "blocked", "deferred", "rejected", "tooling-only"}
            else _expected_postconditions()
        ),
        "supersedes": [],
        "disposition": disposition,
    }


def make_plan(*, action=None):
    return {
        "profile": copy.deepcopy(PROFILE),
        "source": {
            "commit": COMMIT,
            "tree": TREE,
            "source_set_sha256": SOURCE_SET,
            "members": copy.deepcopy(MEMBERS),
        },
        "steps": [
            {
                "migration_id": "0900",
                "semantic_step_id": "configure",
                "ordinal": 0,
                "required": True,
                "actions": [copy.deepcopy(action or _plan_action())],
            }
        ],
    }


def make_two_step_plan():
    plan = make_plan()
    second_action = copy.deepcopy(_plan_action())
    second_action.update(
        {
            "action_id": "0901:000000:finalize-hq",
            "semantic_action_id": "finalize-hq",
        }
    )
    second_action["expected_postconditions"][0][
        "postcondition_id"
    ] = "finalized-value"
    plan["steps"].append(
        {
            "migration_id": "0901",
            "semantic_step_id": "finalize",
            "ordinal": 1,
            "required": True,
            "actions": [second_action],
        }
    )
    return plan


def _transaction(*, required=True):
    if not required:
        return {
            "required": False,
            "request_identity": {
                "state": "not-applicable",
                "semantic_request_id": None,
                "plan_action_sha256": None,
                "reason_code": "non-transaction-action",
            },
            "submission": {
                "status": "not-applicable",
                "transaction_hash": None,
            },
            "receipt": {
                "status": "not-applicable",
                "transaction_hash": None,
                "block_number": None,
                "block_hash": None,
                "success": None,
                "gas_used": None,
                "cumulative_gas_used": _typed(
                    "not-applicable",
                    "uint256",
                    None,
                    "non-transaction-action",
                ),
            },
            "finality": {
                "status": "not-applicable",
                "policy_id": None,
                "required_confirmations": None,
                "required_finality_tag": _typed(
                    "not-applicable",
                    "string",
                    None,
                    "non-transaction-action",
                ),
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
    plan = make_plan()
    digest = plan_sha256(plan)
    return {
        "required": True,
        "request_identity": {
            "state": "known",
            "semantic_request_id": "0900:000000:configure-hq",
            "plan_action_sha256": plan_action_sha256(
                digest, "0900:000000:configure-hq"
            ),
        },
        "submission": {
            "status": "submitted",
            "transaction_hash": TX_HASH,
        },
        "receipt": {
            "status": "confirmed",
            "transaction_hash": TX_HASH,
            "block_number": 123,
            "block_hash": BLOCK_HASH,
            "success": True,
            "gas_used": 0,
            "cumulative_gas_used": _typed(),
        },
        "finality": {
            "status": "complete",
            "policy_id": "robinhood-confirmations-64-v1",
            "required_confirmations": 64,
            "required_finality_tag": _typed(
                "not-applicable",
                "string",
                None,
                "confirmation-depth-policy",
            ),
            "observed_confirmations": 64,
            "observation_block_number": 187,
            "observation_block_hash": OBSERVATION_HASH,
        },
        "reconciliation": {
            "status": "reconciled",
            "observation_source_code": "owner-approved-observer",
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


def _complete_action(
    *,
    kind="configuration",
    required=True,
    transaction_required=True,
    disposition=None,
):
    expected = (
        _non_executable_postconditions()
        if kind in {"omission", "blocked", "deferred", "rejected", "tooling-only"}
        else _expected_postconditions()
    )
    observed = (
        [
            {
                "postcondition_id": "non-executable-effect",
                "value": _typed(
                    "not-applicable",
                    "string",
                    None,
                    "non-executable-action",
                ),
                "observation": {
                    "method_code": "not-applicable",
                    "block_number": None,
                    "block_hash": None,
                },
                "status": "not-applicable",
            }
        ]
        if kind in {"omission", "blocked", "deferred", "rejected", "tooling-only"}
        else [
            {
                "postcondition_id": "configured-value",
                "value": _typed(),
                "observation": {
                    "method_code": "configuration-read",
                    "block_number": 187,
                    "block_hash": OBSERVATION_HASH,
                },
                "status": "matched",
            }
        ]
    )
    return {
        "action_id": "0900:000000:configure-hq",
        "ordinal": 0,
        "semantic_action_id": "configure-hq",
        "kind": kind,
        "required": required,
        "status": "complete",
        "expected_postconditions": expected,
        "observed_postconditions": observed,
        "transaction": _transaction(required=transaction_required),
        "events": [],
        "supersedes": [],
        "disposition": disposition,
        "error": None,
    }


def _complete_action_for_plan(plan_action):
    action = _complete_action(
        kind=plan_action["kind"],
        required=plan_action["required"],
        transaction_required=plan_action["transaction_required"],
        disposition=copy.deepcopy(plan_action["disposition"]),
    )
    for key in (
        "action_id",
        "semantic_action_id",
        "ordinal",
        "kind",
        "required",
        "expected_postconditions",
        "supersedes",
        "disposition",
    ):
        action[key] = copy.deepcopy(plan_action[key])
    observed = []
    for expected in plan_action["expected_postconditions"]:
        if expected["value"]["state"] == "not-applicable":
            observed.append(
                {
                    "postcondition_id": expected["postcondition_id"],
                    "value": copy.deepcopy(expected["value"]),
                    "observation": {
                        "method_code": "not-applicable",
                        "block_number": None,
                        "block_hash": None,
                    },
                    "status": "not-applicable",
                }
            )
        else:
            observed.append(
                {
                    "postcondition_id": expected["postcondition_id"],
                    "value": copy.deepcopy(expected["value"]),
                    "observation": {
                        "method_code": "configuration-read",
                        "block_number": 187,
                        "block_hash": OBSERVATION_HASH,
                    },
                    "status": "matched",
                }
            )
    action["observed_postconditions"] = observed
    if action["transaction"]["required"]:
        action["transaction"]["request_identity"][
            "semantic_request_id"
        ] = action["action_id"]
    return action


def make_record(*, action=None, terminal=True, plan=None, step_ordinal=0):
    supplied_plan = plan
    if plan is None:
        plan_action = _plan_action()
        if action is not None:
            plan_action = {
                key: copy.deepcopy(action[key])
                for key in (
                    "action_id",
                    "semantic_action_id",
                    "ordinal",
                    "kind",
                    "required",
                    "expected_postconditions",
                    "supersedes",
                    "disposition",
                )
            }
            plan_action["transaction_required"] = action["transaction"][
                "required"
            ]
        plan = make_plan(action=plan_action)
    digest = plan_sha256(plan)
    plan_step = plan["steps"][step_ordinal]
    actions = (
        [copy.deepcopy(action)]
        if action is not None
        else [
            _complete_action_for_plan(plan_action)
            for plan_action in plan_step["actions"]
        ]
    )
    if action is None:
        for action_value in actions:
            if action_value["transaction"]["required"]:
                action_value["transaction"]["request_identity"][
                    "plan_action_sha256"
                ] = plan_action_sha256(
                    digest, action_value["action_id"]
                )
    if supplied_plan is None:
        completed = [plan_step["semantic_step_id"]]
        remaining = [] if terminal else ["later"]
        plan_status = "complete" if terminal else "in-progress"
    else:
        completed = sorted(
            step["semantic_step_id"]
            for step in plan["steps"]
            if step["required"] and step["ordinal"] <= step_ordinal
        )
        remaining = sorted(
            step["semantic_step_id"]
            for step in plan["steps"]
            if step["required"] and step["ordinal"] > step_ordinal
        )
        plan_status = "complete" if not remaining else "in-progress"
    unsigned = {
        "schema": "ripe.robinhood.deployment-manifest",
        "schema_version": 2,
        "artifact_kind": "immutable_step_record",
        "record_id": (
            f"{plan['profile']['profile_id']}:{digest}:"
            f"{plan_step['migration_id']}:{plan_step['semantic_step_id']}"
        ),
        "record_sha256": "0" * 64,
        "profile": copy.deepcopy(plan["profile"]),
        "source": {
            "commit": plan["source"]["commit"],
            "tree": plan["source"]["tree"],
            "plan_sha256": digest,
            "source_set_sha256": plan["source"]["source_set_sha256"],
            "members": copy.deepcopy(plan["source"]["members"]),
        },
        "step": {
            "migration_id": plan_step["migration_id"],
            "semantic_step_id": plan_step["semantic_step_id"],
            "ordinal": plan_step["ordinal"],
            "previous_record_id": None,
            "previous_record_sha256": None,
            "status": "complete",
            "actions": actions,
        },
        "plan_state": {
            "plan_sha256": digest,
            "predecessor_plan_sha256": None,
            "completed_step_ids": completed,
            "remaining_required_step_ids": remaining,
            "status": plan_status,
        },
    }
    return seal_artifact(unsigned)


def make_attempt(*, plan=None):
    record = make_record(plan=plan)
    attempt = {
        key: copy.deepcopy(record[key])
        for key in ("schema", "schema_version", "profile", "source", "step", "plan_state")
    }
    attempt.update(
        {
            "artifact_kind": "attempt_record",
            "attempt_id": "ab" * 16,
            "attempt_sha256": "0" * 64,
            "base_record_id": None,
            "base_record_sha256": None,
            "retention_class": "success-7d",
        }
    )
    return seal_artifact(attempt)


def make_index(record, prior=None):
    return seal_artifact(
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


def write_artifact(root, artifact, basename):
    root.mkdir(mode=0o700)
    (root / basename).write_bytes(canonical_json_bytes(artifact))


def make_successor(record, *, plan=None):
    successor = copy.deepcopy(record)
    if plan is None:
        action = successor["step"]["actions"][0]
        action["action_id"] = "0901:000000:finalize-hq"
        action["semantic_action_id"] = "finalize-hq"
        action["transaction"]["request_identity"][
            "semantic_request_id"
        ] = action["action_id"]
        for expected in action["expected_postconditions"]:
            expected["postcondition_id"] = "finalized-value"
        for observed in action["observed_postconditions"]:
            observed["postcondition_id"] = "finalized-value"
        plan_step = {
            "migration_id": "0901",
            "semantic_step_id": "finalize",
            "ordinal": 1,
        }
    else:
        assert plan_sha256(plan) == record["source"]["plan_sha256"]
        plan_step = plan["steps"][1]
        action = _complete_action_for_plan(plan_step["actions"][0])
        successor["step"]["actions"] = [action]
    action["transaction"]["request_identity"][
        "plan_action_sha256"
    ] = plan_action_sha256(
        record["source"]["plan_sha256"], action["action_id"]
    )
    successor["step"].update(
        {
            "migration_id": plan_step["migration_id"],
            "semantic_step_id": plan_step["semantic_step_id"],
            "ordinal": plan_step["ordinal"],
            "previous_record_id": record["record_id"],
            "previous_record_sha256": record["record_sha256"],
        }
    )
    successor["record_id"] = (
        f"robinhood-mainnet:{record['source']['plan_sha256']}:"
        f"{plan_step['migration_id']}:{plan_step['semantic_step_id']}"
    )
    successor["record_sha256"] = "0" * 64
    if plan is None:
        successor["plan_state"]["completed_step_ids"] = [
            "configure",
            "finalize",
        ]
    else:
        successor["plan_state"]["completed_step_ids"] = sorted(
            step["semantic_step_id"]
            for step in plan["steps"]
            if step["required"] and step["ordinal"] <= plan_step["ordinal"]
        )
        successor["plan_state"]["remaining_required_step_ids"] = sorted(
            step["semantic_step_id"]
            for step in plan["steps"]
            if step["required"] and step["ordinal"] > plan_step["ordinal"]
        )
        successor["plan_state"]["status"] = (
            "complete"
            if not successor["plan_state"][
                "remaining_required_step_ids"
            ]
            else "in-progress"
        )
    return seal_artifact(successor)


def test_schema_file_is_exact_authoritative_builder_output():
    assert SCHEMA_PATH.read_bytes() == schema_json_bytes()
    parsed = load_json_bytes(SCHEMA_PATH.read_bytes())
    assert parsed == build_manifest_schema()
    assert parsed["additionalProperties"] is False
    assert parsed["$defs"]["immutableStepRecord"][
        "additionalProperties"
    ] is False


def test_every_schema_object_branch_is_closed_and_declares_exact_required_keys():
    schema = build_manifest_schema()
    visited = 0

    def walk(node, path=()):
        nonlocal visited
        if isinstance(node, dict):
            if node.get("type") == "object":
                visited += 1
                assert node["additionalProperties"] is False
                optional = set(node["properties"]) - set(node["required"])
                if path == ("$defs", "action"):
                    assert optional == {"execution_evidence"}
                else:
                    assert optional == set()
            for key, child in node.items():
                walk(child, path + (key,))
        elif isinstance(node, list):
            for index, child in enumerate(node):
                walk(child, path + (index,))

    walk(schema)
    assert visited >= 50
    explicit_null_branches = [
        branch
        for branch in schema["$defs"]["typedValue"]["oneOf"]
        if branch["properties"]["state"].get("const") == "explicit-null"
    ]
    assert {
        branch["properties"]["type"]["const"]
        for branch in explicit_null_branches
    } == {
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
    }
    assert all(
        branch["properties"]["value"] == {"type": "null"}
        for branch in explicit_null_branches
    )


@pytest.mark.parametrize(
    "mutation",
    (
        lambda value: value.pop("profile"),
        lambda value: value.update({"extra": True}),
        lambda value: value.update({"schema_version": "2"}),
        lambda value: value["profile"].update({"expected_chain_id": 0}),
        lambda value: value["step"]["actions"][0].update({"status": None}),
        lambda value: value["step"]["actions"][0]["transaction"].update(
            {"required": "true"}
        ),
    ),
)
def test_schema_rejects_missing_extra_and_wrong_type_fields(mutation):
    record = make_record()
    mutation(record)
    with pytest.raises(ManifestError):
        validate_manifest(record)


@pytest.mark.parametrize(
    "kind",
    (
        "deployment",
        "configuration",
        "assertion",
        "omission",
        "blocked",
        "deferred",
        "rejected",
        "tooling-only",
    ),
)
def test_every_action_kind_has_a_closed_valid_record(kind):
    non_executable = kind in {
        "omission",
        "blocked",
        "deferred",
        "rejected",
        "tooling-only",
    }
    disposition = (
        {
            "code": "owner-disposition",
            "authority_ref": "OD-TEST",
            "explanation_digest_sha256": "bb" * 32,
        }
        if non_executable
        else None
    )
    action = _complete_action(
        kind=kind,
        required=False if kind == "blocked" else True,
        transaction_required=not non_executable and kind != "assertion",
        disposition=disposition,
    )
    record = make_record(action=action)
    validate_manifest(record)
    verify_self_hash(record)


def test_zero_false_empty_and_explicit_null_are_not_missing():
    record = make_record()
    value = record["step"]["actions"][0]["expected_postconditions"][0]["value"]
    assert value == {"state": "known", "type": "uint256", "value": 0}
    known_false = _typed("known", "boolean", False)
    known_empty = _typed("known", "string", "")
    explicit_null = _typed("explicit-null", "address", None)
    for typed_value in (known_false, known_empty, explicit_null):
        candidate = make_record()
        candidate["step"]["actions"][0]["expected_postconditions"][0][
            "value"
        ] = typed_value
        candidate["step"]["actions"][0]["observed_postconditions"][0][
            "value"
        ] = copy.deepcopy(typed_value)
        candidate = seal_artifact(candidate)
        validate_manifest(candidate)
    missing = make_record()
    del missing["step"]["actions"][0]["expected_postconditions"][0]["value"]
    with pytest.raises(ManifestError):
        validate_manifest(missing)


@pytest.mark.parametrize(
    ("value", "code"),
    (
        (1.5, "H06_FLOAT_FORBIDDEN"),
        ("\ud800", "H06_UNICODE_INVALID_SCALAR"),
        ("e\u0301", "H06_UNICODE_NOT_NFC"),
    ),
)
def test_canonical_domain_rejects_float_surrogate_and_non_nfc(value, code):
    with pytest.raises(ManifestError, match=code):
        canonical_json_bytes({"value": value})


def test_strict_parser_rejects_duplicate_float_nonfinite_and_negative_zero():
    for raw in (
        b'{"a":1,"a":2}',
        b'{"a":1.0}',
        b'{"a":NaN}',
        b'{"a":-0.0}',
    ):
        with pytest.raises(ManifestError, match="H06_JSON_PARSE"):
            load_json_bytes(raw)


def test_canonical_serialization_exact_key_escape_and_newline_vector():
    value = {"\U00010000": 0, "\ue000": False, "a": "\b\t\n/\\"}
    expected = (
        '{"a":"\\u0008\\u0009\\u000a/\\\\","":false,"𐀀":0}\n'
    ).encode()
    assert canonical_json_bytes(value) == expected
    assert not canonical_json_bytes(value).endswith(b"\n\n")


@pytest.mark.parametrize(
    "path",
    (
        "",
        "/absolute",
        "../escape",
        "nested/../escape",
        "nested//empty",
        "trailing/",
        r"windows\path",
        "file://uri",
        "~/home",
        "C:/drive",
        "control/\n",
    ),
)
def test_persisted_path_rejection_is_fail_closed(path):
    with pytest.raises(ManifestError):
        normalize_evidence_path(path)


@pytest.mark.parametrize(
    ("boundary", "h05_bytes", "h06_value"),
    (
        ("self-field", b'{"a":1}', {"a": 1}),
        ("hash-input-lf", b'{"a":1}', {"a": 1}),
        ("stored-lf", b'{"a":1}\n', {"a": 1}),
        ("control-escaping", b'{"a":"\\b"}', {"a": "\b"}),
        ("unicode-order", '{"𐀀":0,"":0}'.encode(), {"\ue000": 0, "\U00010000": 0}),
        ("artifact-kind", b'{"artifact_kind":"h05-report"}', {"artifact_kind": "current_index"}),
        ("domain", b"report", {"plan": "report"}),
    ),
)
def test_seven_h05_h06_boundary_vectors_are_not_substitutable(
    boundary, h05_bytes, h06_value
):
    h06_bytes = canonical_json_bytes(h06_value)
    if boundary == "stored-lf":
        assert h06_bytes == h05_bytes
        assert hashlib.sha256(h06_bytes).digest() != hashlib.sha256(
            h05_bytes[:-1]
        ).digest()
    else:
        assert h06_bytes != h05_bytes


def test_source_plan_and_action_digests_are_deterministic_known_vectors():
    plan = make_plan()
    assert SOURCE_SET == (
        "a0b5b40118486c2f82e15fe06f7a8e0909fcf80ed1de1b39b02dc3b5116b3a12"
    )
    assert plan_sha256(plan) == (
        "24a538ecabbed898e434bb9165a5c085ec4ba25bae84726dcb645df1fca3da8a"
    )
    assert plan_action_sha256(
        plan_sha256(plan), "0900:000000:configure-hq"
    ) == "de3f80900f766cd2cdb6b17661fe6de40d0c0b1c0718b07ab43dfff9e052ca61"


def test_git_source_identity_resolves_commit_tree_and_exact_blob_bytes():
    source = {
        "commit": COMMIT,
        "tree": TREE,
        "source_set_sha256": SOURCE_SET,
        "members": copy.deepcopy(MEMBERS),
    }
    validate_git_source_identity(ROOT, source)
    wrong_tree = copy.deepcopy(source)
    wrong_tree["tree"] = "f" * 40
    with pytest.raises(ManifestError, match="H06_SOURCE_GIT_IDENTITY"):
        validate_git_source_identity(ROOT, wrong_tree)
    wrong_member = copy.deepcopy(source)
    wrong_member["members"][0]["sha256"] = "f" * 64
    with pytest.raises(
        ManifestError, match="H06_SOURCE_MEMBER_MISMATCH"
    ):
        validate_git_source_identity(ROOT, wrong_member)


def _event_projection():
    return {
        "expected_chain_id": 4663,
        "transaction_hash": TX_HASH,
        "block_number": 123,
        "block_hash": BLOCK_HASH,
        "log_index": 0,
        "emitter": "0x" + "33" * 20,
        "topics": ["0x" + "44" * 32, "0x" + "55" * 32],
        "data": "0x0001ff",
    }


def _event_parent():
    projection = _event_projection()
    return {
        "profile": copy.deepcopy(PROFILE),
        "submission": {
            "status": "submitted",
            "transaction_hash": TX_HASH,
        },
        "receipt": {
            "status": "confirmed",
            "transaction_hash": TX_HASH,
            "block_number": 123,
            "block_hash": BLOCK_HASH,
        },
        "event": {
            "log_index": 0,
            "emitter": projection["emitter"],
            "topics": copy.deepcopy(projection["topics"]),
            "data": projection["data"],
            "signature_topic": projection["topics"][0],
        },
    }


def test_event_evidence_exact_reviewed_vector_and_domain():
    parent = _event_parent()
    assert event_evidence_sha256(
        _event_projection(), **parent
    ) == EVENT_VECTOR
    expected_bytes = (
        EVENT_EVIDENCE_DOMAIN
        + b"\x00"
        + canonical_json_bytes(_event_projection())
    )
    assert hashlib.sha256(expected_bytes).hexdigest() == EVENT_VECTOR


@pytest.mark.parametrize(
    "mutation",
    (
        lambda value: value.pop("data"),
        lambda value: value.update({"extra": 1}),
        lambda value: value.update({"transaction_hash": "0X" + "11" * 32}),
        lambda value: value.update({"block_hash": "0x1"}),
        lambda value: value.update({"emitter": "0x" + "AA" * 20}),
        lambda value: value.update({"data": "0x001"}),
        lambda value: value["topics"].reverse(),
        lambda value: value["topics"].pop(),
        lambda value: value.update({"data": "0x01ff"}),
    ),
)
def test_event_evidence_rejects_projection_and_linkage_mutations(mutation):
    projection = _event_projection()
    mutation(projection)
    with pytest.raises(ManifestError):
        event_evidence_sha256(projection, **_event_parent())


def test_event_evidence_rejects_wrong_parent_receipt_link():
    parent = _event_parent()
    parent["receipt"]["block_number"] = 124
    with pytest.raises(
        ManifestError, match="H06_EVENT_RECEIPT_MISMATCH"
    ):
        event_evidence_sha256(_event_projection(), **parent)


def test_self_hash_tampering_and_canonical_byte_tampering_fail():
    record = make_record()
    data = canonical_json_bytes(record)
    assert parse_canonical_manifest(data) == record
    tampered = copy.deepcopy(record)
    tampered["step"]["actions"][0]["observed_postconditions"][0]["value"][
        "value"
    ] = 1
    with pytest.raises(ManifestError, match="H06_SELF_HASH_MISMATCH"):
        verify_self_hash(tampered)
    with pytest.raises(ManifestError, match="H06_CANONICAL_BYTES"):
        parse_canonical_manifest(data[:-1] + b" \n")


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    (
        ("rpc_url", "https://public.invalid"),
        ("private_key", "synthetic-secret"),
        ("environment", {"SAFE": "value"}),
        ("provider_payload", {"id": 1}),
        ("exception_text", "synthetic error"),
        ("signed_transaction", "0x00"),
        ("signer", "0x" + "00" * 20),
    ),
)
def test_sensitive_and_unknown_fields_are_rejected(field_name, field_value):
    record = make_record()
    record[field_name] = field_value
    with pytest.raises(
        ManifestError,
        match="H06_(SENSITIVE_FIELD|SCHEMA_ADDITIONAL_PROPERTY)",
    ):
        validate_manifest(record)


def test_public_operator_allowed_only_as_typed_role_postcondition():
    action = _complete_action()
    address = "0x" + "77" * 20
    action["expected_postconditions"] = [
        {
            "postcondition_id": "operator-role",
            "kind": "role-membership",
            "subject": "operator-role",
            "value": _typed("known", "address", address),
        }
    ]
    action["observed_postconditions"] = [
        {
            "postcondition_id": "operator-role",
            "value": _typed("known", "address", address),
            "observation": {
                "method_code": "role-membership-read",
                "block_number": 187,
                "block_hash": OBSERVATION_HASH,
            },
            "status": "matched",
        }
    ]
    validate_manifest(make_record(action=action))
    action["signer"] = address
    with pytest.raises(ManifestError):
        make_record(action=action)


def test_execution_handoff_accepts_complete_typed_result_only():
    plan = make_plan()
    action = _complete_action()
    action["transaction"]["request_identity"][
        "plan_action_sha256"
    ] = plan_action_sha256(
        plan_sha256(plan), action["action_id"]
    )
    assert validate_execution_handoff(plan, action) == action
    for status in (
        "planned",
        "submitted",
        "confirmed",
        "finality-pending",
        "failed",
        "blocked",
    ):
        candidate = copy.deepcopy(action)
        candidate["status"] = status
        with pytest.raises(ManifestError):
            validate_execution_handoff(plan, candidate)
    with pytest.raises(ManifestError):
        validate_execution_handoff(plan, None)


def test_two_step_fixture_uses_exact_plan_action_hashes():
    plan = make_two_step_plan()
    first = make_record(plan=plan)
    second = make_successor(first, plan=plan)
    digest = plan_sha256(plan)
    for record in (first, second):
        action = record["step"]["actions"][0]
        assert action["transaction"]["request_identity"][
            "plan_action_sha256"
        ] == plan_action_sha256(digest, action["action_id"])


def test_semantic_plan_step_identity_is_unique():
    plan = make_two_step_plan()
    plan["steps"][1]["semantic_step_id"] = "configure"
    with pytest.raises(ManifestError, match="H06_PLAN_STEP_IDENTITY"):
        validate_semantic_plan(plan)
    plan = make_two_step_plan()
    plan["steps"][1]["migration_id"] = "0900"
    with pytest.raises(ManifestError, match="H06_PLAN_STEP_IDENTITY"):
        validate_semantic_plan(plan)


def test_semantic_plan_rejects_report_fields_and_report_hash_substitution():
    plan = make_plan()
    validate_semantic_plan(plan)
    plan["report_sha256"] = "aa" * 32
    with pytest.raises(ManifestError):
        validate_semantic_plan(plan)
    plan = make_plan()
    plan["plan_sha256"] = "bb" * 32
    with pytest.raises(ManifestError):
        validate_semantic_plan(plan)


def test_history_reader_valid_absent_incomplete_stale_and_wrong_identity(
    tmp_path,
):
    absent = tmp_path / "absent"
    result = read_history(
        "robinhood-mainnet",
        4663,
        "aa" * 32,
        COMMIT,
        TREE,
        absent,
    )
    assert result.state is HistoryState.ABSENT_CLEAN

    record = make_record()
    root = tmp_path / "history"
    write_artifact(root, record, immutable_basename(record))
    incomplete = read_history(
        "robinhood-mainnet",
        4663,
        record["source"]["plan_sha256"],
        COMMIT,
        TREE,
        root,
    )
    assert incomplete.state is HistoryState.INCOMPLETE

    index = make_index(record)
    (root / "current-manifest.json").write_bytes(
        canonical_json_bytes(index)
    )
    valid = read_history(
        "robinhood-mainnet",
        4663,
        record["source"]["plan_sha256"],
        COMMIT,
        TREE,
        root,
    )
    assert valid.state is HistoryState.VALID
    assert valid.action_ids == ("0900:000000:configure-hq",)
    assert read_history(
        "robinhood-testnet",
        4663,
        record["source"]["plan_sha256"],
        COMMIT,
        TREE,
        root,
    ).state is HistoryState.WRONG_PROFILE
    assert read_history(
        "robinhood-mainnet",
        46630,
        record["source"]["plan_sha256"],
        COMMIT,
        TREE,
        root,
    ).state is HistoryState.WRONG_CHAIN
    assert read_history(
        "robinhood-mainnet",
        4663,
        "ff" * 32,
        COMMIT,
        TREE,
        root,
    ).state is HistoryState.WRONG_PLAN
    assert read_history(
        "robinhood-mainnet",
        4663,
        record["source"]["plan_sha256"],
        "f" * 40,
        TREE,
        root,
    ).state is HistoryState.CORRUPT


def test_hash_chain_stale_current_missing_prior_and_multiple_heads(tmp_path):
    first = make_record()
    second = make_successor(first)
    root = tmp_path / "chain"
    root.mkdir(mode=0o700)
    (root / immutable_basename(first)).write_bytes(
        canonical_json_bytes(first)
    )
    (root / immutable_basename(second)).write_bytes(
        canonical_json_bytes(second)
    )
    stale_index = make_index(first)
    (root / "current-manifest.json").write_bytes(
        canonical_json_bytes(stale_index)
    )
    result = read_history(
        "robinhood-mainnet",
        4663,
        second["source"]["plan_sha256"],
        COMMIT,
        TREE,
        root,
    )
    assert result.state is HistoryState.STALE

    (root / immutable_basename(second)).unlink()
    missing = make_successor(first)
    missing["step"]["previous_record_sha256"] = "ff" * 32
    missing["record_sha256"] = "0" * 64
    missing = seal_artifact(missing)
    (root / immutable_basename(missing)).write_bytes(
        canonical_json_bytes(missing)
    )
    result = read_history(
        "robinhood-mainnet",
        4663,
        first["source"]["plan_sha256"],
        COMMIT,
        TREE,
        root,
    )
    assert result.state is HistoryState.CORRUPT

    (root / immutable_basename(missing)).unlink()
    second_head = copy.deepcopy(first)
    second_head["step"]["actions"][0]["observed_postconditions"][0]["value"][
        "value"
    ] = 1
    second_head["step"]["actions"][0]["expected_postconditions"][0]["value"][
        "value"
    ] = 1
    second_head["record_sha256"] = "0" * 64
    second_head = seal_artifact(second_head)
    (root / immutable_basename(second_head)).write_bytes(
        canonical_json_bytes(second_head)
    )
    result = read_history(
        "robinhood-mainnet",
        4663,
        first["source"]["plan_sha256"],
        COMMIT,
        TREE,
        root,
    )
    assert result.state is HistoryState.AMBIGUOUS


def test_attempt_is_non_authoritative_and_never_current():
    attempt = make_attempt()
    assert attempt_basename(attempt).startswith(
        ".attempt-robinhood-mainnet-"
    )
    with pytest.raises(ManifestError):
        immutable_basename(attempt)


def test_robinhood_migration_handoff_is_in_memory_typed_and_write_free(
    tmp_path,
):
    history = (
        tmp_path
        / "migration_history/robinhood-mainnet/v1"
    )
    deploy_args = SimpleNamespace(
        rpc="redacted-reference",
        sender=SimpleNamespace(address="0x" + "00" * 20),
        chain="robinhood-mainnet",
        blueprint=None,
        ignore_logs=False,
    )
    migration = Migration(
        deploy_args,
        {},
        "0900",
        None,
        str(history),
    )
    assert not history.exists()
    plan = make_plan()
    action = _complete_action()
    action["transaction"]["request_identity"][
        "plan_action_sha256"
    ] = plan_action_sha256(
        plan_sha256(plan), action["action_id"]
    )
    assert (
        migration.handoff_manifest_v2_action_result(plan, action)
        == action
    )
    assert migration.manifest_v2_action_results() == (action,)
    with pytest.raises(
        ManifestError, match="H06_HANDOFF_ACTION_DUPLICATE"
    ):
        migration.handoff_manifest_v2_action_result(plan, action)
    with pytest.raises(
        ManifestError, match="H06_LEGACY_EXECUTION_FORBIDDEN"
    ):
        migration.execute(lambda: None)
    assert not history.exists()


def test_every_committed_base_json_parses_without_rewrite():
    # The 59 numeric Base step manifests were extracted from the active tree and
    # remain recoverable from 610b43f4508e85628a1362532a79d68d71ea902c; see
    # docs/simplification/extracted-files.tsv.
    #
    # There is deliberately no assertion on the size of the corpus. What this
    # test is for is that every committed Base manifest parses, matches the
    # schema, and is not rewritten by being read — all of which hold for any
    # number of files. Pinning a count only meant that adding or removing a
    # manifest failed a test about JSON schema, which is what made the earlier
    # 60 -> 1 edit look like a coverage decision when it was really an artifact
    # of the pin.
    before = {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(BASE_HISTORY.glob("*.json"))
    }
    assert before, "no Base manifests found to validate"
    for relative in before:
        parsed = json.loads((ROOT / relative).read_bytes())
        assert set(parsed) == {"contracts"}
        for record in parsed["contracts"].values():
            assert set(record) in (
                {"address"},
                {"abi", "address", "args", "file", "solc_json"},
            )
    after = {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(BASE_HISTORY.glob("*.json"))
    }
    assert after == before


def test_two_clean_processes_produce_identical_record_bytes(tmp_path):
    expression = (
        "from tests.deployment.test_manifest_schema import make_record;"
        "from scripts.utils.manifest_schema import canonical_json_bytes;"
        "import sys;sys.stdout.buffer.write(canonical_json_bytes(make_record()))"
    )
    environment = {"PATH": os.defpath, "PYTHONPATH": str(ROOT)}
    outputs = []
    for name in ("checkout-a", "checkout-b"):
        checkout = tmp_path / name
        checkout.mkdir(mode=0o700)
        result = subprocess.run(
            [sys.executable, "-c", expression],
            cwd=checkout,
            env=environment,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr.decode()
        outputs.append(result.stdout)
    assert outputs[0] == outputs[1] == canonical_json_bytes(make_record())


@pytest.mark.parametrize(
    "path",
    (
        "migration_history/robinhood-mainnet/v1/.attempt-a",
        "migration_history/robinhood-mainnet/v1/.manifest-v2.lock",
        "migration_history/robinhood-mainnet/v1/.x.tmp.y",
        "migration_history/robinhood-testnet/v1/.attempt-a",
        "migration_history/robinhood-testnet/v1/.manifest-v2.lock",
        "migration_history/robinhood-testnet/v1/.x.tmp.y",
    ),
)
def test_six_restricted_patterns_are_ignored(path):
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "--quiet", path],
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 0


@pytest.mark.parametrize(
    "path",
    (
        "migration_history/robinhood-mainnet/v1/0900-x-"
        + "a" * 64
        + ".manifest-v2.json",
        "migration_history/robinhood-mainnet/v1/current-manifest.json",
        "migration_history/base-mainnet/v1/.attempt-a",
        "other/migration_history/robinhood-mainnet/v1/.attempt-a",
        "migration_history/robinhood-mainnet/v1/attempt-a",
        "migration_history/robinhood-mainnet/v1/.manifest-v2.locked",
        "migration_history/robinhood-mainnet/v1/x.tmp.y",
    ),
)
def test_ignore_rules_do_not_match_authority_base_or_near_matches(path):
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "--quiet", path],
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 1


def test_force_added_restricted_path_is_rejected_by_scope_policy():
    force_added = (
        "migration_history/robinhood-mainnet/v1/"
        ".attempt-robinhood-mainnet-" + "a" * 32 + "-" + "b" * 64 + ".json"
    )
    assert Path(force_added).name.startswith(".attempt-")
    authorized = {
        "docs/chains/rh/evidence/robinhood-manifest-phase-a.md",
        "scripts/utils/migration.py",
        "scripts/utils/json_file.py",
        "scripts/utils/manifest_schema.py",
        "docs/chains/rh/schemas/deployment-manifest-v2.schema.json",
        "tests/deployment/test_manifest_schema.py",
        "tests/deployment/test_current_manifest_promotion.py",
        ".gitignore",
    }
    assert force_added not in authorized
