from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from config.artifact_expectations import (
    ArtifactExpectationsError,
    load_artifact_expectations,
)
from scripts import check_contract_artifacts as artifact_checker
from scripts import update_contract_artifact_expectations as artifact_updater


ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "scripts" / "check_contract_artifacts.py"
EXPECTATIONS = ROOT / "config" / "contract-artifact-expectations.json"
EIP_170_LIMIT = 24_576
REQUIRED_CONTRACTS = frozenset(
    {
        "AuctionHouse",
        "CreditEngine",
        "Deleverage",
        "DefaultsRobinhood",
        "SimpleErc20",
        "Ledger",
        "Lootbox",
        "MissionControl",
        "RipeGov",
        "SwitchboardDelta",
        "SwitchboardBravo",
        "StabilityPool",
        "Teller",
        "UniswapV2Prices",
        "VaultMigrator",
    }
)
NEW_CONTRACT_SOURCES = {
    "AuctionHouse": ROOT / "contracts" / "core" / "AuctionHouse.vy",
    "Deleverage": ROOT / "contracts" / "core" / "Deleverage.vy",
    "DefaultsRobinhood": ROOT / "contracts" / "config" / "DefaultsRobinhood.vy",
    "SwitchboardDelta": ROOT / "contracts" / "config" / "SwitchboardDelta.vy",
    "MissionControl": ROOT / "contracts" / "data" / "MissionControl.vy",
    "RipeGov": ROOT / "contracts" / "vaults" / "RipeGov.vy",
    "StabilityPool": ROOT / "contracts" / "vaults" / "StabilityPool.vy",
    "SwitchboardBravo": ROOT / "contracts" / "config" / "SwitchboardBravo.vy",
    "UniswapV2Prices": ROOT / "contracts" / "priceSources" / "UniswapV2Prices.vy",
    "VaultMigrator": ROOT / "contracts" / "core" / "VaultMigrator.vy",
}

# These are constructor-bound deployed-code measurements. They are deliberately
# distinct from the pre-constructor runtime-template values frozen in the JSON.
DEPLOYED_RUNTIME_FACTS = {
    "AuctionHouse": {"size": 24_556, "headroom": 20},
    "Deleverage": {"size": 24_569, "headroom": 7},
}
CURVE_LAUNCH_ARTIFACTS = {
    ROOT / "contracts" / "priceSources" / "CurvePrices.vy": (
        "f6e8234be8e433ed344f6f61d9cf04d20a4327c773759bb6aced44b9f65ebd0c"
    ),
    ROOT / "scripts" / "abis" / "CurvePrices.json": (
        "3f06fa5c83f4404bfb97da689ea3b4611e94c60a504174001210033c7c429772"
    ),
}


def _run_checker(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), *args],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )


def _write_expectations(tmp_path: Path, values: dict) -> Path:
    tampered = tmp_path / "expectations.json"
    tampered.write_text(json.dumps(values, sort_keys=True) + "\n")
    return tampered


def _load_expectations(path: Path = EXPECTATIONS, *, root: Path = ROOT) -> dict:
    return load_artifact_expectations(path, root=root)


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def _write_v2_expectations(tmp_path: Path):
    repository = tmp_path / "repository"
    records_root = repository / "config" / "contract-artifacts"
    records_root.mkdir(parents=True)
    values = _load_expectations()
    references = {}
    record_paths = {}
    for name, expectation in values["contracts"].items():
        relative = Path("config") / "contract-artifacts" / f"{name}.json"
        record_path = repository / relative
        raw = _json_bytes(
            {
                "contract": name,
                "expectation": expectation,
                "schema_version": 1,
            }
        )
        record_path.write_bytes(raw)
        references[name] = {
            "path": relative.as_posix(),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
        record_paths[name] = record_path

    index = {
        "compiler": values["compiler"],
        "contracts": references,
        "records_root": "config/contract-artifacts",
        "schema_version": 2,
    }
    index_path = repository / "config" / "contract-artifact-expectations.json"
    index_path.write_bytes(_json_bytes(index))
    return repository, index_path, index, record_paths


def _rewrite_v2_index(index_path: Path, index: dict) -> None:
    index_path.write_bytes(_json_bytes(index))


def _snapshot_regular_files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file() and not path.is_symlink()
    }


def test_v1_loader_preserves_the_current_in_memory_shape():
    assert _load_expectations() == json.loads(EXPECTATIONS.read_bytes())


def test_checker_accepts_canonical_relative_v1_expectations_path():
    result = _run_checker(
        "--contract",
        "Lootbox",
        "--expectations",
        "config/contract-artifact-expectations.json",
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[-1] == "CONTRACT_ARTIFACTS_OK"


def test_v2_loader_is_equivalent_to_the_frozen_v1_shape(tmp_path):
    repository, index_path, _, _ = _write_v2_expectations(tmp_path)
    assert _load_expectations(index_path, root=repository) == _load_expectations()


def test_v2_index_must_be_natively_contained_by_root(tmp_path):
    repository, index_path, _, _ = _write_v2_expectations(tmp_path)
    outside_index = tmp_path / "outside-index.json"
    outside_index.write_bytes(index_path.read_bytes())
    with pytest.raises(ArtifactExpectationsError, match="native path escapes"):
        _load_expectations(outside_index, root=repository)


def test_duplicate_json_keys_fail_closed(tmp_path):
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text(
        '{"compiler": {}, "contracts": {}, "schema_version": 1, '
        '"schema_version": 1}\n'
    )
    with pytest.raises(ArtifactExpectationsError, match="duplicate JSON key"):
        _load_expectations(duplicate, root=tmp_path)


def test_symlink_index_fails_closed(tmp_path):
    target = _write_expectations(tmp_path, _load_expectations())
    symlink = tmp_path / "expectations-symlink.json"
    symlink.symlink_to(target)
    result = _run_checker(
        "--contract", "Lootbox", "--expectations", str(symlink)
    )
    assert result.returncode == 1
    assert "symlink anchor components are forbidden" in result.stderr


def test_relative_root_and_index_anchors_fail_closed(tmp_path):
    index_path = _write_expectations(tmp_path, _load_expectations())
    with pytest.raises(ArtifactExpectationsError, match="anchor must be absolute"):
        _load_expectations("expectations.json", root=tmp_path)
    with pytest.raises(ArtifactExpectationsError, match="anchor must be absolute"):
        _load_expectations(index_path, root="repository")


def test_dot_and_dotdot_anchor_spellings_fail_closed(tmp_path):
    repository = tmp_path / "repository"
    repository.mkdir()
    index_path = _write_expectations(repository, _load_expectations())
    unsafe_indexes = (
        f"{repository}/./{index_path.name}",
        f"{repository}/unused/../{index_path.name}",
    )
    for unsafe_index in unsafe_indexes:
        with pytest.raises(ArtifactExpectationsError, match="may not contain . or .."):
            _load_expectations(unsafe_index, root=repository)

    unsafe_roots = (
        f"{tmp_path}/./repository",
        f"{repository}/unused/..",
    )
    for unsafe_root in unsafe_roots:
        with pytest.raises(ArtifactExpectationsError, match="may not contain . or .."):
            _load_expectations(index_path, root=unsafe_root)


def test_root_and_index_parent_symlinks_fail_closed(tmp_path):
    repository = tmp_path / "repository"
    repository.mkdir()
    index_path = _write_expectations(repository, _load_expectations())
    linked_repository = tmp_path / "linked-repository"
    linked_repository.symlink_to(repository, target_is_directory=True)

    with pytest.raises(
        ArtifactExpectationsError, match="symlink anchor components are forbidden"
    ):
        _load_expectations(
            linked_repository / index_path.name, root=repository
        )
    with pytest.raises(
        ArtifactExpectationsError, match="symlink anchor components are forbidden"
    ):
        _load_expectations(index_path, root=linked_repository)


def test_root_and_index_component_casing_must_match_disk(tmp_path):
    repository = tmp_path / "Repository"
    repository.mkdir()
    index_path = repository / "Expectations.json"
    index_path.write_bytes(_json_bytes(_load_expectations()))

    with pytest.raises(ArtifactExpectationsError, match="component casing mismatch"):
        _load_expectations(
            repository / "expectations.json", root=repository
        )
    with pytest.raises(ArtifactExpectationsError, match="component casing mismatch"):
        _load_expectations(index_path, root=tmp_path / "repository")


@pytest.mark.parametrize("schema_version", [3, True, 1.0])
def test_unsupported_index_schema_fails_closed(tmp_path, schema_version):
    values = _load_expectations()
    values["schema_version"] = schema_version
    unsupported = _write_expectations(tmp_path, values)
    with pytest.raises(ArtifactExpectationsError, match="unsupported schema_version"):
        _load_expectations(unsupported, root=tmp_path)


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_v1_non_finite_constants_fail_closed(tmp_path, constant):
    values = _load_expectations()
    values["contracts"]["Lootbox"]["non_finite_counterexample"] = (
        "__NON_FINITE__"
    )
    raw = _json_bytes(values).replace(b'"__NON_FINITE__"', constant.encode())
    index_path = tmp_path / "non-finite-v1.json"
    index_path.write_bytes(raw)
    with pytest.raises(ArtifactExpectationsError, match="non-finite JSON constant"):
        _load_expectations(index_path, root=tmp_path)


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_v2_nested_non_finite_constants_fail_closed(tmp_path, constant):
    repository, index_path, index, record_paths = _write_v2_expectations(tmp_path)
    record_path = record_paths["Lootbox"]
    record = json.loads(record_path.read_bytes())
    record["expectation"]["non_finite_counterexample"] = "__NON_FINITE__"
    raw = _json_bytes(record).replace(b'"__NON_FINITE__"', constant.encode())
    record_path.write_bytes(raw)
    index["contracts"]["Lootbox"]["sha256"] = hashlib.sha256(raw).hexdigest()
    _rewrite_v2_index(index_path, index)
    with pytest.raises(ArtifactExpectationsError, match="non-finite JSON constant"):
        _load_expectations(index_path, root=repository)


@pytest.mark.parametrize("overflow", ["1e9999", "-1e9999"])
def test_v1_float_overflow_fails_closed(tmp_path, overflow):
    values = _load_expectations()
    values["contracts"]["Lootbox"]["float_overflow_counterexample"] = (
        "__FLOAT_OVERFLOW__"
    )
    raw = _json_bytes(values).replace(b'"__FLOAT_OVERFLOW__"', overflow.encode())
    index_path = tmp_path / "float-overflow-v1.json"
    index_path.write_bytes(raw)
    with pytest.raises(ArtifactExpectationsError, match="non-finite JSON float"):
        _load_expectations(index_path, root=tmp_path)


@pytest.mark.parametrize("overflow", ["1e9999", "-1e9999"])
def test_v2_nested_float_overflow_fails_closed(tmp_path, overflow):
    repository, index_path, index, record_paths = _write_v2_expectations(tmp_path)
    record_path = record_paths["Lootbox"]
    record = json.loads(record_path.read_bytes())
    record["expectation"]["float_overflow_counterexample"] = (
        "__FLOAT_OVERFLOW__"
    )
    raw = _json_bytes(record).replace(b'"__FLOAT_OVERFLOW__"', overflow.encode())
    record_path.write_bytes(raw)
    index["contracts"]["Lootbox"]["sha256"] = hashlib.sha256(raw).hexdigest()
    _rewrite_v2_index(index_path, index)
    with pytest.raises(ArtifactExpectationsError, match="non-finite JSON float"):
        _load_expectations(index_path, root=repository)


def test_v2_missing_record_fails_closed(tmp_path):
    repository, index_path, _, record_paths = _write_v2_expectations(tmp_path)
    record_paths["Lootbox"].unlink()
    with pytest.raises(ArtifactExpectationsError, match="record set mismatch"):
        _load_expectations(index_path, root=repository)


def test_v2_extra_record_fails_closed(tmp_path):
    repository, index_path, index, record_paths = _write_v2_expectations(tmp_path)
    record_paths["Lootbox"].with_name("Unindexed.json").write_text("{}\n")
    _rewrite_v2_index(index_path, index)
    with pytest.raises(ArtifactExpectationsError, match="record set mismatch"):
        _load_expectations(index_path, root=repository)


def test_v2_record_hash_mismatch_fails_closed(tmp_path):
    repository, index_path, index, _ = _write_v2_expectations(tmp_path)
    index["contracts"]["Lootbox"]["sha256"] = "0" * 64
    _rewrite_v2_index(index_path, index)
    with pytest.raises(ArtifactExpectationsError, match="SHA-256 mismatch"):
        _load_expectations(index_path, root=repository)


@pytest.mark.parametrize(
    ("unsafe_path", "failure"),
    [
        ("/tmp/Lootbox.json", "absolute paths are forbidden"),
        ("../Lootbox.json", "may not escape its root"),
        ("C:/Lootbox.json", "Windows drive paths are forbidden"),
        ("C:Lootbox.json", "Windows drive paths are forbidden"),
    ],
)
def test_v2_unsafe_record_paths_fail_closed(tmp_path, unsafe_path, failure):
    repository, index_path, index, _ = _write_v2_expectations(tmp_path)
    index["contracts"]["Lootbox"]["path"] = unsafe_path
    _rewrite_v2_index(index_path, index)
    with pytest.raises(ArtifactExpectationsError, match=failure):
        _load_expectations(index_path, root=repository)


def test_contract_names_must_be_identifier_safe(tmp_path):
    values = _load_expectations()
    record = values["contracts"].pop("Lootbox")
    values["contracts"]["Lootbox-unsafe"] = record
    index_path = _write_expectations(tmp_path, values)
    with pytest.raises(ArtifactExpectationsError, match="identifier-safe"):
        _load_expectations(index_path, root=tmp_path)


def test_v2_record_filename_must_match_contract_exactly(tmp_path):
    repository, index_path, index, record_paths = _write_v2_expectations(tmp_path)
    record_path = record_paths["Lootbox"]
    renamed = record_path.with_name("Lootbox-record.json")
    record_path.rename(renamed)
    index["contracts"]["Lootbox"]["path"] = renamed.relative_to(
        repository
    ).as_posix()
    _rewrite_v2_index(index_path, index)
    with pytest.raises(ArtifactExpectationsError, match="expected exact filename"):
        _load_expectations(index_path, root=repository)


def test_v2_relative_component_casing_must_match_disk(tmp_path):
    repository, index_path, _, record_paths = _write_v2_expectations(tmp_path)
    records_root = record_paths["Lootbox"].parent
    records_root.rename(records_root.with_name("Contract-Artifacts"))
    with pytest.raises(ArtifactExpectationsError, match="component casing mismatch"):
        _load_expectations(index_path, root=repository)


def test_v2_non_regular_record_fails_closed(tmp_path):
    repository, index_path, _, record_paths = _write_v2_expectations(tmp_path)
    record_path = record_paths["Lootbox"]
    record_path.unlink()
    record_path.mkdir()
    with pytest.raises(ArtifactExpectationsError, match="not a regular file"):
        _load_expectations(index_path, root=repository)


def test_v2_symlink_record_fails_closed(tmp_path):
    repository, index_path, _, record_paths = _write_v2_expectations(tmp_path)
    record_path = record_paths["Lootbox"]
    target = tmp_path / "outside-record.json"
    target.write_bytes(record_path.read_bytes())
    record_path.unlink()
    record_path.symlink_to(target)
    with pytest.raises(ArtifactExpectationsError, match="symlink paths are forbidden"):
        _load_expectations(index_path, root=repository)


def test_v2_unsupported_record_schema_fails_closed(tmp_path):
    repository, index_path, index, record_paths = _write_v2_expectations(tmp_path)
    record_path = record_paths["Lootbox"]
    record = json.loads(record_path.read_bytes())
    record["schema_version"] = 2
    raw = _json_bytes(record)
    record_path.write_bytes(raw)
    index["contracts"]["Lootbox"]["sha256"] = hashlib.sha256(raw).hexdigest()
    _rewrite_v2_index(index_path, index)
    with pytest.raises(ArtifactExpectationsError, match="unsupported record schema"):
        _load_expectations(index_path, root=repository)


def test_updater_refuses_v2_before_compile_or_write(tmp_path, monkeypatch):
    repository, index_path, _, _ = _write_v2_expectations(tmp_path)
    before = _snapshot_regular_files(repository)

    def unexpected_vyper_lookup():
        pytest.fail("updater reached compiler discovery for read-only v2")

    def unexpected_write(*_args, **_kwargs):
        pytest.fail("updater attempted to write read-only v2")

    monkeypatch.setattr(artifact_updater, "ROOT", repository)
    monkeypatch.setattr(artifact_updater, "EXPECTATIONS", index_path)
    monkeypatch.setattr(
        artifact_updater.checker, "_vyper_path", unexpected_vyper_lookup
    )
    monkeypatch.setattr(Path, "write_text", unexpected_write)
    monkeypatch.setattr(
        sys, "argv", ["update_contract_artifact_expectations.py"]
    )

    with pytest.raises(
        ArtifactExpectationsError, match="updates require an atomic v2 writer"
    ):
        artifact_updater.main()

    assert _snapshot_regular_files(repository) == before


def test_frozen_required_contract_set_is_exact():
    values = _load_expectations()
    assert set(values["contracts"]) == REQUIRED_CONTRACTS


def test_eager_migrated_source_settlement_entrypoints_are_absent():
    removed_functions = {
        "Lootbox": "settleAndCleanupMigratedSource",
        "VaultMigrator": "settleAndCleanupLegacyRipeGovSources",
        "SwitchboardEcho": "settleAndCleanupLegacyRipeGovSources",
    }
    for contract_name, function_name in removed_functions.items():
        abi = json.loads(
            (ROOT / "scripts" / "abis" / f"{contract_name}.json").read_text()
        )
        assert not any(
            entry.get("type") == "function" and entry.get("name") == function_name
            for entry in abi
        )


def test_governance_migration_surface_has_exactly_three_use_cases():
    expected = {
        "migrateLegacyRipeGovPositions": ["address[]"],
        "migrateRipeGovPositions": ["address[]", "uint256"],
        "migrateVaultPositions": ["address[]", "uint256", "uint256"],
    }
    for contract_name in ("VaultMigrator", "SwitchboardEcho"):
        abi = json.loads(
            (ROOT / "scripts" / "abis" / f"{contract_name}.json").read_text()
        )
        migration_functions = {
            entry["name"]: [item["type"] for item in entry["inputs"]]
            for entry in abi
            if entry.get("type") == "function"
            and "migrat" in entry.get("name", "").lower()
        }
        assert migration_functions == expected

    vault_migrator_abi = json.loads(
        (ROOT / "scripts" / "abis" / "VaultMigrator.json").read_text()
    )
    assert not any(
        entry.get("type") == "event"
        and entry.get("name") == "LegacyRipeGovMigrationAssetSet"
        for entry in vault_migrator_abi
    )
    for event_name in (
        "LegacyRipeGovPositionMigrationExecuted",
        "RipeGovPositionMigrationExecuted",
        "VaultPositionMigrationExecuted",
    ):
        event = next(
            entry
            for entry in vault_migrator_abi
            if entry.get("type") == "event" and entry.get("name") == event_name
        )
        assert "caller" not in {item["name"] for item in event["inputs"]}


def test_robinhood_curve_launch_reuses_frozen_source_and_abi():
    assert {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in CURVE_LAUNCH_ARTIFACTS
    } == {
        path.relative_to(ROOT).as_posix(): expected
        for path, expected in CURVE_LAUNCH_ARTIFACTS.items()
    }


def test_frozen_contract_artifacts_are_current():
    result = _run_checker()
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert lines[-1] == "CONTRACT_ARTIFACTS_OK"
    contract_lines = lines[:-1]
    assert len(contract_lines) == len(REQUIRED_CONTRACTS)
    assert {line.split(":", 1)[0] for line in contract_lines} == REQUIRED_CONTRACTS
    assert all(
        "not a deployed-runtime identity; constructor immutables" in line
        for line in contract_lines
    )


@pytest.mark.parametrize("contract", NEW_CONTRACT_SOURCES)
def test_new_contract_selection_succeeds(contract):
    result = _run_checker("--contract", contract)
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert lines[-1] == "CONTRACT_ARTIFACTS_OK"
    assert len(lines) == 2
    assert lines[0].startswith(f"{contract}:")


def test_constructor_bound_deployed_runtime_facts_are_compiler_backed():
    contracts = _load_expectations()["contracts"]

    for name, deployed in DEPLOYED_RUNTIME_FACTS.items():
        artifacts = contracts[name]["artifacts"]
        assert contracts[name]["constructor_bound_runtime_template"] is True
        assert deployed["size"] + deployed["headroom"] == EIP_170_LIMIT
        assert artifacts["deployed_runtime_size"] == deployed["size"]
        assert artifacts["deployed_eip170_headroom"] == deployed["headroom"]
        assert (
            artifacts["runtime_template_size"] + artifacts["eip170_headroom"]
            == EIP_170_LIMIT
        )
        assert (
            artifacts["runtime_template_size"],
            artifacts["eip170_headroom"],
        ) != (deployed["size"], deployed["headroom"])


def test_creation_prefix_and_compiler_metadata_have_per_contract_boundaries():
    contracts = _load_expectations()["contracts"]
    metadata_sizes = {
        record["artifacts"]["creation_metadata_size"]
        for record in contracts.values()
    }

    assert len(metadata_sizes) > 1
    vyper = artifact_checker._vyper_path()
    for name, record in contracts.items():
        facts = record["artifacts"]
        compiled = artifact_checker._compile(ROOT / record["source_path"], vyper)
        binding = artifact_checker._creation_binding(
            compiled.creation,
            integrity=compiled.integrity,
            runtime_template=compiled.runtime_template,
        )
        assert (
            len(binding.executable_prefix) + len(binding.compiler_metadata)
            == record["artifacts"]["creation_size"]
        )
        assert len(binding.executable_prefix) == facts["creation_executable_prefix_size"]
        assert artifact_checker._sha256(binding.executable_prefix) == (
            facts["creation_executable_prefix_sha256"]
        )
        assert len(binding.compiler_metadata) == facts["creation_metadata_size"]
        assert artifact_checker._sha256(binding.compiler_metadata) == (
            facts["creation_metadata_sha256"]
        )


def test_compiler_metadata_integrity_must_bind_compiler_inputs():
    vyper = artifact_checker._vyper_path()
    compiled = artifact_checker._compile(
        ROOT / "contracts" / "core" / "Teller.vy",
        vyper,
    )

    with pytest.raises(
        artifact_checker.ArtifactCheckError,
        match="metadata integrity does not bind compiler inputs",
    ):
        artifact_checker._creation_binding(
            compiled.creation,
            integrity="00" * 32,
            runtime_template=compiled.runtime_template,
        )


def test_prefix_or_metadata_byte_tampering_breaks_the_frozen_creation_binding():
    vyper = artifact_checker._vyper_path()
    compiled = artifact_checker._compile(
        ROOT / "contracts" / "core" / "Teller.vy",
        vyper,
    )
    expected = _load_expectations()["contracts"]["Teller"]
    binding = artifact_checker._creation_binding(
        compiled.creation,
        integrity=compiled.integrity,
        runtime_template=compiled.runtime_template,
    )

    tampered_prefix = bytearray(compiled.creation)
    tampered_prefix[0] ^= 1
    tampered_prefix_binding = artifact_checker._creation_binding(
        bytes(tampered_prefix),
        integrity=compiled.integrity,
        runtime_template=compiled.runtime_template,
    )
    assert artifact_checker._sha256(bytes(tampered_prefix)) != (
        expected["artifacts"]["creation_sha256"]
    )
    assert artifact_checker._sha256(
        tampered_prefix_binding.executable_prefix
    ) != expected["artifacts"]["creation_executable_prefix_sha256"]
    assert artifact_checker._sha256(tampered_prefix_binding.compiler_metadata) == (
        expected["artifacts"]["creation_metadata_sha256"]
    )

    tampered_metadata = bytearray(compiled.creation)
    metadata_start = len(tampered_metadata) - len(binding.compiler_metadata)
    tampered_metadata[metadata_start + 3] ^= 1
    with pytest.raises(
        artifact_checker.ArtifactCheckError,
        match="metadata integrity does not bind compiler inputs",
    ):
        artifact_checker._creation_binding(
            bytes(tampered_metadata),
            integrity=compiled.integrity,
            runtime_template=compiled.runtime_template,
        )


@pytest.mark.parametrize(
    ("contract", "source"),
    NEW_CONTRACT_SOURCES.items(),
)
def test_new_contract_tampered_source_copy_fails_closed(
    tmp_path, contract, source
):
    tampered = tmp_path / source.name
    tampered.write_bytes(source.read_bytes() + b"\n# Gate 1 negative mutation\n")

    result = _run_checker(
        "--contract",
        contract,
        "--source-override",
        f"{contract}={tampered}",
    )

    assert result.returncode == 1
    assert "source_sha256 mismatch" in result.stderr


@pytest.mark.parametrize("contract", NEW_CONTRACT_SOURCES)
def test_new_contract_tampered_expectation_fails_closed(tmp_path, contract):
    values = _load_expectations()
    values["contracts"][contract]["abi"]["canonical_sha256"] = "00" * 32
    tampered = _write_expectations(tmp_path, values)

    result = _run_checker(
        "--contract",
        contract,
        "--expectations",
        str(tampered),
    )

    assert result.returncode == 1
    assert "fresh canonical ABI versus frozen expectation mismatch" in (
        result.stderr
    )


@pytest.mark.parametrize(
    ("field_path", "replacement", "failure"),
    [
        (
            ("transitive_compiler_input_integrity",),
            "00" * 32,
            "transitive_compiler_input_integrity mismatch",
        ),
        (
            ("compiler_settings", "optimize"),
            "gas",
            "compiler_settings mismatch",
        ),
        (
            ("artifacts", "runtime_template_sha256"),
            "00" * 32,
            "runtime_template_sha256 mismatch",
        ),
    ],
)
def test_deleverage_compiler_and_runtime_identity_drift_fails_closed(
    tmp_path, field_path, replacement, failure
):
    values = _load_expectations()
    target = values["contracts"]["Deleverage"]
    for key in field_path[:-1]:
        target = target[key]
    target[field_path[-1]] = replacement
    tampered = _write_expectations(tmp_path, values)

    result = _run_checker(
        "--contract",
        "Deleverage",
        "--expectations",
        str(tampered),
    )

    assert result.returncode == 1
    assert failure in result.stderr


def test_tampered_source_copy_fails_closed(tmp_path):
    source = ROOT / "contracts" / "core" / "Teller.vy"
    tampered = tmp_path / "Teller.vy"
    tampered.write_bytes(source.read_bytes() + b"\n# S1 negative source mutation\n")

    result = _run_checker(
        "--contract",
        "Teller",
        "--source-override",
        f"Teller={tampered}",
    )

    assert result.returncode == 1
    assert "source_sha256 mismatch" in result.stderr


def test_tampered_expectation_fails_closed(tmp_path):
    values = _load_expectations()
    values["contracts"]["Teller"]["abi"]["canonical_sha256"] = "00" * 32
    tampered = _write_expectations(tmp_path, values)

    result = _run_checker(
        "--contract",
        "Teller",
        "--expectations",
        str(tampered),
    )

    assert result.returncode == 1
    assert "fresh canonical ABI versus frozen expectation mismatch" in (
        result.stderr
    )


def test_tampered_layout_expectation_fails_closed(tmp_path):
    values = _load_expectations()
    values["contracts"]["Teller"]["storage_layout"] = {}
    tampered = _write_expectations(tmp_path, values)

    result = _run_checker(
        "--contract",
        "Teller",
        "--expectations",
        str(tampered),
    )

    assert result.returncode == 1
    assert "persistent storage layout mismatch" in result.stderr


def test_optimize_override_conflicts_with_pragma_bound_contract():
    vyper = Path(sys.executable).with_name("vyper")
    result = subprocess.run(
        [
            str(vyper),
            "-O",
            "gas",
            "-p",
            ".",
            "-f",
            "bytecode",
            "contracts/core/Teller.vy",
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "settings conflict!" in result.stderr
    assert "source pragma indicates codesize" in result.stderr
