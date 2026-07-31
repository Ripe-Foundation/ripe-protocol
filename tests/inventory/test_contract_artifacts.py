from __future__ import annotations

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
        "GuardedErc20",
        "Ledger",
        "Lootbox",
        "SwitchboardDelta",
        "Teller",
    }
)
NEW_CONTRACT_SOURCES = {
    "AuctionHouse": ROOT / "contracts" / "core" / "AuctionHouse.vy",
    "Deleverage": ROOT / "contracts" / "core" / "Deleverage.vy",
    "SwitchboardDelta": ROOT / "contracts" / "config" / "SwitchboardDelta.vy",
}

# These are constructor-bound deployed-code measurements. They are deliberately
# distinct from the pre-constructor runtime-template values frozen in the JSON.
DEPLOYED_RUNTIME_FACTS = {
    "AuctionHouse": {"size": 24_469, "headroom": 107},
    "Deleverage": {"size": 24_569, "headroom": 7},
}
CREATION_BINDING_FACTS = {
    "AuctionHouse": {
        "prefix_size": 24_497,
        "prefix_sha256": "dcd9dc89c963925e01679613aa03e1ab2229063c9b2e6446b1a3c91976476a45",
        "metadata_size": 59,
        "metadata_sha256": "f9c98ba80dfb11b6352093908bcf8ba4fc99ab1e4a4372488ef5dea4024a7b0e",
    },
    "CreditEngine": {
        "prefix_size": 24_266,
        "prefix_sha256": "5e27e6db4d007533d5d3c38dc50acb79209a53bd44962dfa69b5195bff0ff736",
        "metadata_size": 70,
        "metadata_sha256": "0677fbc6cf3571701c7f82afa6fb521df7beaadea383c945e871bda1338b5132",
    },
    "Deleverage": {
        "prefix_size": 24_833,
        "prefix_sha256": "26ff82b5e245dbcc146adc36452a4352581c81d04820d95194fe58611d49e219",
        "metadata_size": 61,
        "metadata_sha256": "0e52a5555be52eda112bd98d8a9a6ddf439f00837b49eb27a5aa8363065273ac",
    },
    "GuardedErc20": {
        "prefix_size": 10_635,
        "prefix_sha256": "fc362fc65e3f5fb4cc2a5e8e5715580aa16f699f0af72f7567fc308eeb1a9c2d",
        "metadata_size": 56,
        "metadata_sha256": "1c2dced73bd886916233eaacbe6ed0399c6ca87c6a7e309cc7feb131bb133a90",
    },
    "Ledger": {
        "prefix_size": 13_674,
        "prefix_sha256": "51d9b8ad87d7ac50b58c8004a623f067ddfa26b9d7c84e4ff1de3c459dd29fce",
        "metadata_size": 56,
        "metadata_sha256": "3d532fe4ad921b1c38182671d4f0dc502eddf4870e58da828cb0d7c963dcc28f",
    },
    "Lootbox": {
        "prefix_size": 21_848,
        "prefix_sha256": "53dac6ede2946eaf838c64e845b963cce61fcda37112be966ce977febc454d70",
        "metadata_size": 63,
        "metadata_sha256": "9ece9d291e68621d380f08bc035c2e47b4004fe9606faa7831987ca6de361c00",
    },
    "SwitchboardDelta": {
        "prefix_size": 24_305,
        "prefix_sha256": "5d7e5a00144259460b75b0e623b3371b05e122c4491423f42c6ca7e49ae6fe4f",
        "metadata_size": 84,
        "metadata_sha256": "cc1bcadb5528be3f406a18544734a3a08de07719ec230abf79ff988ac1428f18",
    },
    "Teller": {
        "prefix_size": 24_295,
        "prefix_sha256": "0c6cffa7d91b251a741cfca71db077d21d96947cd2295e819b4756dc8e3b64eb",
        "metadata_size": 92,
        "metadata_sha256": "7b68fed219ab8fe328e064e4edc044d0d6d0dcfdcda397977826e660c095ec4a",
    },
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


def test_guarded_and_simple_canonical_selectors_and_layout_match():
    vyper = artifact_checker._vyper_path()
    guarded = artifact_checker._compile(
        ROOT / "contracts" / "vaults" / "GuardedErc20.vy",
        vyper,
    )
    simple = artifact_checker._compile(
        ROOT / "contracts" / "vaults" / "SimpleErc20.vy",
        vyper,
    )

    assert guarded.method_identifiers == simple.method_identifiers
    assert len(guarded.method_identifiers) == 34
    assert guarded.storage_layout == simple.storage_layout
    assert guarded.transient_storage_layout == simple.transient_storage_layout
    assert guarded.code_layout == simple.code_layout

    guarded_functions = [
        entry for entry in guarded.abi if entry.get("type") == "function"
    ]
    simple_functions = [
        entry for entry in simple.abi if entry.get("type") == "function"
    ]
    assert guarded_functions == simple_functions
    assert [
        entry for entry in guarded.abi if entry.get("type") == "constructor"
    ] == [
        entry for entry in simple.abi if entry.get("type") == "constructor"
    ]


@pytest.mark.parametrize("contract", NEW_CONTRACT_SOURCES)
def test_new_contract_selection_succeeds(contract):
    result = _run_checker("--contract", contract)
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert lines[-1] == "CONTRACT_ARTIFACTS_OK"
    assert len(lines) == 2
    assert lines[0].startswith(f"{contract}:")


def test_constructor_bound_deployed_runtime_facts_are_not_template_headroom():
    contracts = json.loads(EXPECTATIONS.read_text())["contracts"]

    for name, deployed in DEPLOYED_RUNTIME_FACTS.items():
        artifacts = contracts[name]["artifacts"]
        assert contracts[name]["constructor_bound_runtime_template"] is True
        assert deployed["size"] + deployed["headroom"] == EIP_170_LIMIT
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
    metadata_sizes = {facts["metadata_size"] for facts in CREATION_BINDING_FACTS.values()}

    assert len(metadata_sizes) > 1
    assert set(CREATION_BINDING_FACTS) == REQUIRED_CONTRACTS
    vyper = artifact_checker._vyper_path()
    for name, facts in CREATION_BINDING_FACTS.items():
        record = contracts[name]
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
        assert len(binding.executable_prefix) == facts["prefix_size"]
        assert artifact_checker._sha256(binding.executable_prefix) == (
            facts["prefix_sha256"]
        )
        assert len(binding.compiler_metadata) == facts["metadata_size"]
        assert artifact_checker._sha256(binding.compiler_metadata) == (
            facts["metadata_sha256"]
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
    ) != CREATION_BINDING_FACTS["Teller"]["prefix_sha256"]
    assert artifact_checker._sha256(tampered_prefix_binding.compiler_metadata) == (
        CREATION_BINDING_FACTS["Teller"]["metadata_sha256"]
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
