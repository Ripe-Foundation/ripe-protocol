from __future__ import annotations

import hashlib
import json
import os
from collections import Counter
from pathlib import Path

import pytest


EXPECTED_NODE_COUNT = 175
EXPECTED_NODE_DIGEST = (
    "829ea019d7028129c703a053111ea9f2f9d3e92b1fa0ddfc1c66a63e463e281a"
)
EXPECTED_CLASSIFICATION_SHA256 = {
    "disabled": (
        "04f2e307291eda018243c1934fae514edcd6672104a324eaf4039242098156a9"
    ),
    "read-only-archive-fork": (
        "a74f93ae6e44685cea403ef66f39febd38c5031ddc3f9100598d79aeb69e7534"
    ),
}
EXPECTED_CLASS_COUNTS = {
    "disabled": {
        "blocked": 4,
        "deselected-safe-default": 1,
        "supporting": 170,
    },
    "read-only-archive-fork": {
        "blocked": 4,
        "qualifying": 1,
        "supporting": 170,
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
    if fork_framework.qualification_mode(os.environ) == (
        fork_framework.DISABLED_MODE
    ):
        assert deselected == (
            "tests/deployment/fork/network/test_pin_archive.py::"
            "test_robinhood_archive_qualification_preflight",
        )
    else:
        assert deselected == ()


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
