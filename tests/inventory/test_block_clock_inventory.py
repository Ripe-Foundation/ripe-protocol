from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import check_block_clock_inventory as checker


def test_non_admitted_uniswap_sources_are_excluded_only_at_exact_bytes(
    tmp_path,
):
    assert set(checker.OPTIONAL_ARCHIVAL_VYPER_SHA256) == {
        "contracts/mock/MockUniswapV2Pair.vy",
        "contracts/mock/MockUniswapV2QuotePriceDesk.vy",
        "contracts/mock/MockUniswapV2RipeHq.vy",
        "contracts/mock/MockUniswapV2Token.vy",
        "contracts/priceSources/UniswapV2Prices.vy",
    }
    for relative, expected in checker.OPTIONAL_ARCHIVAL_VYPER_SHA256.items():
        source = REPOSITORY_ROOT / relative
        assert hashlib.sha256(source.read_bytes()).hexdigest() == expected
        assert checker._has_exact_optional_archival_bytes(REPOSITORY_ROOT, relative)

    relative = "contracts/priceSources/UniswapV2Prices.vy"
    changed = tmp_path / relative
    changed.parent.mkdir(parents=True)
    changed.write_bytes((REPOSITORY_ROOT / relative).read_bytes() + b"\n")
    assert not checker._has_exact_optional_archival_bytes(tmp_path, relative)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
INVENTORY_RELATIVE = Path("config/block-clock-inventory.json")
SCRIPT_RELATIVE = Path("scripts/check_block_clock_inventory.py")
ARTIFACT_EXPECTATIONS_RELATIVE = Path(
    "config/contract-artifact-expectations.json"
)
IMPLEMENTATION_RECORD_RELATIVE = Path(
    "docs/chains/rh/ledger-guard-implementation-record.md"
)
SHARED_BASIC_VAULT_RELATIVE = "contracts/vaults/modules/BasicVault.vy"
SHARED_STAB_VAULT_RELATIVE = "contracts/vaults/modules/StabVault.vy"
M3_CREDIT_RELATIVE = "contracts/core/CreditEngine.vy"
H04_MANIFEST_RELATIVE = "config/robinhood-parameters.json"
H04_GENERATOR_RELATIVE = "scripts/params/generate_robinhood_defaults.py"
H04_TEST_RELATIVE = "tests/config/test_defaults_robinhood.py"
H04_CONTRACT_RELATIVE = "contracts/config/DefaultsRobinhood.vy"


@pytest.fixture(scope="session")
def ripe_hq() -> None:
    """Override the repository's autouse deployment fixture for this stdlib guard."""


def _load_inventory(root: Path) -> dict:
    return json.loads((root / INVENTORY_RELATIVE).read_text(encoding="utf-8"))


def _write_inventory(root: Path, inventory: dict) -> None:
    (root / INVENTORY_RELATIVE).write_text(
        json.dumps(inventory, indent=2) + "\n", encoding="utf-8"
    )


def _replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert text.count(old) >= 1, f"{old!r} not found in {path}"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def _append(path: Path, text: str) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text)


def _codes(result: checker.CheckResult) -> set[str]:
    return {finding.code for finding in result.findings}


def _assert_failure(
    root: Path, code: str, *, path: str | None = None
) -> checker.CheckResult:
    result = checker.check_repository(root)
    assert not result.ok, result.output
    assert code in _codes(result), result.output
    if path is not None:
        matching = [
            finding
            for finding in result.findings
            if finding.code == code and finding.path == path
        ]
        assert matching, result.output
        assert matching[0].remediation
    return result


def _assert_pr61_artifact_metadata_failure(root: Path) -> checker.CheckResult:
    result = checker.check_repository(root)
    assert not result.ok, result.output
    assert "INV-SCHEMA-PR61-ARTIFACT-METADATA" in _codes(result), result.output
    assert "INV-SCHEMA-S5-LEGACY-FINGERPRINT" in _codes(result), result.output
    return result


@pytest.fixture(scope="session")
def approved_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    template = tmp_path_factory.mktemp("clock-inventory-template") / "repo"
    inventory = _load_inventory(REPOSITORY_ROOT)
    relative_paths = {
        INVENTORY_RELATIVE.as_posix(),
        SCRIPT_RELATIVE.as_posix(),
    }
    for collection in (
        "directOccurrences",
        "timestampContext",
        "cadenceCandidates",
        "secondsUnitCandidates",
        "allowedMixedClockFunctions",
        "vyperPathClassifications",
    ):
        relative_paths.update(
            str(record["path"])
            for record in inventory.get(collection, [])
            if "path" in record
        )
    relative_paths.update(
        str(record["path"])
        for record in inventory["currentBindings"]["sourcePaths"]
    )
    for relative in sorted(relative_paths):
        source = REPOSITORY_ROOT / relative
        destination = template / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return template


@pytest.fixture
def fixture_repo(tmp_path: Path, approved_template: Path) -> Path:
    destination = tmp_path / "repo"
    shutil.copytree(approved_template, destination)
    return destination


def test_clean_approved_fixture_passes_without_git_or_network(
    fixture_repo: Path,
) -> None:
    assert not (fixture_repo / ".git").exists()
    result = checker.check_repository(fixture_repo)
    assert result.ok, result.output
    assert "production_occurrences=102" in result.output
    assert "production_lines=97" in result.output
    assert "production_files=18" in result.output
    assert "bn_ids=32" in result.output
    assert "indirect_ids=1" in result.output
    assert "cadence_candidates=640" in result.output
    assert "timestamp_ids=11" in result.output
    assert "seconds_unit_candidates=70" in result.output
    assert "mixed_clock_functions=4" in result.output
    assert "vyper_paths=95" in result.output
    assert "current_bindings=6/4" in result.output
    assert (
        "current_state_sha256=" + checker.CURRENT_BINDINGS_STATE_SHA256
        in result.output
    )
    assert "post_s5_production_records=59" in result.output
    assert (
        "post_s5_production_sha256="
        + checker.CURRENT_PRODUCTION_INVENTORY_SHA256
        in result.output
    )
    assert "CLOCK_INVENTORY_NONPROD" in result.output
    assert "CLOCK_INVENTORY_NONPROD_CADENCE" in result.output
    assert "test=174" in result.output


def test_current_bindings_are_exact_and_preserve_historical_fingerprint(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    bindings = inventory["currentBindings"]

    assert set(bindings) == {
        "schemaVersion",
        "currentStateSha256",
        "sourcePaths",
        "timestampLines",
    }
    assert bindings["schemaVersion"] == checker.CURRENT_BINDINGS_SCHEMA_VERSION
    assert bindings["sourcePaths"] == list(
        checker.EXPECTED_CURRENT_SOURCE_BINDINGS
    )
    assert bindings["timestampLines"] == list(
        checker.EXPECTED_CURRENT_TIMESTAMP_BINDINGS
    )
    assert len({record["path"] for record in bindings["sourcePaths"]}) == 6
    assert len(
        {
            checker._current_binding_timestamp_key(record)
            for record in bindings["timestampLines"]
        }
    ) == 4
    assert checker.CURRENT_BINDINGS_STATE_SHA256 == (
        "cc6ccb4d0d966306623b78444bff793ce48ab867c6f4656451cf74852802fb38"
    )
    assert checker._current_bindings_fingerprint(bindings) == (
        checker.CURRENT_BINDINGS_STATE_SHA256
    )

    without_current = copy.deepcopy(inventory)
    without_current.pop("currentBindings")
    assert checker._s5_legacy_inventory_fingerprint(inventory, fixture_repo) == (
        checker.S5_LEGACY_INVENTORY_SHA256
    )
    assert checker._s5_legacy_inventory_fingerprint(
        without_current, fixture_repo
    ) == checker.S5_LEGACY_INVENTORY_SHA256
    assert checker._post_s5_production_inventory_fingerprint(inventory) == (
        checker.CURRENT_PRODUCTION_INVENTORY_SHA256
    )

    for record in bindings["sourcePaths"]:
        actual = hashlib.sha256(
            (fixture_repo / record["path"]).read_bytes()
        ).hexdigest()
        assert actual == record["currentContentSha256"]
    for record in bindings["timestampLines"]:
        raw_line = (fixture_repo / record["path"]).read_bytes().splitlines(
            keepends=True
        )[record["currentLine"] - 1]
        assert hashlib.sha256(raw_line).hexdigest() == record[
            "currentLineSha256"
        ]
        assert raw_line.decode().removesuffix("\n") == record["currentLineText"]


@pytest.mark.parametrize(
    "mutation",
    ["addition", "removal", "mutation", "duplication", "reordering"],
)
@pytest.mark.parametrize("collection", ["sourcePaths", "timestampLines"])
def test_current_bindings_structural_drift_fails_closed(
    fixture_repo: Path,
    mutation: str,
    collection: str,
) -> None:
    inventory = _load_inventory(fixture_repo)
    bindings = inventory["currentBindings"]
    records = bindings[collection]
    if mutation == "addition":
        added = copy.deepcopy(records[0])
        if collection == "sourcePaths":
            added["path"] = "contracts/mock/UnexpectedMorphoV2.vy"
        else:
            added["function"] = "_unexpectedTimestamp"
        records.append(added)
    elif mutation == "removal":
        records.pop()
    elif mutation == "mutation":
        if collection == "sourcePaths":
            records[0]["currentContentSha256"] = "0" * 64
        else:
            records[0]["currentLineText"] += "  # mutation"
    elif mutation == "duplication":
        records.append(copy.deepcopy(records[0]))
    else:
        records[0], records[1] = records[1], records[0]

    # Repinning the inventory field alone cannot acquire checker authority.
    bindings["currentStateSha256"] = checker._current_bindings_fingerprint(
        bindings
    )
    _write_inventory(fixture_repo, inventory)
    result = _assert_failure(
        fixture_repo, "INV-SCHEMA-CURRENT-BINDINGS-FINGERPRINT"
    )
    assert "INV-SCHEMA-CURRENT-BINDINGS" in _codes(result)
    if mutation == "duplication":
        assert "INV-SCHEMA-CURRENT-BINDINGS-DUPLICATE" in _codes(result)


def test_current_binding_source_drift_fails_closed(fixture_repo: Path) -> None:
    path = fixture_repo / "contracts/mock/MockMorphoV2Factory.vy"
    _append(path, "\n# source drift\n")
    _assert_failure(
        fixture_repo,
        "INV-CURRENT-SOURCE-HASH",
        path="contracts/mock/MockMorphoV2Factory.vy",
    )


def test_current_binding_line_move_fails_closed(fixture_repo: Path) -> None:
    binding = _load_inventory(fixture_repo)["currentBindings"][
        "timestampLines"
    ][0]
    path = fixture_repo / binding["path"]
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    lines.insert(binding["currentLine"] - 1, "\n")
    path.write_text("".join(lines), encoding="utf-8")
    _assert_failure(
        fixture_repo,
        "INV-CURRENT-TIMESTAMP-LINE",
        path=binding["path"],
    )


def test_current_binding_line_content_drift_fails_closed(
    fixture_repo: Path,
) -> None:
    binding = _load_inventory(fixture_repo)["currentBindings"][
        "timestampLines"
    ][0]
    path = fixture_repo / binding["path"]
    _replace_once(
        path,
        binding["currentLineText"],
        binding["currentLineText"] + "  # drift",
    )
    _assert_failure(
        fixture_repo,
        "INV-CURRENT-TIMESTAMP-LINE",
        path=binding["path"],
    )


def test_source_authority_batch_preserves_historical_fingerprints(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    batches = (
        (
            checker._source_authority_direct_records(inventory),
            checker.SOURCE_AUTHORITY_DIRECT_RECORD_COUNT,
            checker.SOURCE_AUTHORITY_DIRECT_RECORDS_SHA256,
        ),
        (
            checker._source_authority_cadence_records(inventory),
            checker.SOURCE_AUTHORITY_CADENCE_RECORD_COUNT,
            checker.SOURCE_AUTHORITY_CADENCE_RECORDS_SHA256,
        ),
        (
            checker._source_authority_seconds_records(inventory),
            checker.SOURCE_AUTHORITY_SECONDS_RECORD_COUNT,
            checker.SOURCE_AUTHORITY_SECONDS_RECORDS_SHA256,
        ),
        (
            checker._source_authority_path_records(inventory),
            checker.SOURCE_AUTHORITY_PATH_RECORD_COUNT,
            checker.SOURCE_AUTHORITY_PATH_RECORDS_SHA256,
        ),
        (
            checker._source_authority_cad_sites(inventory),
            checker.SOURCE_AUTHORITY_CAD_SITE_COUNT,
            checker.SOURCE_AUTHORITY_CAD_SITES_SHA256,
        ),
    )
    assert checker._is_exact_source_authority_batch(inventory)
    for records, expected_count, expected_fingerprint in batches:
        assert len(records) == expected_count
        assert checker._records_fingerprint(records) == expected_fingerprint
    # The replaced JSON-first H-04 identities remain immutable historical facts.
    assert checker.H04_CADENCE_RECORD_COUNT == 116
    assert checker.H04_CADENCE_RECORDS_SHA256 == (
        "d0d0e3ca3ac472b1a709a9525e9ad38d5b76c5337b4e540c3ca10b7c0dcddf05"
    )
    assert checker.H04_CAD_SITE_COUNT == 6
    assert checker.H04_CAD_SITES_SHA256 == (
        "8ffb9dd92c225d4cacea6827194bf3b42eb5cb2efaf6729f6aa1f083503f42ee"
    )
    exact = checker._exact_source_authority_record_fingerprints(inventory)
    assert tuple(map(len, exact)) == (3, 121, 12, 1, 5)
    assert checker._s5_legacy_inventory_fingerprint(inventory) == (
        checker.S5_LEGACY_INVENTORY_SHA256
    )
    assert checker._post_s5_production_inventory_fingerprint(inventory) == (
        checker.CURRENT_PRODUCTION_INVENTORY_SHA256
    )


def test_transaction_executor_cadence_batch_is_exact_and_additive(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    records = checker._transaction_executor_cadence_records(inventory)

    assert checker._is_exact_transaction_executor_cadence_batch(inventory)
    assert len(records) == checker.TRANSACTION_EXECUTOR_CADENCE_RECORD_COUNT == 7
    assert checker._records_fingerprint(records) == (
        checker.TRANSACTION_EXECUTOR_CADENCE_RECORDS_SHA256
    )
    assert [record["path"] for record in records] == [
        "scripts/utils/migration_runner.py",
        "scripts/utils/robinhood_backends.py",
        "scripts/utils/robinhood_backends.py",
        "scripts/utils/robinhood_backends.py",
        "scripts/utils/robinhood_executor.py",
        "scripts/utils/robinhood_executor.py",
        "tests/deployment/robinhood_execution_support.py",
    ]
    assert [record["semanticIds"] for record in records] == [
        ["BN-027", "BN-028"],
        ["BN-024"],
        ["BN-024"],
        ["BN-024"],
        [],
        [],
        ["BN-027", "BN-028"],
    ]
    assert all(
        record["semanticReview"]
        == {
            "owner": "protocol/security",
            "status": "reviewed",
            "commit": checker.SOURCE_AUTHORITY_REVIEW_COMMIT,
        }
        for record in records
    )
    assert checker._s5_legacy_inventory_fingerprint(inventory) == (
        checker.S5_LEGACY_INVENTORY_SHA256
    )
    assert checker._post_s5_production_inventory_fingerprint(inventory) == (
        checker.CURRENT_PRODUCTION_INVENTORY_SHA256
    )


def test_transaction_executor_cadence_batch_removal_fails_closed(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    removed = checker._transaction_executor_cadence_records(inventory)[0]
    inventory["cadenceCandidates"].remove(removed)

    assert not checker._is_exact_transaction_executor_cadence_batch(inventory)
    assert checker._s5_legacy_inventory_fingerprint(inventory) != (
        checker.S5_LEGACY_INVENTORY_SHA256
    )
    _write_inventory(fixture_repo, inventory)
    _assert_failure(
        fixture_repo,
        "INV-SCHEMA-TRANSACTION-EXECUTOR-CADENCE-BATCH",
    )


def test_transaction_executor_cadence_batch_cannot_widen_by_path(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    extra = copy.deepcopy(
        checker._transaction_executor_cadence_records(inventory)[0]
    )
    extra["function"] = "future_executor_branch"
    inventory["cadenceCandidates"].append(extra)

    assert not checker._is_exact_transaction_executor_cadence_batch(inventory)
    assert checker._s5_legacy_inventory_fingerprint(inventory) != (
        checker.S5_LEGACY_INVENTORY_SHA256
    )
    _write_inventory(fixture_repo, inventory)
    _assert_failure(
        fixture_repo,
        "INV-SCHEMA-TRANSACTION-EXECUTOR-CADENCE-BATCH",
    )


def test_pr61_exact_batch_preserves_the_frozen_legacy_fingerprint(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    batches = (
        (
            checker._pr61_direct_records(inventory),
            checker.PR61_DIRECT_RECORD_COUNT,
            checker.PR61_DIRECT_RECORDS_SHA256,
        ),
        (
            checker._pr61_cadence_records(inventory),
            checker.PR61_CADENCE_RECORD_COUNT,
            checker.PR61_CADENCE_RECORDS_SHA256,
        ),
        (
            checker._pr61_seconds_records(inventory),
            checker.PR61_SECONDS_RECORD_COUNT,
            checker.PR61_SECONDS_RECORDS_SHA256,
        ),
        (
            checker._pr61_path_records(inventory),
            checker.PR61_PATH_RECORD_COUNT,
            checker.PR61_PATH_RECORDS_SHA256,
        ),
    )
    assert checker._is_exact_pr61_reconciliation(inventory)
    for records, expected_count, expected_fingerprint in batches:
        assert len(records) == expected_count
        assert checker._records_fingerprint(records) == expected_fingerprint
    assert (
        inventory["reviewProvenance"]["pr61ReviewCommit"]
        == checker.PR61_REVIEW_COMMIT
    )
    assert checker._s5_legacy_inventory_fingerprint(inventory) == (
        checker.S5_LEGACY_INVENTORY_SHA256
    )
    assert checker._post_s5_production_inventory_fingerprint(inventory) == (
        checker.CURRENT_PRODUCTION_INVENTORY_SHA256
    )


def test_pr61_exact_artifact_layout_metadata_package_preserves_authority(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    records = checker._pr61_artifact_layout_metadata_records(inventory)
    path_records = checker._pr61_artifact_expectations_cadence_records(
        inventory
    )

    assert checker._is_exact_pr61_artifact_layout_metadata(
        inventory, fixture_repo
    )
    assert len(records) == checker.PR61_ARTIFACT_LAYOUT_METADATA_RECORD_COUNT == 8
    assert checker._records_fingerprint(records) == (
        checker.PR61_ARTIFACT_LAYOUT_METADATA_RECORDS_SHA256
    )
    assert len(path_records) == (
        checker.PR61_ARTIFACT_EXPECTATIONS_CADENCE_RECORD_COUNT
    ) == 11
    assert checker._records_fingerprint(path_records) == (
        checker.PR61_ARTIFACT_EXPECTATIONS_CADENCE_RECORDS_SHA256
    )
    artifact_path = fixture_repo / ARTIFACT_EXPECTATIONS_RELATIVE
    artifact_bytes = artifact_path.read_bytes()
    assert hashlib.sha256(artifact_bytes).hexdigest() == (
        checker.CURRENT_ARTIFACT_EXPECTATIONS_SHA256
    )
    legacy_artifact = json.loads(artifact_bytes)
    legacy_artifact["contracts"].pop("DefaultsRobinhood")
    checker._restore_pr61_artifact_expectations_legacy(legacy_artifact)
    legacy_bytes = (
        json.dumps(legacy_artifact, indent=2, sort_keys=True) + "\n"
    ).encode()
    assert hashlib.sha256(legacy_bytes).hexdigest() == (
        checker.PR61_ARTIFACT_EXPECTATIONS_SHA256
    )
    assert checker._s5_legacy_inventory_fingerprint(
        inventory, fixture_repo
    ) == checker.S5_LEGACY_INVENTORY_SHA256
    assert checker._post_s5_production_inventory_fingerprint(inventory) == (
        checker.CURRENT_PRODUCTION_INVENTORY_SHA256
    )


def test_every_field_of_every_pr61_artifact_metadata_record_is_bound(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    field_mutations = (
        (("path",), "config/future-artifact-expectations.json"),
        (("function",), "future_group"),
        (("pattern",), "cadence-comment"),
        (("matchedText",), '"futureDelay":'),
        (("normalizedSnippet",), '"futureDelay": {'),
        (("ordinalInFunction",), 99),
        (("reviewedLine",), 99),
        (("classification",), "tooling"),
        (("semanticIds",), ["CAD-001"]),
        (("reviewDomain",), "future-surface"),
        (("semanticReview", "owner"), "engineering/tooling"),
        (("semanticReview", "status"), "ignored"),
        (("semanticReview", "commit"), "0" * 40),
    )

    for record_index in range(
        checker.PR61_ARTIFACT_LAYOUT_METADATA_RECORD_COUNT
    ):
        for field_path, replacement in field_mutations:
            mutated = copy.deepcopy(inventory)
            record = checker._pr61_artifact_layout_metadata_records(mutated)[
                record_index
            ]
            target = record
            for key in field_path[:-1]:
                target = target[key]
            target[field_path[-1]] = replacement
            assert not checker._is_exact_pr61_artifact_layout_metadata(
                mutated, fixture_repo
            )
            assert checker._s5_legacy_inventory_fingerprint(
                mutated, fixture_repo
            ) != checker.S5_LEGACY_INVENTORY_SHA256


def test_pr61_artifact_metadata_tuple_drift_reports_legacy_fingerprint(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    checker._pr61_artifact_layout_metadata_records(inventory)[0][
        "reviewedLine"
    ] += 1
    _write_inventory(fixture_repo, inventory)
    _assert_pr61_artifact_metadata_failure(fixture_repo)


def test_pr61_artifact_metadata_record_removal_fails_closed(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    removed = checker._pr61_artifact_layout_metadata_records(inventory)[3]
    inventory["cadenceCandidates"].remove(removed)
    _write_inventory(fixture_repo, inventory)
    _assert_pr61_artifact_metadata_failure(fixture_repo)


def test_pr61_artifact_metadata_ninth_lookalike_fails_closed(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    future = copy.deepcopy(
        checker._pr61_artifact_layout_metadata_records(inventory)[0]
    )
    future["matchedText"] = '"futureDelay":'
    future["normalizedSnippet"] = '"futureDelay": {'
    future["reviewedLine"] = 1200
    inventory["cadenceCandidates"].append(future)
    _write_inventory(fixture_repo, inventory)
    _assert_pr61_artifact_metadata_failure(fixture_repo)


def test_pr61_artifact_metadata_reordering_fails_closed(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    records = checker._pr61_artifact_layout_metadata_records(inventory)
    first_index = inventory["cadenceCandidates"].index(records[0])
    second_index = inventory["cadenceCandidates"].index(records[1])
    inventory["cadenceCandidates"][first_index] = records[1]
    inventory["cadenceCandidates"][second_index] = records[0]
    _write_inventory(fixture_repo, inventory)
    _assert_pr61_artifact_metadata_failure(fixture_repo)


def test_pr61_artifact_expectations_byte_drift_fails_closed(
    fixture_repo: Path,
) -> None:
    _append(fixture_repo / ARTIFACT_EXPECTATIONS_RELATIVE, "\n")
    _assert_pr61_artifact_metadata_failure(fixture_repo)


def test_pr61_artifact_metadata_provenance_drift_fails_closed(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    inventory["reviewProvenance"]["pr61ReviewCommit"] = "0" * 40
    _write_inventory(fixture_repo, inventory)
    _assert_pr61_artifact_metadata_failure(fixture_repo)


def test_general_remediation_registry_expansion_cannot_escape_legacy_authority(
    fixture_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    future_key = (
        "config/future-artifact-expectations.json",
        "<module>",
        "block-default-key",
        '"futureDelay":',
        '"futureDelay": {',
        1,
    )
    monkeypatch.setattr(
        checker,
        "REVIEWER_REMEDIATION_CADENCE_KEYS",
        checker.REVIEWER_REMEDIATION_CADENCE_KEYS | {future_key},
    )
    _assert_pr61_artifact_metadata_failure(fixture_repo)


def test_profile1_configuration_registry_append_is_exact_and_preserves_s5(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    records = checker._profile1_configuration_cadence_records(inventory)
    old_registry = checker.REVIEWER_REMEDIATION_CADENCE_KEYS - {
        checker.PROFILE1_CONFIGURATION_CADENCE_KEY
    }

    assert len(old_registry) == 9
    assert checker._key_set_fingerprint(old_registry) == (
        "0739c77da0d92999c241eb6b9e9a54dea4bac749a9a682afb4b3a4a0ca5a4251"
    )
    assert len(checker.REVIEWER_REMEDIATION_CADENCE_KEYS) == 10
    assert checker._key_set_fingerprint(
        checker.REVIEWER_REMEDIATION_CADENCE_KEYS
    ) == (
        "cb64d7b0dbd1d8e278b83b248ec7c457137a24a16aa7247cc2deab9fa9b5c4df"
    )
    assert checker.REVIEWER_REMEDIATION_CADENCE_KEYS - old_registry == {
        checker.PROFILE1_CONFIGURATION_CADENCE_KEY
    }
    assert len(records) == checker.PROFILE1_CONFIGURATION_CADENCE_RECORD_COUNT
    assert checker._records_fingerprint(records) == (
        checker.PROFILE1_CONFIGURATION_CADENCE_RECORDS_SHA256
    )
    assert records[0]["classification"] == "test"
    assert records[0]["semanticIds"] == ["BN-027", "BN-028"]
    assert records[0]["semanticReview"]["commit"] == (
        checker.PROFILE1_CONFIGURATION_PROVENANCE_COMMIT
    )
    assert checker._is_exact_reviewer_remediation_cadence_registry(inventory)
    assert checker._s5_legacy_inventory_fingerprint(inventory) == (
        checker.S5_LEGACY_INVENTORY_SHA256
    )


@pytest.mark.parametrize(
    ("field_path", "replacement"),
    (
        (("path",), "tests/deployment/test_future_omissions.py"),
        (("function",), "test_future_profile1_safety_envelope"),
        (("pattern",), "block-default-key"),
        (("matchedText",), "futureCadence"),
        (("normalizedSnippet",), '"futureCadence",'),
        (("ordinalInFunction",), 2),
        (("reviewedLine",), 668),
        (("classification",), "support"),
        (("semanticIds",), ["BN-027"]),
        (("reviewDomain",), "future-domain"),
        (("semanticReview", "owner"), "engineering/tooling"),
        (("semanticReview", "status"), "pending"),
        (("semanticReview", "commit"), checker.HARDENING_REVIEW_COMMIT),
    ),
)
def test_profile1_configuration_record_drift_fails_closed(
    fixture_repo: Path,
    field_path: tuple[str, ...],
    replacement: object,
) -> None:
    inventory = _load_inventory(fixture_repo)
    record = checker._profile1_configuration_cadence_records(inventory)[0]
    target = record
    for field in field_path[:-1]:
        target = target[field]
    target[field_path[-1]] = replacement

    assert not checker._is_exact_reviewer_remediation_cadence_registry(
        inventory
    )
    assert checker._s5_legacy_inventory_fingerprint(inventory) != (
        checker.S5_LEGACY_INVENTORY_SHA256
    )
    _write_inventory(fixture_repo, inventory)
    _assert_pr61_artifact_metadata_failure(fixture_repo)


def test_profile1_configuration_record_removal_fails_closed(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    record = checker._profile1_configuration_cadence_records(inventory)[0]
    inventory["cadenceCandidates"].remove(record)

    assert not checker._is_exact_reviewer_remediation_cadence_registry(
        inventory
    )
    assert checker._s5_legacy_inventory_fingerprint(inventory) != (
        checker.S5_LEGACY_INVENTORY_SHA256
    )
    _write_inventory(fixture_repo, inventory)
    _assert_pr61_artifact_metadata_failure(fixture_repo)


def test_profile1_configuration_record_duplication_fails_closed(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    record = checker._profile1_configuration_cadence_records(inventory)[0]
    inventory["cadenceCandidates"].append(copy.deepcopy(record))

    assert not checker._is_exact_reviewer_remediation_cadence_registry(
        inventory
    )
    assert checker._s5_legacy_inventory_fingerprint(inventory) != (
        checker.S5_LEGACY_INVENTORY_SHA256
    )
    _write_inventory(fixture_repo, inventory)
    _assert_pr61_artifact_metadata_failure(fixture_repo)


def test_real_repository_inventory_is_complete() -> None:
    result = checker.check_repository(REPOSITORY_ROOT)
    assert result.ok, result.output


def test_pr61_direct_tuple_drift_fails_closed(fixture_repo: Path) -> None:
    inventory = _load_inventory(fixture_repo)
    checker._pr61_direct_records(inventory)[0]["reviewedLine"] += 1
    assert not checker._is_exact_pr61_reconciliation(inventory)
    assert checker._s5_legacy_inventory_fingerprint(inventory) != (
        checker.S5_LEGACY_INVENTORY_SHA256
    )
    _write_inventory(fixture_repo, inventory)
    _assert_failure(fixture_repo, "INV-SCHEMA-PR61-RECONCILIATION")


def test_pr61_path_provenance_drift_fails_closed(fixture_repo: Path) -> None:
    inventory = _load_inventory(fixture_repo)
    checker._pr61_path_records(inventory)[0]["semanticReview"]["commit"] = (
        checker.HARDENING_REVIEW_COMMIT
    )
    assert not checker._is_exact_pr61_reconciliation(inventory)
    assert checker._s5_legacy_inventory_fingerprint(inventory) != (
        checker.S5_LEGACY_INVENTORY_SHA256
    )
    _write_inventory(fixture_repo, inventory)
    _assert_failure(fixture_repo, "INV-SCHEMA-PR61-RECONCILIATION")


def test_pr61_removed_test_record_gains_no_authority(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    inventory["cadenceCandidates"].append(
        checker._pr61_removed_test_record()
    )
    assert not checker._is_exact_pr61_reconciliation(inventory)
    assert checker._s5_legacy_inventory_fingerprint(inventory) != (
        checker.S5_LEGACY_INVENTORY_SHA256
    )
    _write_inventory(fixture_repo, inventory)
    _assert_failure(fixture_repo, "INV-SCHEMA-PR61-RECONCILIATION")


def test_source_authoritative_defaults_has_exact_production_admission(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    source = fixture_repo / H04_CONTRACT_RELATIVE
    assert source.is_file()
    record = next(
        record
        for record in inventory["vyperPathClassifications"]
        if record["path"] == H04_CONTRACT_RELATIVE
    )
    assert record["classification"] == "production"
    assert record["contentSha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert checker.POST_S5_PRODUCTION_INVENTORY_SHA256 == (
        "07fc837ee5c9c56a4cf979c64e3d678753eeb6c263e4100d7a1f0cb4704f2122"
    )
    assert checker.CURRENT_PRODUCTION_INVENTORY_SHA256 == (
        "7e2333b58353a26f68ef91287fd169bf129ca72b083af3a3b232107df75e79d4"
    )
    assert checker.S5_LEGACY_INVENTORY_SHA256 == (
        "924a559075d5b96bcac3f73d28390deee3b436fe5500adc4fb6bf769282217b4"
    )


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        pytest.param("path", "config/robinhood-parameters-moved.json", id="path"),
        pytest.param("function", "different_function", id="function"),
        pytest.param("pattern", "cadence-comment", id="pattern"),
        pytest.param("matchedText", "ripePerBlock", id="matched-text"),
        pytest.param("normalizedSnippet", "mutated snippet", id="snippet"),
        pytest.param("ordinalInFunction", 999, id="ordinal"),
        pytest.param("reviewedLine", 999, id="line"),
        pytest.param("classification", "other", id="classification"),
        pytest.param("semanticIds", ["BN-030"], id="semantic-id"),
        pytest.param("reviewDomain", "timestamp-surface", id="review-domain"),
        pytest.param("semanticReview.owner", "engineering/tooling", id="owner"),
        pytest.param("semanticReview.status", "ignored", id="status"),
        pytest.param("semanticReview.commit", "0" * 40, id="provenance"),
    ],
)
def test_h04_record_tuple_drift_never_inherits_legacy_exclusion(
    fixture_repo: Path,
    field: str,
    replacement: object,
) -> None:
    inventory = _load_inventory(fixture_repo)
    record = next(
        item
        for item in checker._source_authority_cadence_records(inventory)
        if "CAD-001" not in item["semanticIds"]
    )
    if field.startswith("semanticReview."):
        record["semanticReview"][field.split(".", 1)[1]] = replacement
    else:
        record[field] = replacement
    assert not checker._is_exact_source_authority_batch(inventory)
    assert checker._s5_legacy_inventory_fingerprint(inventory) != (
        checker.S5_LEGACY_INVENTORY_SHA256
    )
    _write_inventory(fixture_repo, inventory)
    _assert_failure(fixture_repo, "INV-SCHEMA-SOURCE-AUTHORITY-BATCH")


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        pytest.param("path", "config/robinhood-parameters-moved.json", id="path"),
        pytest.param("function", "different_function", id="function"),
        pytest.param("pattern", "cadence-comment", id="pattern"),
        pytest.param("matchedText", "ripePerBlock", id="matched-text"),
        pytest.param("normalizedSnippet", "mutated snippet", id="snippet"),
        pytest.param("ordinalInFunction", 999, id="ordinal"),
        pytest.param("reviewedLine", 999, id="line"),
        pytest.param("classification", "other", id="classification"),
        pytest.param("semanticIds", ["BN-029"], id="semantic-id"),
        pytest.param("reviewDomain", "other", id="review-domain"),
    ],
)
def test_h04_cad_mirror_metadata_drift_is_not_excluded(
    fixture_repo: Path,
    field: str,
    replacement: object,
) -> None:
    inventory = _load_inventory(fixture_repo)
    checker._source_authority_cad_sites(inventory)[0][field] = replacement
    assert not checker._is_exact_source_authority_batch(inventory)
    assert checker._s5_legacy_inventory_fingerprint(inventory) != (
        checker.S5_LEGACY_INVENTORY_SHA256
    )
    _write_inventory(fixture_repo, inventory)
    _assert_failure(fixture_repo, "INV-SCHEMA-SOURCE-AUTHORITY-BATCH")


@pytest.mark.parametrize(
    ("field", "replacement", "code"),
    [
        pytest.param(
            "owner",
            "protocol/security",
            "INV-SCHEMA-OWNER",
            id="owner",
        ),
        pytest.param(
            "status",
            "ignored",
            "INV-SCHEMA-STATUS",
            id="status",
        ),
        pytest.param(
            "commit",
            checker.H04_REVIEW_COMMIT,
            "INV-SCHEMA-PROVENANCE",
            id="provenance",
        ),
    ],
)
def test_h04_cad_parent_authority_drift_never_inherits_legacy_exclusion(
    fixture_repo: Path,
    field: str,
    replacement: str,
    code: str,
) -> None:
    inventory = _load_inventory(fixture_repo)
    parent = next(
        record
        for record in inventory["indirectCadence"]
        if record["id"] == "CAD-001"
    )
    parent["semanticReview"][field] = replacement
    assert checker._is_exact_source_authority_batch(inventory)
    assert checker._s5_legacy_inventory_fingerprint(inventory) != (
        checker.S5_LEGACY_INVENTORY_SHA256
    )
    _write_inventory(fixture_repo, inventory)
    _assert_failure(fixture_repo, code)


def test_extending_exact_h04_record_set_gains_no_exclusion_authority(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    inventory["cadenceCandidates"].append(
        json.loads(
            json.dumps(checker._source_authority_cadence_records(inventory)[0])
        )
    )
    assert not checker._is_exact_source_authority_batch(inventory)
    assert checker._exact_source_authority_record_fingerprints(inventory) == (
        frozenset(),
    ) * 5
    assert checker._s5_legacy_inventory_fingerprint(inventory) != (
        checker.S5_LEGACY_INVENTORY_SHA256
    )
    _write_inventory(fixture_repo, inventory)
    _assert_failure(fixture_repo, "INV-SCHEMA-SOURCE-AUTHORITY-BATCH")


def test_h04_source_content_drift_is_new_cadence(fixture_repo: Path) -> None:
    _append(fixture_repo / H04_GENERATOR_RELATIVE, "\n# ripePerBlock\n")
    _assert_failure(
        fixture_repo,
        "INV-CADENCE-NEW",
        path=H04_GENERATOR_RELATIVE,
    )


def test_h04_source_deletion_fails_candidate_completeness(
    fixture_repo: Path,
) -> None:
    (fixture_repo / H04_MANIFEST_RELATIVE).unlink()
    _assert_failure(
        fixture_repo,
        "INV-CADENCE-MISSING",
        path=H04_MANIFEST_RELATIVE,
    )


def test_h04_sibling_path_substitution_fails_both_directions(
    fixture_repo: Path,
) -> None:
    sibling = fixture_repo / "config/robinhood-parameters-sibling.json"
    (fixture_repo / H04_MANIFEST_RELATIVE).rename(sibling)
    result = checker.check_repository(fixture_repo)
    assert not result.ok
    assert {"INV-CADENCE-NEW", "INV-CADENCE-MISSING"} <= _codes(result)


def test_future_h04_path_is_unknown_even_with_h04_review_labels(
    fixture_repo: Path,
) -> None:
    future_relative = "scripts/params/h04_future.py"
    future = fixture_repo / future_relative
    future.parent.mkdir(parents=True, exist_ok=True)
    future.write_text("# ripePerBlock\n", encoding="utf-8")
    inventory = _load_inventory(fixture_repo)
    candidate = checker._scan_candidates(
        fixture_repo,
        [future],
        inventory["productionRoots"],
        inventory["excludedProductionGlobs"],
        inventory["cadenceExcludedGlobs"],
    )[0]
    inventory["cadenceCandidates"].append(
        {
            "path": candidate.path,
            "function": candidate.function,
            "pattern": candidate.pattern,
            "matchedText": candidate.matched_text,
            "normalizedSnippet": candidate.normalized_snippet,
            "ordinalInFunction": candidate.ordinal,
            "reviewedLine": candidate.line,
            "classification": candidate.classification,
            "semanticIds": ["BN-024"],
            "reviewDomain": "cadence-surface",
            "semanticReview": {
                "owner": "protocol/security",
                "status": "reviewed",
                "commit": checker.H04_REVIEW_COMMIT,
            },
        }
    )
    _write_inventory(fixture_repo, inventory)
    result = checker.check_repository(fixture_repo)
    assert not result.ok
    assert "INV-SCHEMA-PROVENANCE" in _codes(result)
    assert checker._s5_legacy_inventory_fingerprint(inventory) != (
        checker.S5_LEGACY_INVENTORY_SHA256
    )


def test_extending_h04_path_predicate_does_not_gain_exclusion_authority(
    fixture_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inventory = _load_inventory(fixture_repo)
    extra = dict(checker._source_authority_cadence_records(inventory)[0])
    extra["path"] = "scripts/params/h04_future.py"
    inventory["cadenceCandidates"].append(extra)
    monkeypatch.setattr(
        checker,
        "SOURCE_AUTHORITY_CADENCE_PATHS",
        checker.SOURCE_AUTHORITY_CADENCE_PATHS
        | {"scripts/params/h04_future.py"},
    )
    assert not checker._is_exact_source_authority_batch(inventory)
    assert checker._s5_legacy_inventory_fingerprint(inventory) != (
        checker.S5_LEGACY_INVENTORY_SHA256
    )


def test_unknown_future_h04_cadence_file_gets_new_candidate_diagnostic(
    fixture_repo: Path,
) -> None:
    future = fixture_repo / "scripts/params/h04_unknown_future.py"
    future.parent.mkdir(parents=True, exist_ok=True)
    future.write_text("# ripePerBlock\n", encoding="utf-8")
    _assert_failure(
        fixture_repo,
        "INV-CADENCE-NEW",
        path="scripts/params/h04_unknown_future.py",
    )


def test_s5_review_artifact_scope_and_legacy_commits_are_exact(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    field = checker.S5_REVIEW_ARTIFACT_FIELD

    direct_records = {
        checker._record_key(record): record
        for record in inventory["directOccurrences"]
        if field in record
    }
    cadence_records = {
        checker._candidate_from_record(record): record
        for record in inventory["cadenceCandidates"]
        if field in record
    }
    path_records = {
        record["path"]: record
        for record in inventory["vyperPathClassifications"]
        if field in record
    }

    assert set(direct_records) == checker.S5_REVIEW_DIRECT_KEYS
    assert set(cadence_records) == checker.S5_REVIEW_CADENCE_KEYS
    assert set(path_records) == checker.S5_REVIEW_PATHS
    assert len(direct_records) + len(cadence_records) + len(path_records) == 24
    assert all(
        record[field] == checker.S5_REVIEW_ARTIFACT_SHA256
        for record in (
            list(direct_records.values())
            + list(cadence_records.values())
            + list(path_records.values())
        )
    )
    assert all(
        record["semanticReview"]["commit"] == checker.TRACK3_REVIEW_COMMIT
        for record in direct_records.values()
    )
    assert all(
        record["semanticReview"]["commit"]
        == checker.HARDENING_REVIEW_COMMIT
        for record in (
            list(cadence_records.values()) + list(path_records.values())
        )
    )
    assert (
        checker._s5_legacy_inventory_fingerprint(inventory)
        == checker.S5_LEGACY_INVENTORY_SHA256
    )
    assert (
        checker._post_s5_production_inventory_fingerprint(inventory)
        == checker.CURRENT_PRODUCTION_INVENTORY_SHA256
    )


def test_shared_basic_vault_record_is_exact_and_content_pinned(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    record = next(
        item
        for item in inventory["vyperPathClassifications"]
        if item["path"] == SHARED_BASIC_VAULT_RELATIVE
    )
    assert checker._is_reviewed_shared_basic_vault_record(record)
    assert record["classification"] == "production"
    assert record["contentSha256"] == checker.SHARED_BASIC_VAULT_SHA256
    assert (
        hashlib.sha256(
            (fixture_repo / SHARED_BASIC_VAULT_RELATIVE).read_bytes()
        ).hexdigest()
        == checker.SHARED_BASIC_VAULT_SHA256
    )
    result = checker.check_repository(fixture_repo)
    assert result.ok, result.output


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        pytest.param(
            "path",
            "contracts/vaults/GuardedErc20Moved.vy",
            id="path",
        ),
        pytest.param("contentSha256", "0" * 64, id="content-hash"),
        pytest.param("classification", "test", id="classification"),
    ],
)
def test_shared_basic_vault_inventory_drift_fails_current_fingerprint(
    fixture_repo: Path,
    field: str,
    replacement: str,
) -> None:
    inventory = _load_inventory(fixture_repo)
    record = next(
        item
        for item in inventory["vyperPathClassifications"]
        if item["path"] == SHARED_BASIC_VAULT_RELATIVE
    )
    record[field] = replacement
    _write_inventory(fixture_repo, inventory)
    _assert_failure(
        fixture_repo,
        "INV-SCHEMA-POST-S5-PRODUCTION-FINGERPRINT",
    )


def test_shared_basic_vault_source_content_drift_fails_exact_pin(
    fixture_repo: Path,
) -> None:
    _append(fixture_repo / SHARED_BASIC_VAULT_RELATIVE, "\n# drift fixture\n")
    _assert_failure(
        fixture_repo,
        "INV-PATH-BASIC-VAULT-CONTENT",
        path=SHARED_BASIC_VAULT_RELATIVE,
    )


def test_shared_stab_vault_record_is_exact_and_content_pinned(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    record = next(
        item
        for item in inventory["vyperPathClassifications"]
        if item["path"] == SHARED_STAB_VAULT_RELATIVE
    )
    assert checker._is_reviewed_shared_stab_vault_record(record)
    assert record["classification"] == "production"
    assert record["contentSha256"] == checker.SHARED_STAB_VAULT_SHA256
    assert (
        hashlib.sha256(
            (fixture_repo / SHARED_STAB_VAULT_RELATIVE).read_bytes()
        ).hexdigest()
        == checker.SHARED_STAB_VAULT_SHA256
    )
    result = checker.check_repository(fixture_repo)
    assert result.ok, result.output


def test_shared_stab_vault_source_content_drift_fails_exact_pin(
    fixture_repo: Path,
) -> None:
    _append(fixture_repo / SHARED_STAB_VAULT_RELATIVE, "\n# drift fixture\n")
    _assert_failure(
        fixture_repo,
        "INV-PATH-STAB-VAULT-CONTENT",
        path=SHARED_STAB_VAULT_RELATIVE,
    )


def test_shared_basic_vault_source_deletion_fails(fixture_repo: Path) -> None:
    (fixture_repo / SHARED_BASIC_VAULT_RELATIVE).unlink()
    _assert_failure(
        fixture_repo,
        "INV-PATH-MISSING",
        path=SHARED_BASIC_VAULT_RELATIVE,
    )


def test_shared_basic_vault_sibling_production_path_fails(
    fixture_repo: Path,
) -> None:
    relative = "contracts/vaults/FutureProtectedErc20.vy"
    path = fixture_repo / relative
    path.write_text("@external\ndef noop():\n    pass\n", encoding="utf-8")
    result = checker.check_repository(fixture_repo)
    assert "INV-PATH-NEW" in _codes(result), result.output
    finding = next(item for item in result.findings if item.code == "INV-PATH-NEW")
    assert finding.path == relative
    assert finding.actual == "production"


def test_future_production_admission_requires_new_controlling_fingerprint(
    fixture_repo: Path,
) -> None:
    relative = "contracts/vaults/FutureProtectedErc20.vy"
    path = fixture_repo / relative
    path.write_text("@external\ndef noop():\n    pass\n", encoding="utf-8")
    inventory = _load_inventory(fixture_repo)
    inventory["vyperPathClassifications"].append(
        {
            "path": relative,
            "classification": "production",
            "contentSha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "semanticReview": {
                "owner": "engineering/tooling",
                "status": "reviewed",
                "commit": checker.HARDENING_REVIEW_COMMIT,
            },
        }
    )
    assert (
        checker._post_s5_production_inventory_fingerprint(inventory)
        != checker.CURRENT_PRODUCTION_INVENTORY_SHA256
    )
    _write_inventory(fixture_repo, inventory)
    _assert_failure(
        fixture_repo,
        "INV-SCHEMA-POST-S5-PRODUCTION-FINGERPRINT",
    )


def test_m3_production_record_is_exact_and_content_pinned(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    record = next(
        item
        for item in inventory["vyperPathClassifications"]
        if item["path"] == M3_CREDIT_RELATIVE
    )
    assert checker._is_reviewed_m3_production_record(record)
    assert record["classification"] == "production"
    assert record["contentSha256"] == checker.M3_CREDIT_ENGINE_SHA256
    assert (
        checker.M3_CREDIT_ENGINE_SHA256
        != checker.M3_CREDIT_ENGINE_BASELINE_SHA256
    )
    assert (
        hashlib.sha256((fixture_repo / M3_CREDIT_RELATIVE).read_bytes()).hexdigest()
        == checker.M3_CREDIT_ENGINE_SHA256
    )
    assert (
        checker._s5_legacy_inventory_fingerprint(inventory)
        == checker.S5_LEGACY_INVENTORY_SHA256
    )
    result = checker.check_repository(fixture_repo)
    assert result.ok, result.output


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        pytest.param(
            "path",
            "contracts/core/CreditEngineMoved.vy",
            id="path",
        ),
        pytest.param("contentSha256", "0" * 64, id="content-hash"),
        pytest.param("classification", "test", id="classification"),
    ],
)
def test_m3_inventory_identity_drift_fails_current_and_legacy_fingerprints(
    fixture_repo: Path,
    field: str,
    replacement: str,
) -> None:
    inventory = _load_inventory(fixture_repo)
    record = next(
        item
        for item in inventory["vyperPathClassifications"]
        if item["path"] == M3_CREDIT_RELATIVE
    )
    record[field] = replacement
    _write_inventory(fixture_repo, inventory)
    result = _assert_failure(
        fixture_repo,
        "INV-SCHEMA-POST-S5-PRODUCTION-FINGERPRINT",
    )
    assert "INV-SCHEMA-S5-LEGACY-FINGERPRINT" in _codes(result), result.output


def test_m3_review_owner_drift_disables_legacy_substitution(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    record = next(
        item
        for item in inventory["vyperPathClassifications"]
        if item["path"] == M3_CREDIT_RELATIVE
    )
    record["semanticReview"]["owner"] = "protocol/security"
    assert not checker._is_reviewed_m3_production_record(record)
    assert (
        checker._s5_legacy_inventory_fingerprint(inventory)
        != checker.S5_LEGACY_INVENTORY_SHA256
    )
    assert (
        checker._post_s5_production_inventory_fingerprint(inventory)
        != checker.CURRENT_PRODUCTION_INVENTORY_SHA256
    )
    _write_inventory(fixture_repo, inventory)
    _assert_failure(
        fixture_repo,
        "INV-SCHEMA-OWNER",
        path=M3_CREDIT_RELATIVE,
    )


def test_m3_baseline_hash_reversion_fails_current_fingerprint(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    record = next(
        item
        for item in inventory["vyperPathClassifications"]
        if item["path"] == M3_CREDIT_RELATIVE
    )
    record["contentSha256"] = checker.M3_CREDIT_ENGINE_BASELINE_SHA256
    _write_inventory(fixture_repo, inventory)
    assert (
        checker._s5_legacy_inventory_fingerprint(inventory)
        == checker.S5_LEGACY_INVENTORY_SHA256
    )
    _assert_failure(
        fixture_repo,
        "INV-SCHEMA-POST-S5-PRODUCTION-FINGERPRINT",
    )


def test_m3_record_removal_fails_both_fingerprints(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    records = inventory["vyperPathClassifications"]
    records[:] = [
        item for item in records if item["path"] != M3_CREDIT_RELATIVE
    ]
    _write_inventory(fixture_repo, inventory)
    result = _assert_failure(
        fixture_repo,
        "INV-SCHEMA-S5-LEGACY-FINGERPRINT",
    )
    assert (
        "INV-SCHEMA-POST-S5-PRODUCTION-FINGERPRINT" in _codes(result)
    ), result.output


def test_m3_source_content_drift_fails_exact_pin(fixture_repo: Path) -> None:
    _append(fixture_repo / M3_CREDIT_RELATIVE, "\n# drift fixture\n")
    _assert_failure(
        fixture_repo,
        "INV-PATH-M3-CONTENT",
        path=M3_CREDIT_RELATIVE,
    )


def test_m3_source_deletion_fails(fixture_repo: Path) -> None:
    (fixture_repo / M3_CREDIT_RELATIVE).unlink()
    _assert_failure(
        fixture_repo,
        "INV-PATH-MISSING",
        path=M3_CREDIT_RELATIVE,
    )


def test_m3_sibling_production_path_fails(fixture_repo: Path) -> None:
    relative = "contracts/core/FutureCreditEngine.vy"
    path = fixture_repo / relative
    path.write_text("@external\ndef noop():\n    pass\n", encoding="utf-8")
    result = checker.check_repository(fixture_repo)
    assert "INV-PATH-NEW" in _codes(result), result.output
    finding = next(item for item in result.findings if item.code == "INV-PATH-NEW")
    assert finding.path == relative
    assert finding.actual == "production"


def test_m3_future_admission_requires_new_controlling_fingerprint(
    fixture_repo: Path,
) -> None:
    relative = "contracts/core/FutureCreditEngine.vy"
    path = fixture_repo / relative
    path.write_text("@external\ndef noop():\n    pass\n", encoding="utf-8")
    inventory = _load_inventory(fixture_repo)
    inventory["vyperPathClassifications"].append(
        {
            "path": relative,
            "classification": "production",
            "contentSha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "semanticReview": {
                "owner": "engineering/tooling",
                "status": "reviewed",
                "commit": checker.HARDENING_REVIEW_COMMIT,
            },
        }
    )
    assert (
        checker._post_s5_production_inventory_fingerprint(inventory)
        != checker.CURRENT_PRODUCTION_INVENTORY_SHA256
    )
    _write_inventory(fixture_repo, inventory)
    _assert_failure(
        fixture_repo,
        "INV-SCHEMA-POST-S5-PRODUCTION-FINGERPRINT",
    )


@pytest.mark.parametrize(
    "replacement",
    [
        pytest.param(None, id="missing"),
        pytest.param("0x1234", id="malformed"),
        pytest.param(
            checker.S5_REVIEW_ARTIFACT_SHA256.upper(),
            id="uppercase",
        ),
        pytest.param("0" * 64, id="mismatched"),
        pytest.param(checker.HARDENING_REVIEW_COMMIT, id="legacy-commit"),
        pytest.param("__LIVE_STAGE_C_RECORD__", id="live-record"),
    ],
)
def test_s5_review_artifact_value_fails_closed(
    fixture_repo: Path,
    replacement: str | None,
) -> None:
    inventory = _load_inventory(fixture_repo)
    record = next(
        item
        for item in inventory["directOccurrences"]
        if checker._record_key(item) in checker.S5_REVIEW_DIRECT_KEYS
    )
    if replacement is None:
        record.pop(checker.S5_REVIEW_ARTIFACT_FIELD)
    else:
        if replacement == "__LIVE_STAGE_C_RECORD__":
            replacement = hashlib.sha256(
                (
                    REPOSITORY_ROOT / IMPLEMENTATION_RECORD_RELATIVE
                ).read_bytes()
            ).hexdigest()
            assert replacement != checker.S5_REVIEW_ARTIFACT_SHA256
        record[checker.S5_REVIEW_ARTIFACT_FIELD] = replacement
    _write_inventory(fixture_repo, inventory)
    _assert_failure(fixture_repo, "INV-SCHEMA-S5-PROVENANCE")


def test_legacy_record_rejects_s5_review_artifact(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    record = next(
        item
        for item in inventory["directOccurrences"]
        if checker._record_key(item) not in checker.S5_RECONCILED_DIRECT_KEYS
    )
    record[checker.S5_REVIEW_ARTIFACT_FIELD] = (
        checker.S5_REVIEW_ARTIFACT_SHA256
    )
    _write_inventory(fixture_repo, inventory)
    _assert_failure(
        fixture_repo,
        "INV-SCHEMA-S5-PROVENANCE-SCOPE",
        path=record["path"],
    )


def test_legacy_inventory_record_mutation_fails_fingerprint(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    record = next(
        item
        for item in inventory["directOccurrences"]
        if checker._record_key(item) not in checker.S5_RECONCILED_DIRECT_KEYS
    )
    record["category"] = "mutated outside S5 scope"
    _write_inventory(fixture_repo, inventory)
    _assert_failure(
        fixture_repo,
        "INV-SCHEMA-S5-LEGACY-FINGERPRINT",
    )


def test_unmapped_direct_addition_fails_with_actionable_context(
    fixture_repo: Path,
) -> None:
    relative = "contracts/tokens/modules/Erc20Token.vy"
    _append(
        fixture_repo / relative,
        "\n# mutation fixture\nmutatedNumber: uint256 = block.number\n",
    )
    result = _assert_failure(fixture_repo, "INV-DIRECT-NEW", path=relative)
    finding = next(item for item in result.findings if item.code == "INV-DIRECT-NEW")
    assert finding.function != "-"
    assert finding.line > 0
    assert "block.number" in finding.snippet
    assert "semantic review" in finding.remediation


def test_missing_direct_occurrence_fails(fixture_repo: Path) -> None:
    relative = "contracts/tokens/modules/Erc20Token.vy"
    _replace_once(fixture_repo / relative, "block.number", "42")
    result = _assert_failure(
        fixture_repo, "INV-DIRECT-MISSING", path=relative
    )
    assert "INV-DIRECT-COUNT" in _codes(result), result.output


def test_two_exact_occurrences_on_one_line_are_counted_separately(
    fixture_repo: Path,
) -> None:
    relative = "contracts/tokens/modules/Erc20Token.vy"
    _replace_once(
        fixture_repo / relative,
        "block.number + self.hqChangeTimeLock",
        "block.number + block.number + self.hqChangeTimeLock",
    )
    result = _assert_failure(fixture_repo, "INV-DIRECT-NEW", path=relative)
    assert any(
        finding.actual.endswith("block.number")
        for finding in result.findings
        if finding.code == "INV-DIRECT-NEW"
    )


def test_moved_occurrence_within_function_requires_review(
    fixture_repo: Path,
) -> None:
    relative = "contracts/config/BondBooster.vy"
    path = fixture_repo / relative
    lines = path.read_text(encoding="utf-8").splitlines()
    index = next(
        number
        for number, line in enumerate(lines)
        if "config.expireBlock <= block.number" in line
    )
    lines[index], lines[index + 1] = lines[index + 1], lines[index]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _assert_failure(fixture_repo, "INV-DIRECT-MOVE", path=relative)


def test_function_rename_makes_old_identity_missing_and_new_identity_unmapped(
    fixture_repo: Path,
) -> None:
    relative = "contracts/config/BondBooster.vy"
    _replace_once(
        fixture_repo / relative,
        "def getBoostRatio(",
        "def renamedGetBoostRatio(",
    )
    result = checker.check_repository(fixture_repo)
    assert {"INV-DIRECT-MISSING", "INV-DIRECT-NEW"} <= _codes(result), result.output


def test_normalized_expression_change_is_not_silently_rewritten(
    fixture_repo: Path,
) -> None:
    relative = "contracts/config/BondBooster.vy"
    _replace_once(fixture_repo / relative, "block.number", "block . number")
    result = checker.check_repository(fixture_repo)
    assert "INV-PARSER-FIXED-DISAGREE" in _codes(result), result.output
    assert {"INV-DIRECT-MISSING", "INV-DIRECT-NEW"} <= _codes(result), result.output


def test_duplicate_schema_mapping_fails(fixture_repo: Path) -> None:
    inventory = _load_inventory(fixture_repo)
    inventory["directOccurrences"].append(
        dict(inventory["directOccurrences"][0])
    )
    _write_inventory(fixture_repo, inventory)
    _assert_failure(fixture_repo, "INV-SCHEMA-DUPLICATE")


def test_duplicate_timestamp_context_fails(fixture_repo: Path) -> None:
    inventory = _load_inventory(fixture_repo)
    inventory["timestampContext"].append(
        dict(inventory["timestampContext"][0])
    )
    _write_inventory(fixture_repo, inventory)
    _assert_failure(fixture_repo, "INV-SCHEMA-DUPLICATE")


def test_duplicate_mixed_clock_allowance_fails(fixture_repo: Path) -> None:
    inventory = _load_inventory(fixture_repo)
    inventory["allowedMixedClockFunctions"].append(
        dict(inventory["allowedMixedClockFunctions"][0])
    )
    _write_inventory(fixture_repo, inventory)
    _assert_failure(fixture_repo, "INV-SCHEMA-DUPLICATE")


def test_expected_production_count_tampering_fails(fixture_repo: Path) -> None:
    inventory = _load_inventory(fixture_repo)
    inventory["expectedProductionCounts"]["occurrences"] -= 1
    _write_inventory(fixture_repo, inventory)
    _assert_failure(fixture_repo, "INV-SCHEMA-BASELINE")


def test_path_discovery_configuration_tampering_fails(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    inventory["cadenceRoots"].remove("config")
    _write_inventory(fixture_repo, inventory)
    _assert_failure(fixture_repo, "INV-SCHEMA-PATH-CONFIG")


def test_stable_id_renumbering_fails(fixture_repo: Path) -> None:
    inventory = _load_inventory(fixture_repo)
    inventory["directOccurrences"][0]["id"] = "BN-999"
    _write_inventory(fixture_repo, inventory)
    _assert_failure(fixture_repo, "INV-SCHEMA-ID-SET")


def test_new_indirect_cadence_identifier_fails(fixture_repo: Path) -> None:
    relative = "config/BluePrint.py"
    _append(fixture_repo / relative, "\nFRESH_INTERVAL_BLOCKS = 123\n")
    result = _assert_failure(fixture_repo, "INV-CADENCE-NEW", path=relative)
    assert "block-unit-identifier" in result.output


def test_lootbox_floor_identifier_discovery_is_exact() -> None:
    patterns = dict(checker.CADENCE_PATTERNS)
    pattern = patterns["reviewed-cadence-identifier"]

    assert pattern.fullmatch("MIN_UNDERSCORE_SEND_INTERVAL")
    assert pattern.search("OTHER_MIN_UNDERSCORE_SEND_INTERVAL") is None
    assert pattern.search("MIN_UNDERSCORE_SEND_INTERVAL_EXTRA") is None


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    (
        ("delete", "INV-CADENCE-MISSING"),
        ("rename", "INV-CADENCE-MISSING"),
        ("move", "INV-CADENCE-MOVE"),
    ),
)
def test_lootbox_floor_inventory_mutations_fail(
    fixture_repo: Path, mutation: str, expected_code: str
) -> None:
    relative = "contracts/core/Lootbox.vy"
    path = fixture_repo / relative
    declaration = "MIN_UNDERSCORE_SEND_INTERVAL: immutable(uint256)"

    if mutation == "delete":
        _replace_once(
            path,
            declaration,
            "# mutation fixture: immutable floor declaration deleted",
        )
    elif mutation == "rename":
        text = path.read_text(encoding="utf-8")
        assert text.count("MIN_UNDERSCORE_SEND_INTERVAL") >= 1
        path.write_text(
            text.replace(
                "MIN_UNDERSCORE_SEND_INTERVAL",
                "RENAMED_MIN_UNDERSCORE_SEND_INTERVAL",
            ),
            encoding="utf-8",
        )
    else:
        lines = path.read_text(encoding="utf-8").splitlines()
        index = lines.index(declaration)
        assert lines[index + 1] == ""
        lines[index], lines[index + 1] = lines[index + 1], lines[index]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    result = _assert_failure(fixture_repo, expected_code, path=relative)
    assert "MIN_UNDERSCORE_SEND_INTERVAL" in result.output


def test_blueprint_chain_default_value_change_fails(
    fixture_repo: Path,
) -> None:
    relative = "config/BluePrint.py"
    _replace_once(
        fixture_repo / relative,
        '"RIPE_HQ_MIN_GOV_TIMELOCK": 43_200',
        '"RIPE_HQ_MIN_GOV_TIMELOCK": 21_600',
    )
    result = checker.check_repository(fixture_repo)
    assert {"INV-CADENCE-MISSING", "INV-CADENCE-NEW"} <= _codes(
        result
    ), result.output


@pytest.mark.parametrize("key", ("duration", "delay", "blocks"))
def test_bare_block_default_keys_fail(
    fixture_repo: Path, key: str
) -> None:
    relative = "config/BluePrint.py"
    _append(fixture_repo / relative, f'\nMUTATED_DEFAULTS = {{"{key}": 10}}\n')
    _assert_failure(fixture_repo, "INV-CADENCE-NEW", path=relative)


@pytest.mark.parametrize(
    "declaration",
    (
        "warmupBlocks: constant(uint256) = 10",
        "SECONDS_PER_BLOCK: constant(uint256) = 2",
    ),
)
def test_camel_case_and_singular_block_identifiers_fail(
    fixture_repo: Path, declaration: str
) -> None:
    relative = "contracts/config/DefaultsBase.vy"
    _append(fixture_repo / relative, f"\n{declaration}\n")
    _assert_failure(fixture_repo, "INV-CADENCE-NEW", path=relative)


def test_removed_or_changed_cad_001_site_fails(fixture_repo: Path) -> None:
    relative = "contracts/config/DefaultsBase.vy"
    _replace_once(
        fixture_repo / relative,
        "increasePerDangerBlock",
        "increasePerDangerStep",
    )
    result = _assert_failure(fixture_repo, "INV-CADENCE-MISSING", path=relative)
    assert any(
        finding.candidate == "CAD-001"
        for finding in result.findings
        if finding.code == "INV-CADENCE-MISSING"
    )


def test_cad_001_site_set_divergence_reports_fingerprints(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    replacement = next(
        record
        for record in inventory["cadenceCandidates"]
        if "CAD-001" not in record["semanticIds"]
    )
    inventory["indirectCadence"][0]["sites"][0] = {
        key: replacement[key]
        for key in (
            "path",
            "function",
            "pattern",
            "matchedText",
            "normalizedSnippet",
            "ordinalInFunction",
            "reviewedLine",
            "classification",
            "semanticIds",
            "reviewDomain",
        )
    }
    _write_inventory(fixture_repo, inventory)
    result = _assert_failure(fixture_repo, "INV-SCHEMA-CAD-SITES")
    finding = next(
        item
        for item in result.findings
        if item.code == "INV-SCHEMA-CAD-SITES"
    )
    assert finding.expected.startswith("count=32,sha256=")
    assert finding.actual.startswith("count=32,sha256=")
    assert finding.expected != finding.actual


def test_duplicate_cad_001_site_row_fails(fixture_repo: Path) -> None:
    inventory = _load_inventory(fixture_repo)
    sites = inventory["indirectCadence"][0]["sites"]
    sites.append(dict(sites[0]))
    _write_inventory(fixture_repo, inventory)
    result = _assert_failure(fixture_repo, "INV-SCHEMA-DUPLICATE")
    finding = next(
        item
        for item in result.findings
        if item.code == "INV-SCHEMA-DUPLICATE"
        and item.domain == "indirect"
        and item.candidate == "CAD-001"
    )
    assert finding.expected == "1"
    assert finding.actual == "2"
    assert "redundant" in finding.remediation


def test_new_timestamp_context_fails(fixture_repo: Path) -> None:
    relative = "contracts/tokens/modules/Erc20Token.vy"
    _append(
        fixture_repo / relative,
        "\n# mutation fixture\nmutatedTimestamp: uint256 = block.timestamp\n",
    )
    _assert_failure(fixture_repo, "INV-TIMESTAMP-NEW", path=relative)


def test_mixed_number_timestamp_arithmetic_fails(fixture_repo: Path) -> None:
    relative = "contracts/tokens/modules/Erc20Token.vy"
    _append(
        fixture_repo / relative,
        (
            "\n# mutation fixture\n"
            "mixedClock: uint256 = block.number + block.timestamp\n"
        ),
    )
    result = _assert_failure(fixture_repo, "INV-MIXED-CLOCK-NEW", path=relative)
    assert {"INV-DIRECT-NEW", "INV-TIMESTAMP-NEW"} <= _codes(result), result.output


def test_bare_mixed_clock_allowance_cannot_suppress_review(
    fixture_repo: Path,
) -> None:
    relative = "contracts/tokens/modules/Erc20Token.vy"
    _append(
        fixture_repo / relative,
        "\nSNEAKY_MIXED: constant(uint256) = block.number + block.timestamp\n",
    )
    inventory = _load_inventory(fixture_repo)
    inventory["allowedMixedClockFunctions"].append(
        {"path": relative, "function": "<module>"}
    )
    _write_inventory(fixture_repo, inventory)
    _assert_failure(fixture_repo, "INV-SCHEMA-REVIEW", path=relative)


def test_new_production_vyper_path_fails_classification_and_direct_review(
    fixture_repo: Path,
) -> None:
    relative = "contracts/new/ClockConsumer.vy"
    path = fixture_repo / relative
    path.parent.mkdir(parents=True)
    path.write_text(
        "@external\n@view\ndef readClock() -> uint256:\n"
        "    return block.number\n",
        encoding="utf-8",
    )
    result = checker.check_repository(fixture_repo)
    assert {"INV-PATH-NEW", "INV-DIRECT-NEW"} <= _codes(result), result.output


@pytest.mark.parametrize(
    ("source", "destination"),
    (
        (
            "contracts/config/BondBooster.vy",
            "contracts/testing/BondBooster.vy",
        ),
        (
            "contracts/testing/StockTokenTransferProbe.vy",
            "contracts/StockTokenTransferProbe.vy",
        ),
    ),
)
def test_moving_file_into_or_out_of_testing_requires_classification_review(
    fixture_repo: Path, source: str, destination: str
) -> None:
    destination_path = fixture_repo / destination
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(fixture_repo / source, destination_path)
    result = _assert_failure(fixture_repo, "INV-PATH-MOVED", path=destination)
    assert f"{source}->{destination}" in result.output


def test_cadence_use_in_testing_contract_is_reported_separately(
    fixture_repo: Path,
) -> None:
    relative = "contracts/testing/StockTokenTransferProbe.vy"
    _append(fixture_repo / relative, "\nTEST_INTERVAL_BLOCKS: constant(uint256) = 1\n")
    result = _assert_failure(fixture_repo, "INV-CADENCE-NEW", path=relative)
    finding = next(
        item
        for item in result.findings
        if item.code == "INV-CADENCE-NEW" and item.path == relative
    )
    assert finding.actual.startswith("testing:")
    assert "probe/mock review" in finding.remediation


def test_cadence_use_in_mock_contract_is_reported_separately(
    fixture_repo: Path,
) -> None:
    relative = "contracts/mock/MockErc20.vy"
    _append(fixture_repo / relative, "\nMOCK_INTERVAL_BLOCKS: constant(uint256) = 1\n")
    result = _assert_failure(fixture_repo, "INV-CADENCE-NEW", path=relative)
    finding = next(
        item
        for item in result.findings
        if item.code == "INV-CADENCE-NEW" and item.path == relative
    )
    assert finding.actual.startswith("mock:")
    assert "probe/mock review" in finding.remediation


@pytest.mark.parametrize(
    "statement",
    (
        "import contracts.testing.StockTokenTransferProbe",
        "import contracts.mock.MockErc20",
        "from contracts.testing.StockTokenTransferProbe import Probe",
        "from contracts.mock.MockErc20 import MockErc20",
    ),
)
def test_production_import_from_testing_or_mock_fails(
    fixture_repo: Path, statement: str
) -> None:
    relative = "contracts/tokens/modules/Erc20Token.vy"
    path = fixture_repo / relative
    path.write_text(
        f"{statement}\n" + path.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    _assert_failure(
        fixture_repo, "INV-IMPORT-PROD-NONPROD", path=relative
    )


def test_placeholder_semantic_review_fails(fixture_repo: Path) -> None:
    inventory = _load_inventory(fixture_repo)
    inventory["directOccurrences"][0]["semanticReview"]["owner"] = "TODO"
    _write_inventory(fixture_repo, inventory)
    _assert_failure(fixture_repo, "INV-SCHEMA-PLACEHOLDER")


def test_missing_seconds_unit_review_fails(fixture_repo: Path) -> None:
    inventory = _load_inventory(fixture_repo)
    relative = inventory["secondsUnitCandidates"][0]["path"]
    inventory["secondsUnitCandidates"][0].pop("semanticReview")
    _write_inventory(fixture_repo, inventory)
    _assert_failure(fixture_repo, "INV-SCHEMA-REVIEW", path=relative)


def test_invalid_review_status_fails(fixture_repo: Path) -> None:
    inventory = _load_inventory(fixture_repo)
    inventory["secondsUnitCandidates"][0]["semanticReview"]["status"] = "skipped"
    _write_inventory(fixture_repo, inventory)
    _assert_failure(fixture_repo, "INV-SCHEMA-STATUS")


def test_review_provenance_cannot_be_reassigned(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    record = inventory["secondsUnitCandidates"][0]
    record["semanticReview"]["commit"] = checker.TRACK3_REVIEW_COMMIT
    _write_inventory(fixture_repo, inventory)
    _assert_failure(
        fixture_repo, "INV-SCHEMA-PROVENANCE", path=record["path"]
    )


def test_seconds_unit_suppression_requires_review(
    fixture_repo: Path,
) -> None:
    relative = "contracts/config/DefaultsBase.vy"
    path = fixture_repo / relative
    declaration = "SNEAKY_IN_SECONDS: constant(uint256) = 60"
    _append(path, f"\n{declaration}\n")
    reviewed_line = len(path.read_text(encoding="utf-8").splitlines())
    inventory = _load_inventory(fixture_repo)
    inventory["secondsUnitCandidates"].append(
        {
            "path": relative,
            "function": "<module>",
            "pattern": "seconds-unit-identifier",
            "matchedText": "SNEAKY_IN_SECONDS",
            "normalizedSnippet": declaration,
            "ordinalInFunction": 1,
            "reviewedLine": reviewed_line,
            "classification": "production",
            "semanticIds": [],
            "reviewDomain": "cadence-surface",
        }
    )
    _write_inventory(fixture_repo, inventory)
    _assert_failure(fixture_repo, "INV-SCHEMA-REVIEW", path=relative)


def test_new_seconds_unit_identifier_fails(fixture_repo: Path) -> None:
    relative = "contracts/config/DefaultsBase.vy"
    _append(
        fixture_repo / relative,
        "\nFRESH_IN_SECONDS: constant(uint256) = 60\n",
    )
    _assert_failure(fixture_repo, "INV-SECONDS-UNIT-NEW", path=relative)


def test_unreviewed_ignore_fails(fixture_repo: Path) -> None:
    inventory = _load_inventory(fixture_repo)
    inventory["directOccurrences"][0]["semanticReview"]["status"] = "ignore"
    inventory["directOccurrences"][0]["semanticReview"].pop(
        "justification", None
    )
    _write_inventory(fixture_repo, inventory)
    _assert_failure(fixture_repo, "INV-SCHEMA-IGNORE")


def test_parser_fixed_string_disagreement_cannot_be_suppressed(
    fixture_repo: Path,
) -> None:
    relative = "contracts/config/BondBooster.vy"
    _append(
        fixture_repo / relative,
        "\n# mutation fixture\nparserOnly: uint256 = block . number\n",
    )
    _assert_failure(
        fixture_repo, "INV-PARSER-FIXED-DISAGREE", path=relative
    )


def test_unclassified_vyper_path_fails(fixture_repo: Path) -> None:
    relative = "rogue/Unclassified.vy"
    path = fixture_repo / relative
    path.parent.mkdir(parents=True)
    path.write_text("@external\ndef noop():\n    pass\n", encoding="utf-8")
    result = checker.check_repository(fixture_repo)
    assert {"INV-PATH-NEW", "INV-PATH-UNCLASSIFIED"} <= _codes(result), result.output


def test_path_classification_record_tampering_fails(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    record = next(
        item
        for item in inventory["vyperPathClassifications"]
        if item["classification"] == "production"
    )
    relative = record["path"]
    record["classification"] = "test"
    _write_inventory(fixture_repo, inventory)
    _assert_failure(fixture_repo, "INV-PATH-CLASSIFICATION", path=relative)


EXCLUDED_EXAMPLE_RELATIVE = (
    "docs/chains/rh/examples/ExampleGreenCcipBurnMintPool.vy"
)


def test_ccip_reference_example_is_excluded_and_content_pinned(
    fixture_repo: Path,
) -> None:
    relative = EXCLUDED_EXAMPLE_RELATIVE
    frozen = checker.EXCLUDED_EXAMPLE_CONTENT_HASHES[relative]
    assert checker.EXCLUDED_EXAMPLE_CONTENT_HASHES == {relative: frozen}
    assert (
        checker.classify_path(
            relative,
            checker.EXPECTED_PRODUCTION_ROOTS,
            checker.EXPECTED_EXCLUDED_PRODUCTION_GLOBS,
        )
        == "excluded"
    )
    inventory = _load_inventory(fixture_repo)
    record = next(
        item
        for item in inventory["vyperPathClassifications"]
        if item["path"] == relative
    )
    assert record["classification"] == "excluded"
    assert record["contentSha256"] == frozen
    source = fixture_repo / relative
    assert hashlib.sha256(source.read_bytes()).hexdigest() == frozen
    assert checker.TIMESTAMP_PATTERN.search(source.read_text(encoding="utf-8"))
    result = checker.check_repository(fixture_repo)
    assert result.ok, result.output
    assert "production_occurrences=102" in result.output
    assert "production_files=18" in result.output


def test_excluded_example_content_drift_fails_closed(
    fixture_repo: Path,
) -> None:
    relative = EXCLUDED_EXAMPLE_RELATIVE
    _append(fixture_repo / relative, "\n# drift fixture\n")
    _assert_failure(fixture_repo, "INV-PATH-EXCLUDED-CONTENT", path=relative)


def test_excluded_example_drift_cannot_be_relabeled_in_inventory(
    fixture_repo: Path,
) -> None:
    relative = EXCLUDED_EXAMPLE_RELATIVE
    path = fixture_repo / relative
    _append(path, "\n# drift fixture\n")
    drifted = hashlib.sha256(path.read_bytes()).hexdigest()
    assert drifted != checker.EXCLUDED_EXAMPLE_CONTENT_HASHES[relative]
    inventory = _load_inventory(fixture_repo)
    record = next(
        item
        for item in inventory["vyperPathClassifications"]
        if item["path"] == relative
    )
    record["contentSha256"] = drifted
    _write_inventory(fixture_repo, inventory)
    _assert_failure(fixture_repo, "INV-SCHEMA-PATH-RECORD", path=relative)


def test_excluded_example_removal_fails_closed(fixture_repo: Path) -> None:
    relative = EXCLUDED_EXAMPLE_RELATIVE
    (fixture_repo / relative).unlink()
    _assert_failure(fixture_repo, "INV-PATH-MISSING", path=relative)


def test_new_docs_example_vyper_path_still_fails_closed(
    fixture_repo: Path,
) -> None:
    relative = "docs/chains/rh/examples/AnotherCcipExample.vy"
    (fixture_repo / relative).write_text(
        "@external\ndef noop():\n    pass\n", encoding="utf-8"
    )
    result = checker.check_repository(fixture_repo)
    assert {"INV-PATH-NEW", "INV-PATH-UNCLASSIFIED"} <= _codes(result), result.output


def test_excluded_classification_cannot_be_claimed_by_other_paths(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    record = next(
        item
        for item in inventory["vyperPathClassifications"]
        if item["classification"] == "production"
    )
    record["classification"] = "excluded"
    _write_inventory(fixture_repo, inventory)
    _assert_failure(fixture_repo, "INV-SCHEMA-PATH-RECORD", path=record["path"])


def test_future_excluded_map_entry_stays_inside_legacy_fingerprint(
    fixture_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    relative = "docs/chains/rh/examples/FutureCcipExample.vy"
    path = fixture_repo / relative
    path.write_text("@external\ndef noop():\n    pass\n", encoding="utf-8")
    content_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    monkeypatch.setitem(
        checker.EXCLUDED_EXAMPLE_CONTENT_HASHES, relative, content_hash
    )
    inventory = _load_inventory(fixture_repo)
    inventory["vyperPathClassifications"].append(
        {
            "path": relative,
            "classification": "excluded",
            "contentSha256": content_hash,
            "semanticReview": {
                "owner": "engineering/tooling",
                "status": "reviewed",
                "commit": checker.HARDENING_REVIEW_COMMIT,
            },
        }
    )
    _write_inventory(fixture_repo, inventory)
    assert (
        checker._s5_legacy_inventory_fingerprint(inventory)
        != checker.S5_LEGACY_INVENTORY_SHA256
    )
    _assert_failure(fixture_repo, "INV-SCHEMA-S5-LEGACY-FINGERPRINT")


def test_new_vyi_interface_cadence_field_is_discovered(
    fixture_repo: Path,
) -> None:
    relative = "interfaces/NewClockConfig.vyi"
    path = fixture_repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "struct NewClockConfig:\n    warmupBlocks: uint256\n",
        encoding="utf-8",
    )
    result = checker.check_repository(fixture_repo)
    assert {"INV-PATH-NEW", "INV-CADENCE-NEW"} <= _codes(result), result.output
    cadence = next(
        item
        for item in result.findings
        if item.code == "INV-CADENCE-NEW" and item.path == relative
    )
    assert cadence.actual.startswith("interface:")


def test_existing_vyi_cadence_field_change_fails(
    fixture_repo: Path,
) -> None:
    relative = "interfaces/ConfigStructs.vyi"
    _replace_once(
        fixture_repo / relative,
        "numBlocksPerInterval",
        "numIntervals",
    )
    _assert_failure(fixture_repo, "INV-CADENCE-MISSING", path=relative)


def test_seconds_constant_renamed_to_ambiguous_blocks_fails_both_domains(
    fixture_repo: Path,
) -> None:
    relative = "contracts/config/DefaultsBase.vy"
    path = fixture_repo / relative
    text = path.read_text(encoding="utf-8")
    name = next(
        token
        for token in (
            "DAY_IN_SECONDS",
            "WEEK_IN_SECONDS",
            "MONTH_IN_SECONDS",
            "YEAR_IN_SECONDS",
        )
        if token in text
    )
    path.write_text(text.replace(name, "AMBIGUOUS_BLOCKS", 1), encoding="utf-8")
    result = checker.check_repository(fixture_repo)
    assert "INV-SECONDS-UNIT-MISSING" in _codes(result), result.output
    assert "INV-CADENCE-NEW" in _codes(result), result.output


def test_future_migration_history_namespace_is_scanned(
    fixture_repo: Path,
) -> None:
    relative = "migration_history/robinhood/v1/manifest.json"
    path = fixture_repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"warmupBlocks": 10}\n', encoding="utf-8")
    _assert_failure(fixture_repo, "INV-CADENCE-NEW", path=relative)


def test_readme_cadence_prose_is_scanned(fixture_repo: Path) -> None:
    relative = "README.md"
    (fixture_repo / relative).write_text(
        "Robinhood warmupBlocks must be reviewed.\n", encoding="utf-8"
    )
    _assert_failure(fixture_repo, "INV-CADENCE-NEW", path=relative)


def test_schema_documents_naming_and_historical_boundaries(
    fixture_repo: Path,
) -> None:
    inventory = _load_inventory(fixture_repo)
    documentation = inventory["schemaDocumentation"]
    assert "lower-camel plural Blocks" in documentation["cadenceCoverage"]
    assert "migration_history/base-mainnet/**" in documentation[
        "historicalExclusions"
    ]
    assert "future" in documentation["historicalExclusions"]
    assert "<module>" in documentation["functionAttribution"]
    assert (
        inventory["reviewAuthorities"]["vyperPathClassifications"]
        == "engineering/tooling"
    )
    assert (
        inventory["reviewProvenance"]["hardeningApprovalCommit"]
        == checker.HARDENING_REVIEW_COMMIT
    )
    assert (
        inventory["reviewProvenance"]["pr61ReviewCommit"]
        == checker.PR61_REVIEW_COMMIT
    )
    assert not any(
        record.get("semanticId") == "REVIEWED-CADENCE-SURFACE"
        for record in inventory["cadenceCandidates"]
    )


def test_function_attribution_ignores_interface_declarations_and_resets_module(
) -> None:
    lines = [
        "interface External:",
        "    def fake(value: uint256) -> uint256: view",
        "MODULE_CLOCK: uint256 = block.number",
        "@external",
        "def real(",
        "    value: uint256,",
        ") -> uint256:",
        "    return block.number",
        "TRAILING_CLOCK: uint256 = block.number",
    ]
    assert checker._line_functions(lines) == [
        "<module>",
        "<module>",
        "<module>",
        "<module>",
        "real",
        "real",
        "real",
        "real",
        "<module>",
    ]


def test_malformed_json_fails_deterministically(fixture_repo: Path) -> None:
    (fixture_repo / INVENTORY_RELATIVE).write_text("{", encoding="utf-8")
    first = checker.check_repository(fixture_repo)
    second = checker.check_repository(fixture_repo)
    assert _codes(first) == {"INV-SCHEMA-JSON"}
    assert first.output == second.output


def test_unsupported_schema_version_fails(fixture_repo: Path) -> None:
    inventory = _load_inventory(fixture_repo)
    inventory["schemaVersion"] = 2
    _write_inventory(fixture_repo, inventory)
    _assert_failure(fixture_repo, "INV-SCHEMA-VERSION")


def test_discovery_order_does_not_change_output(
    fixture_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    baseline = checker.check_repository(fixture_repo)
    assert baseline.ok, baseline.output
    original = checker._iter_files

    def reversed_iter(root: Path, relative_roots):
        return list(reversed(original(root, relative_roots)))

    monkeypatch.setattr(checker, "_iter_files", reversed_iter)
    reordered = checker.check_repository(fixture_repo)
    assert reordered.ok, reordered.output
    assert reordered.output == baseline.output


def test_command_runs_outside_repository_root_and_is_deterministic(
    fixture_repo: Path, tmp_path: Path
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    command = [
        sys.executable,
        str(fixture_repo / SCRIPT_RELATIVE),
        "--check",
    ]
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    first = subprocess.run(
        command,
        cwd=outside,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    second = subprocess.run(
        command,
        cwd=outside,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout
    assert first.stderr == second.stderr == ""
    assert "CLOCK_INVENTORY_OK" in first.stdout
