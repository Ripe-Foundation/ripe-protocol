from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import check_block_clock_inventory as checker


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
INVENTORY_RELATIVE = Path("config/block-clock-inventory.json")
SCRIPT_RELATIVE = Path("scripts/check_block_clock_inventory.py")


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
    assert "production_occurrences=100" in result.output
    assert "production_lines=95" in result.output
    assert "production_files=17" in result.output
    assert "bn_ids=32" in result.output
    assert "indirect_ids=1" in result.output
    assert "timestamp_ids=11" in result.output
    assert "seconds_unit_candidates=58" in result.output
    assert "mixed_clock_functions=4" in result.output
    assert "vyper_paths=92" in result.output
    assert "CLOCK_INVENTORY_NONPROD" in result.output
    assert "test=130" in result.output


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
    assert finding.expected.startswith("count=27,sha256=")
    assert finding.actual.startswith("count=27,sha256=")
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
