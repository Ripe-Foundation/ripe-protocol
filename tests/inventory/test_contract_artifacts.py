from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import subprocess
import sys
from pathlib import Path

import boa
import pytest

from scripts import check_contract_artifacts as artifact_checker
from scripts import capture_contract_runtimes as runtime_capture
from scripts import export_abis as abi_exporter
from scripts import update_contract_artifact_expectations as artifact_updater


ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "scripts" / "check_contract_artifacts.py"
EXPECTATIONS = ROOT / "config" / "contract-artifact-expectations.json"
EIP_170_LIMIT = 24_576
REQUIRED_CONTRACTS = frozenset(
    {
        "AuctionHouse",
        "BlueChipYieldPrices",
        "CreditEngine",
        "Deleverage",
        "DefaultsRobinhood",
        "DefaultsRobinhoodLive",
        "SimpleErc20",
        "Ledger",
        "Lootbox",
        "MissionControl",
        "RipeGov",
        "SwitchboardAlpha",
        "SwitchboardDelta",
        "SwitchboardBravo",
        "SwitchboardCharlie",
        "StabilityPool",
        "Teller",
        "UniswapV2Prices",
        "VaultMigrator",
    }
)
NEW_CONTRACT_SOURCES = {
    "AuctionHouse": ROOT / "contracts" / "core" / "AuctionHouse.vy",
    "BlueChipYieldPrices": (
        ROOT / "contracts" / "priceSources" / "BlueChipYieldPrices.vy"
    ),
    "Deleverage": ROOT / "contracts" / "core" / "Deleverage.vy",
    "DefaultsRobinhood": ROOT / "contracts" / "config" / "DefaultsRobinhood.vy",
    "DefaultsRobinhoodLive": (
        ROOT / "contracts" / "config" / "DefaultsRobinhoodLive.vy"
    ),
    "SwitchboardDelta": ROOT / "contracts" / "config" / "SwitchboardDelta.vy",
    "MissionControl": ROOT / "contracts" / "data" / "MissionControl.vy",
    "RipeGov": ROOT / "contracts" / "vaults" / "RipeGov.vy",
    "StabilityPool": ROOT / "contracts" / "vaults" / "StabilityPool.vy",
    "SwitchboardAlpha": ROOT / "contracts" / "config" / "SwitchboardAlpha.vy",
    "SwitchboardBravo": ROOT / "contracts" / "config" / "SwitchboardBravo.vy",
    "SwitchboardCharlie": (
        ROOT / "contracts" / "config" / "SwitchboardCharlie.vy"
    ),
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


@pytest.fixture(scope="session")
def ripe_hq() -> None:
    """Compiler-only inventory tests do not need the autouse protocol graph."""


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


def _write_capture_fixture(tmp_path: Path, monkeypatch):
    capture_dir = tmp_path / "capture"
    capture_dir.mkdir()
    provenance = runtime_capture.expected_capture_provenance()
    runtime_paths = {}
    records = {}
    for name in sorted(artifact_checker.DEPLOYED_RUNTIME_CONTRACTS):
        runtime = f"runtime:{name}".encode()
        runtime_path = capture_dir / f"{name}.runtime"
        runtime_path.write_bytes(runtime)
        runtime_paths[name] = runtime_path.resolve()
        source = ROOT / artifact_checker.GOVERNED_SOURCES[name]
        records[name] = {
            **provenance[name],
            "source_sha256": artifact_checker._sha256(source.read_bytes()),
            "runtime_file": runtime_path.name,
            "runtime_sha256": artifact_checker._sha256(runtime),
            "runtime_size": len(runtime),
        }

    manifest = {
        "schema_version": runtime_capture.CAPTURE_SCHEMA_VERSION,
        "status": "complete",
        "repository": {
            "root": str(ROOT.resolve()),
            "head": "fixture-head",
            "tree": "fixture-tree",
            "source_status": "",
        },
        "capture_script": {
            "path": "scripts/capture_contract_runtimes.py",
            "sha256": artifact_checker._sha256(
                Path(runtime_capture.__file__).read_bytes()
            ),
        },
        "toolchain": {
            "python": os.path.realpath(sys.executable),
            "titanoboa": importlib.metadata.version("titanoboa"),
            "vyper": "fixture-vyper",
        },
        "governed_contracts": sorted(artifact_checker.GOVERNED_CONTRACTS),
        "runtime_contracts": sorted(
            artifact_checker.DEPLOYED_RUNTIME_CONTRACTS
        ),
        "template_identity_contracts": ["DefaultsRobinhoodLive"],
        "contracts": records,
    }
    manifest_path = capture_dir / runtime_capture.CAPTURE_MANIFEST
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    def fake_git(*arguments):
        if arguments == ("rev-parse", "HEAD^{commit}"):
            return "fixture-head"
        if arguments == ("rev-parse", "HEAD^{tree}"):
            return "fixture-tree"
        if arguments and arguments[0] == "status":
            return ""
        raise AssertionError(arguments)

    monkeypatch.setattr(artifact_updater, "_git", fake_git)
    return manifest_path, runtime_paths, manifest


def test_artifact_pipeline_strict_updater_rejects_positional_filter():
    with pytest.raises(
        artifact_checker.ArtifactCheckError,
        match="forbids positional contract filters",
    ):
        artifact_updater.main(
            ["--require-deployed-runtime-bindings", "Teller"]
        )


def test_artifact_pipeline_strict_updater_requires_exact_runtime_census():
    with pytest.raises(
        artifact_checker.ArtifactCheckError,
        match="strict deployed-runtime input census mismatch",
    ):
        artifact_updater.main(["--require-deployed-runtime-bindings"])


def test_artifact_pipeline_strict_checker_rejects_contract_filter(
    tmp_path,
    monkeypatch,
):
    values = json.loads(EXPECTATIONS.read_text())
    for name in artifact_checker.GOVERNED_CONTRACTS:
        values["contracts"].setdefault(name, {})
    expectations = _write_expectations(tmp_path, values)
    monkeypatch.setattr(
        artifact_checker,
        "_validate_compiler_envelope",
        lambda *_args: None,
    )

    with pytest.raises(
        artifact_checker.ArtifactCheckError,
        match="forbids --contract filters",
    ):
        artifact_checker.check(
            expectations,
            ("DefaultsRobinhoodLive",),
            {},
            require_deployed_runtime_bindings=True,
        )


@pytest.mark.parametrize("mode", ["missing", "unexpected"])
def test_artifact_pipeline_strict_checker_rejects_noncanonical_record_set(
    tmp_path,
    monkeypatch,
    mode,
):
    values = json.loads(EXPECTATIONS.read_text())
    if mode == "unexpected":
        for name in artifact_checker.GOVERNED_CONTRACTS:
            values["contracts"].setdefault(name, {})
        values["contracts"]["TellerAlias"] = values["contracts"]["Teller"]
    expectations = _write_expectations(tmp_path, values)
    monkeypatch.setattr(
        artifact_checker,
        "_validate_compiler_envelope",
        lambda *_args: None,
    )

    with pytest.raises(
        artifact_checker.ArtifactCheckError,
        match="strict governed contract set mismatch",
    ):
        artifact_checker.check(
            expectations,
            (),
            {},
            require_deployed_runtime_bindings=True,
        )


def test_artifact_pipeline_atomic_expectations_replace_preserves_prior_on_failure(
    tmp_path,
    monkeypatch,
):
    target = tmp_path / "expectations.json"
    target.write_bytes(b"prior")

    def fail_replace(*_args):
        raise OSError("injected replace failure")

    monkeypatch.setattr(artifact_checker.os, "replace", fail_replace)
    with pytest.raises(OSError, match="injected replace failure"):
        artifact_checker._atomic_write_bytes(target, b"replacement")
    assert target.read_bytes() == b"prior"
    assert {path.name for path in tmp_path.iterdir()} == {target.name}


def test_artifact_pipeline_abi_completion_seal_rejects_interrupted_generation(
    tmp_path,
):
    expected = {"Alpha.json": b"[]"}
    assert abi_exporter._completion_drift(tmp_path, expected) == (
        "missing ABI export completion seal",
    )
    seal = tmp_path / abi_exporter.ABI_EXPORT_COMPLETION
    abi_exporter._atomic_write_bytes(
        seal,
        abi_exporter._completion_bytes(expected, "in_progress"),
    )
    assert abi_exporter._completion_drift(tmp_path, expected) == (
        "stale or incomplete ABI export completion seal",
    )
    abi_exporter._atomic_write_bytes(
        seal,
        abi_exporter._completion_bytes(expected, "complete"),
    )
    assert abi_exporter._completion_drift(tmp_path, expected) == ()


def test_artifact_pipeline_source_lookup_is_exact_not_basename_driven(
    tmp_path,
    monkeypatch,
):
    canonical = tmp_path / artifact_checker.GOVERNED_SOURCES["Teller"]
    canonical.parent.mkdir(parents=True)
    canonical.write_text("canonical")
    mock = tmp_path / "contracts" / "mock" / "Teller.vy"
    mock.parent.mkdir(parents=True)
    mock.write_text("wrong basename match")
    monkeypatch.setattr(artifact_updater, "ROOT", tmp_path)

    assert artifact_updater._source_for("Teller") == canonical
    canonical.unlink()
    with pytest.raises(
        artifact_checker.ArtifactCheckError,
        match="canonical governed source is missing",
    ):
        artifact_updater._source_for("Teller")


@pytest.mark.parametrize("field", sorted(artifact_checker.COMPILER_ENVELOPE))
def test_artifact_pipeline_validates_every_compiler_envelope_field(
    monkeypatch,
    field,
):
    values = json.loads(EXPECTATIONS.read_text())
    values["compiler"][field] = "tampered"
    monkeypatch.setattr(
        artifact_checker,
        "_run",
        lambda *_args, **_kwargs: values["compiler"]["version"],
    )
    with pytest.raises(
        artifact_checker.ArtifactCheckError,
        match=field,
    ):
        artifact_checker._validate_compiler_envelope(values, Path("vyper"))


def test_artifact_pipeline_capture_provenance_is_exact_and_state_honest():
    provenance = runtime_capture.expected_capture_provenance()
    assert set(provenance) == artifact_checker.DEPLOYED_RUNTIME_CONTRACTS
    assert artifact_checker.DEPLOYED_RUNTIME_CONTRACTS == (
        artifact_checker.GOVERNED_CONTRACTS - {"DefaultsRobinhoodLive"}
    )
    teller_inputs = provenance["Teller"]["constructor_inputs"]
    assert teller_inputs[-1] == {
        "name": "_shouldPause",
        "type": "bool",
        "value": True,
    }
    assert "storage and post-deploy state require" in provenance["Teller"][
        "prospective_state"
    ]["runtime_identity_limit"]


def test_artifact_pipeline_capture_command_is_directly_invocable():
    result = subprocess.run(
        [sys.executable, "scripts/capture_contract_runtimes.py", "--help"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert "--output-dir" in result.stdout


def test_artifact_pipeline_capture_manifest_authenticates_all_records(
    tmp_path,
    monkeypatch,
):
    manifest_path, runtime_paths, manifest = _write_capture_fixture(
        tmp_path,
        monkeypatch,
    )
    assert artifact_updater._validate_capture_manifest(
        manifest_path,
        runtime_paths,
        "fixture-vyper",
    ) == manifest


@pytest.mark.parametrize("tamper", ["constructor", "runtime", "extra_file"])
def test_artifact_pipeline_capture_manifest_rejects_mixed_or_tampered_generation(
    tmp_path,
    monkeypatch,
    tamper,
):
    manifest_path, runtime_paths, manifest = _write_capture_fixture(
        tmp_path,
        monkeypatch,
    )
    if tamper == "constructor":
        manifest["contracts"]["Teller"]["constructor_inputs"][-1]["value"] = False
        manifest_path.write_text(json.dumps(manifest, sort_keys=True))
        match = "constructor_inputs provenance mismatch"
    elif tamper == "runtime":
        runtime_paths["Teller"].write_bytes(b"stale runtime from another capture")
        match = "captured runtime size mismatch"
    else:
        (manifest_path.parent / "stale.runtime").write_bytes(b"stale")
        match = "capture directory census mismatch"

    with pytest.raises(artifact_checker.ArtifactCheckError, match=match):
        artifact_updater._validate_capture_manifest(
            manifest_path,
            runtime_paths,
            "fixture-vyper",
        )


def test_artifact_pipeline_capture_requires_root_clean_sources_and_fresh_output(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(
        artifact_checker.ArtifactCheckError,
        match="must run from the repository root",
    ):
        runtime_capture._require_capture_context(tmp_path / "wrong-cwd")

    monkeypatch.chdir(ROOT)
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(
        artifact_checker.ArtifactCheckError,
        match="output already exists",
    ):
        runtime_capture._require_capture_context(existing)

    monkeypatch.setattr(runtime_capture, "_git", lambda *_args: " M contracts/X.vy")
    with pytest.raises(
        artifact_checker.ArtifactCheckError,
        match="requires clean tracked and untracked",
    ):
        runtime_capture._require_capture_context(tmp_path / "fresh")


def test_artifact_pipeline_rejects_duplicate_unknown_and_unused_overrides(
    monkeypatch,
):
    with pytest.raises(
        artifact_checker.ArtifactCheckError,
        match="duplicate source override",
    ):
        artifact_checker._parse_source_overrides(
            ["Teller=/tmp/one", "Teller=/tmp/two"]
        )

    monkeypatch.setattr(
        artifact_checker,
        "_validate_compiler_envelope",
        lambda *_args: None,
    )
    with pytest.raises(
        artifact_checker.ArtifactCheckError,
        match="unknown source override contract",
    ):
        artifact_checker.check(
            EXPECTATIONS,
            ("Teller",),
            {"Telller": Path("/tmp/typo")},
        )
    with pytest.raises(
        artifact_checker.ArtifactCheckError,
        match="unselected contract",
    ):
        artifact_checker.check(
            EXPECTATIONS,
            ("Teller",),
            {"Ledger": Path("/tmp/unused")},
        )


def test_artifact_pipeline_checker_reports_deployed_size_and_headroom():
    result = _run_checker("--contract", "DefaultsRobinhood")
    assert result.returncode == 0, result.stderr
    assert "template-headroom=" in result.stdout
    assert "deployed-runtime=" in result.stdout
    assert "deployed-headroom=" in result.stdout


def test_frozen_required_contract_set_is_exact():
    values = json.loads(EXPECTATIONS.read_text())
    assert set(values["contracts"]) == REQUIRED_CONTRACTS
    assert artifact_updater.GOVERNED_CONTRACTS == REQUIRED_CONTRACTS


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
        (
            "not a deployed-runtime identity; constructor immutables" in line
            or "full deployed-runtime identity bound" in line
        )
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
    contracts = json.loads(EXPECTATIONS.read_text())["contracts"]

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


def test_constructor_bound_runtime_binding_covers_exact_immutable_suffix(
    tmp_path,
):
    values = json.loads(EXPECTATIONS.read_text())
    record = values["contracts"]["Teller"]
    compiled = artifact_checker._compile(
        ROOT / record["source_path"],
        artifact_checker._vyper_path(),
    )
    immutable_data = b"\x00" * artifact_checker._code_data_size(
        compiled.code_layout
    )
    binding = artifact_checker._deployed_runtime_binding(
        compiled,
        immutable_data.hex(),
    )
    record["artifacts"].update(
        {
            "deployed_runtime_immutable_data_hex": immutable_data.hex(),
            "deployed_runtime_immutable_data_sha256": (
                artifact_checker._sha256(immutable_data)
            ),
            "deployed_runtime_immutable_data_size": len(immutable_data),
            "deployed_runtime_sha256": artifact_checker._sha256(
                binding.runtime
            ),
        }
    )
    expectations = _write_expectations(tmp_path, values)

    result = _run_checker(
        "--contract",
        "Teller",
        "--expectations",
        str(expectations),
        "--require-deployed-runtime-bindings",
    )
    assert result.returncode == 0, result.stderr
    assert "full deployed-runtime identity bound" in result.stdout

    values["contracts"]["Teller"]["artifacts"][
        "deployed_runtime_sha256"
    ] = "00" * 32
    tampered = _write_expectations(tmp_path, values)
    result = _run_checker(
        "--contract",
        "Teller",
        "--expectations",
        str(tampered),
        "--require-deployed-runtime-bindings",
    )
    assert result.returncode == 1
    assert "constructor-bound deployed runtime SHA-256 mismatch" in result.stderr


def test_constructor_bound_runtime_binding_rejects_wrong_suffix_size():
    compiled = artifact_checker._compile(
        ROOT / "contracts" / "core" / "Teller.vy",
        artifact_checker._vyper_path(),
    )
    with pytest.raises(
        artifact_checker.ArtifactCheckError,
        match="constructor immutable data size mismatch",
    ):
        artifact_checker._deployed_runtime_binding(compiled, "")


def test_measured_boa_runtime_is_template_plus_exact_immutable_suffix():
    source = ROOT / "contracts" / "config" / "DefaultsRobinhood.vy"
    constructor_args = [f"0x{value:040x}" for value in range(1, 8)]
    compiled = artifact_checker._compile(
        source,
        artifact_checker._vyper_path(),
    )

    with boa.env.anchor():
        deployed = boa.load(
            str(source),
            *constructor_args,
            name="artifact_runtime_binding_probe",
        )
        measured_runtime = bytes(boa.env.get_code(deployed.address))

    binding = artifact_checker._extract_deployed_runtime_binding(
        compiled,
        measured_runtime,
    )
    expected_immutables = b"".join(
        value.to_bytes(32, "big") for value in range(1, 8)
    )
    assert binding.immutable_data == expected_immutables
    assert binding.runtime == compiled.runtime_template + expected_immutables


def test_creation_prefix_and_compiler_metadata_have_per_contract_boundaries():
    contracts = json.loads(EXPECTATIONS.read_text())["contracts"]
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
    expected = json.loads(EXPECTATIONS.read_text())["contracts"]["Teller"]
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
    values = json.loads(EXPECTATIONS.read_text())
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
    values = json.loads(EXPECTATIONS.read_text())
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
    values = json.loads(EXPECTATIONS.read_text())
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
    values = json.loads(EXPECTATIONS.read_text())
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
