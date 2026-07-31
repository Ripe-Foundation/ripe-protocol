from __future__ import annotations

import hashlib
from pathlib import Path


def test_implemented_path_ledger_is_sorted_unique_and_within_ceiling(
    fork_framework,
):
    ledger = fork_framework.IMPLEMENTED_PATH_LEDGER
    assert ledger == tuple(sorted(set(ledger)))
    assert len(ledger) == 15
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
