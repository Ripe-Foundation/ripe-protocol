from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import check_contract_artifacts as artifact_checker


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


def test_frozen_required_contract_set_is_exact():
    values = json.loads(EXPECTATIONS.read_text())
    assert set(values["contracts"]) == REQUIRED_CONTRACTS


def test_migrated_source_settlement_has_no_caller_supplied_addys():
    abi = json.loads((ROOT / "scripts" / "abis" / "Lootbox.json").read_text())
    settlement = [
        entry
        for entry in abi
        if entry.get("type") == "function"
        and entry.get("name") == "settleAndCleanupMigratedSource"
    ]
    assert len(settlement) == 1
    assert [item["name"] for item in settlement[0]["inputs"]] == [
        "_user",
        "_sourceVaultId",
        "_sourceVault",
    ]


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
