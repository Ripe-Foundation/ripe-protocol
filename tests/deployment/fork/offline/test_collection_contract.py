from __future__ import annotations

import hashlib
import json
import os
from collections import Counter
from pathlib import Path

import pytest


EXPECTED_NODE_COUNT = 177
EXPECTED_NODE_DIGEST = (
    "f3b35ad98bca50c14615a2d7bd646e42096ae5f024d9aac591a9e23a5647703f"
)
EXPECTED_CLASSIFICATION_SHA256 = {
    "disabled": (
        "6a18dac61eb8ba41aa309089bf4d8ae6144d042b6c93be0c2e7e1eefd5e46531"
    ),
    "read-only-archive-fork": (
        "3943a6036398cabec7934038cb9bce6aa51046cb14ea554fedd8dd07be08f0bb"
    ),
}
EXPECTED_CLASS_COUNTS = {
    "disabled": {
        "blocked": 5,
        "deselected-safe-default": 1,
        "supporting": 171,
    },
    "read-only-archive-fork": {
        "blocked": 5,
        "qualifying": 1,
        "supporting": 171,
    },
}


def test_implemented_path_ledger_is_sorted_unique_and_within_ceiling(
    fork_framework,
):
    ledger = fork_framework.IMPLEMENTED_PATH_LEDGER
    assert ledger == tuple(sorted(set(ledger)))
    assert len(ledger) == 31
    assert len(ledger) <= fork_framework.PATH_CEILING
    assert all(
        path.startswith("tests/deployment/fork/") for path in ledger
    )


def test_implemented_path_ledger_matches_filesystem(fork_framework):
    actual = tuple(
        sorted(
            path.relative_to(fork_framework.REPOSITORY_ROOT).as_posix()
            for path in fork_framework.SUITE_ROOT.rglob("*.py")
        )
    )
    assert actual == fork_framework.IMPLEMENTED_PATH_LEDGER


def test_ordered_node_digest_is_stable_and_order_sensitive(fork_framework):
    first = fork_framework.ordered_node_digest(("a::one", "b::two"))
    second = fork_framework.ordered_node_digest(("a::one", "b::two"))
    reversed_digest = fork_framework.ordered_node_digest(
        ("b::two", "a::one")
    )
    assert first == second
    assert first != reversed_digest
    assert len(first) == hashlib.sha256().digest_size * 2


def test_collection_imports_do_not_require_manifest_or_endpoint(
    fork_framework, monkeypatch
):
    monkeypatch.delenv(fork_framework.MANIFEST_ENV, raising=False)
    monkeypatch.delenv("OWNER_RH_ARCHIVE_TEST", raising=False)
    assert fork_framework.qualification_mode({}) == "disabled"
    assert Path(__file__).is_file()


def test_node_id_classification_mapping_is_complete_and_canonical(
    fork_framework, pytestconfig
):
    mapping = pytestconfig.stash[fork_framework.NODE_CLASSIFICATION_STASH]
    deselected = pytestconfig.stash[
        fork_framework.DESELECTED_NODE_IDS_STASH
    ]
    assert mapping
    assert tuple(mapping) == tuple(sorted(mapping))
    assert set(mapping.values()) <= fork_framework.RESULT_VOCABULARY
    assert all(
        node_id.startswith("tests/deployment/fork/")
        for node_id in mapping
    )
    mode = fork_framework.qualification_mode(os.environ)
    first = fork_framework.node_classification_bytes(
        mapping,
        deselected_node_ids=deselected,
        mode=mode,
    )
    second = fork_framework.node_classification_bytes(
        dict(mapping),
        deselected_node_ids=deselected,
        mode=mode,
    )
    assert first == second
    artifact = json.loads(first)
    assert artifact["node_count"] == len(mapping)
    assert artifact["deselected_node_ids"] == list(deselected)
    assert artifact["ordered_node_sha256"] == (
        fork_framework.ordered_node_digest(tuple(mapping))
    )
    requested_roots = {
        Path(value).resolve()
        for value in pytestconfig.args
        if not value.startswith("-")
    }
    if fork_framework.SUITE_ROOT.resolve() not in requested_roots:
        return
    assert len(mapping) == EXPECTED_NODE_COUNT
    assert artifact["ordered_node_sha256"] == EXPECTED_NODE_DIGEST
    assert dict(Counter(mapping.values())) == EXPECTED_CLASS_COUNTS[mode]
    assert hashlib.sha256(first).hexdigest() == (
        EXPECTED_CLASSIFICATION_SHA256[mode]
    )


def test_safe_default_deselection_set_is_exact(
    fork_framework, pytestconfig, safe_default_deselection_reason
):
    assert "safe default" in safe_default_deselection_reason
    deselected = pytestconfig.stash[
        fork_framework.DESELECTED_NODE_IDS_STASH
    ]
    mapping = pytestconfig.stash[fork_framework.NODE_CLASSIFICATION_STASH]
    expected = tuple(
        sorted(
            node_id
            for node_id, classification in mapping.items()
            if classification == "deselected-safe-default"
        )
    )
    assert deselected == expected


def test_archive_node_classification_changes_only_with_exact_opt_in(
    fork_framework,
):
    assert (
        fork_framework.classify_collected_node(
            mode="disabled", archive_required=True
        )
        == "deselected-safe-default"
    )
    assert (
        fork_framework.classify_collected_node(
            mode="read-only-archive-fork", archive_required=True
        )
        == "qualifying"
    )
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_NODE_CLASSIFICATION_CONTRADICTION",
    ):
        fork_framework.classify_collected_node(
            mode="disabled",
            archive_required=True,
            explicit="supporting",
        )
