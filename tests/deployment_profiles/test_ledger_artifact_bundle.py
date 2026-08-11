"""DRAFT — owner approval required before integration or use."""

import json
import os
import subprocess
import sys

import pytest

from scripts.proposals import build_ledger_artifact_bundle as builder
from scripts.proposals import ledger_robinhood_profile as profile


@pytest.fixture(scope="module")
def bundle():
    return builder.build_bundle(
        builder_head="0" * 40,
        require_clean=False,
    )


def test_r2_constructor_encoding_is_exact_three_word_0x64_profile():
    arguments = profile.load_manifest()["constructor"]["ordered_arguments"]
    encoded = bytes.fromhex(
        builder.encode_constructor(arguments).removeprefix("0x")
    )
    assert len(encoded) == 96
    assert encoded[12:32].hex() == arguments[0][2:].lower()
    assert encoded[44:64].hex() == arguments[1][2:].lower()
    assert encoded[64:96] == b"\x00" * 31 + b"\x64"


def test_r2_bundle_separates_baseline_builder_and_compiler_input(bundle):
    assert bundle["baseline"] == (
        "a86650b187c523f27c92f05bfe959d06840025a6"
    )
    assert bundle["builder_head"] == "0" * 40
    assert bundle["compiler"]["transitive_compiler_input_integrity"] == (
        "9fb8e2769edfadc839c478c40859a4c89"
        "b53ac5a4548c520b32bf5f8c8052d80"
    )
    assert len(
        {
            bundle["baseline"],
            bundle["builder_head"],
            bundle["compiler"]["transitive_compiler_input_integrity"],
        }
    ) == 3


def test_r2_bundle_records_reviewed_source_abi_and_template_artifacts(bundle):
    assert bundle["source"] == {
        "path": "contracts/data/Ledger.vy",
        "sha256": (
            "c98c748511a26da7a7e7cc9ae158db00"
            "8e4c95fca18d393232081188ed1ef5a6"
        ),
    }
    assert bundle["abi"]["committed_file_sha256"] == (
        "d5dc29b53051f37a56a1e92b6787ef28"
        "6f97f764ca06d7d2b5ed96a8057b8f33"
    )
    assert bundle["artifacts"]["creation_bytecode"] == {
        "sha256": (
            "516c111fe8d220eb79a4f3a0cc7e1915"
            "c43510b8a0ab6651882309cef896f0aa"
        ),
        "size": 13_597,
    }
    assert bundle["artifacts"]["runtime_template"] == {
        "deployed_runtime_identity": False,
        "sha256": (
            "913b4299ce27692de499c022acd9d2dbf"
            "361563cda0e7763607879df402eefa9"
        ),
        "size": 13_178,
    }


def test_r2_bundle_records_immutable_bound_local_runtime_separately(bundle):
    bound = bundle["artifacts"]["immutable_bound_runtime"]
    template = bundle["artifacts"]["runtime_template"]
    assert bound["action_block_source_readback"] == profile.ARB_SYS
    assert bound["size"] == 13_306
    assert bound["size"] - template["size"] == 4 * 32
    assert bound["sha256"] == (
        "55ad52673ce6e395c41c3cdff41180e2"
        "3a9f89e6165d3809d5e59cfd7a3169c0"
    )


def test_r2_bundle_is_canonical_path_free_and_honestly_labeled(
    bundle,
    tmp_path,
):
    output = tmp_path / "bundle.json"
    builder.write_bundle(bundle, output)
    raw = output.read_bytes()
    assert raw == profile.canonical_json_bytes(json.loads(raw))
    assert raw.endswith(b"\n")
    assert b"\r" not in raw
    assert b"/Users/" not in raw
    assert b"timestamp" not in raw.lower()
    assert bundle["label"] == (
        "local reproduction evidence, not deployment evidence"
    )


def test_r2_clean_builder_guard_rejects_dirty_or_untracked_state(monkeypatch):
    responses = {
        ("rev-parse", "HEAD"): "1" * 40 + "\n",
        ("status", "--short"): "?? untracked\n",
    }

    def fake_git(arguments):
        return responses[tuple(arguments)]

    monkeypatch.setattr(builder, "_git_output", fake_git)
    with pytest.raises(
        builder.BundleBuildError,
        match="requires a clean worktree",
    ):
        builder.resolve_builder_head(require_clean=True)


def test_r2_clean_builder_guard_requires_generator_at_builder_head(
    monkeypatch,
):
    relative = str(builder.GENERATOR_PATH.relative_to(builder.ROOT))
    responses = {
        ("rev-parse", "HEAD"): "2" * 40 + "\n",
        ("status", "--short"): "",
        ("ls-files", "--error-unmatch", relative): "",
    }

    def fake_git(arguments):
        return responses[tuple(arguments)]

    monkeypatch.setattr(builder, "_git_output", fake_git)
    with pytest.raises(
        builder.BundleBuildError,
        match="generator is not tracked",
    ):
        builder.resolve_builder_head(require_clean=True)


def _build_bundle_in_fresh_process(cache_path):
    cache_path.mkdir(mode=0o700)
    environment = os.environ.copy()
    environment.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": ".",
            "RUN_BOA_CACHE": str(cache_path),
        }
    )
    code = (
        "import os, sys; "
        "from boa.interpret import set_cache_dir; "
        "set_cache_dir(os.environ['RUN_BOA_CACHE']); "
        "from scripts.proposals import build_ledger_artifact_bundle as b; "
        "from scripts.proposals import ledger_robinhood_profile as p; "
        "value=b.build_bundle(builder_head='0'*40, require_clean=False); "
        "sys.stdout.buffer.write(p.canonical_json_bytes(value))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=builder.ROOT,
        env=environment,
        check=False,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    return result.stdout


def test_r2_two_independent_processes_are_byte_deterministic(tmp_path):
    first = _build_bundle_in_fresh_process(tmp_path / "boa-first")
    second = _build_bundle_in_fresh_process(tmp_path / "boa-second")
    assert first == second
