from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from config.robinhood_blueprint import Disposition, get_component
from scripts import check_contract_artifacts as artifact_checker
from scripts.utils.deployment_assertions import blueprint_policy


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "contracts" / "priceSources" / "BlueChipYieldPrices.vy"
COMMITTED_ABI = ROOT / "scripts" / "abis" / "BlueChipYieldPrices.json"
EIP_170_LIMIT = 24_576
ACCEPTED_RUNTIME_CEILING = 22_500
MIN_EIP_170_HEADROOM = 2_000

EXPECTED = {
    "source_sha256": "abe188bf7edd973f6d68e58e39767e948471542030f6c2447ab98616c303e8be",
    "source_git_blob": "cafd177ef601186b0a6a30863ba5b8973d8dd92e",
    "integrity": "a7bd19991381dd4d3f1d6863e3b2291823a092c130402e62a18159f21bbeeff5",
    "creation_size": 23_627,
    "creation_sha256": "725ed0aee23fdf31d51fa720ecc1806976f1dff127d2c2c78ea3ce1d28f5ab6d",
    "runtime_size": 22_054,
    "runtime_sha256": "84e004bf72ed7a699c7b7c52d849674517f82581cd4f49b73a06f1721e6cf578",
    "eip_170_headroom": 2_522,
    "abi_sha256": "d1a7f8491d5b1ba59da03ef3e0920a6bbf7682dfc2f0b471d4a5a8a1cb8f5c73",
    "abi_file_sha256": "b4c17cf9a87cd3325fba306cc9e4a9595c2e0689c18fb4fc2da2aed5622e91f7",
    "selector_count": 84,
    "selectors_sha256": "c78a129a79302150f7ebb8e79d5331ee78a84da3818170425eb123e545a0d1fb",
    "event_count": 20,
    "events_sha256": "56a06017c846e4bb852a90e7d1c83089b9a82e2d383522b1446d57bef34f47b5",
    "constructor_sha256": "0a48ac2d0de1d907dd498d210086299a113f47a6138b1e431a9dc7ab69201f01",
    "storage_layout_sha256": "f093152f22b59501908a200a6173741b779f48aa95e603123bdc46989ab22b47",
    "transient_storage_layout_sha256": "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a",
    "code_layout_sha256": "a026a16b9def8bd3b4dd3036145dfaa9d64fb97812e7b7e8af1c27f1d4b9d518",
}


@pytest.fixture(scope="session")
def ripe_hq() -> None:
    """Override the repository's autouse deployment fixture for compiler checks."""


@pytest.fixture(scope="module")
def compiled():
    return artifact_checker._compile(SOURCE, artifact_checker._vyper_path())


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_exact_source_and_compiler_identity(compiled):
    assert compiled.source_sha256 == EXPECTED["source_sha256"]
    assert compiled.source_git_blob == EXPECTED["source_git_blob"]
    assert compiled.integrity == EXPECTED["integrity"]
    assert compiled.effective_optimization == "gas"
    assert compiled.settings == {
        "experimental_codegen": False,
        "optimize": "gas",
    }


def test_exact_creation_and_runtime_artifacts_with_headroom(compiled):
    assert len(compiled.creation) == EXPECTED["creation_size"]
    assert _sha256(compiled.creation) == EXPECTED["creation_sha256"]
    assert len(compiled.runtime_template) == EXPECTED["runtime_size"]
    assert _sha256(compiled.runtime_template) == EXPECTED["runtime_sha256"]
    assert len(compiled.runtime_template) <= ACCEPTED_RUNTIME_CEILING
    headroom = EIP_170_LIMIT - len(compiled.runtime_template)
    assert headroom == EXPECTED["eip_170_headroom"]
    assert headroom >= MIN_EIP_170_HEADROOM


def test_exact_abi_and_committed_abi_reconcile(compiled):
    committed_bytes = COMMITTED_ABI.read_bytes()
    committed = json.loads(committed_bytes)

    assert artifact_checker._json_sha256(compiled.abi) == EXPECTED["abi_sha256"]
    assert _sha256(committed_bytes) == EXPECTED["abi_file_sha256"]
    assert artifact_checker._canonical_json_bytes(compiled.abi) == (
        artifact_checker._canonical_json_bytes(committed)
    )
    constructor = next(entry for entry in compiled.abi if entry["type"] == "constructor")
    assert constructor["inputs"][-1] == {
        "name": "_morphoV2Addr",
        "type": "address",
    }
    assert compiled.method_identifiers["MORPHO_V2_ADDR()"] == "0xa436265d"


def test_exact_selectors_events_constructor_and_layouts(compiled):
    events = [entry for entry in compiled.abi if entry.get("type") == "event"]
    constructors = [
        entry for entry in compiled.abi if entry.get("type") == "constructor"
    ]

    assert len(compiled.method_identifiers) == EXPECTED["selector_count"]
    assert artifact_checker._json_sha256(compiled.method_identifiers) == EXPECTED[
        "selectors_sha256"
    ]
    assert len(events) == EXPECTED["event_count"]
    assert artifact_checker._json_sha256(events) == EXPECTED["events_sha256"]
    assert artifact_checker._json_sha256(constructors) == EXPECTED[
        "constructor_sha256"
    ]
    assert artifact_checker._json_sha256(compiled.storage_layout) == EXPECTED[
        "storage_layout_sha256"
    ]
    assert artifact_checker._json_sha256(
        compiled.transient_storage_layout
    ) == EXPECTED["transient_storage_layout_sha256"]
    assert artifact_checker._json_sha256(compiled.code_layout) == EXPECTED[
        "code_layout_sha256"
    ]


def test_compiler_outputs_are_deterministic(compiled):
    second = artifact_checker._compile(SOURCE, artifact_checker._vyper_path())

    assert second == compiled


def test_source_identity_mutation_is_detected(tmp_path):
    mutated = tmp_path / SOURCE.name
    mutated.write_bytes(SOURCE.read_bytes() + b"\n# negative source mutation\n")

    candidate = artifact_checker._compile(mutated, artifact_checker._vyper_path())
    assert candidate.source_sha256 != EXPECTED["source_sha256"]
    assert candidate.source_git_blob != EXPECTED["source_git_blob"]
    assert candidate.integrity != EXPECTED["integrity"]


def test_profile1_bluechip_topology_is_selected_in_slot_three():
    component = get_component("CM-018")
    policy = blueprint_policy()

    assert component.name == "BlueChipYieldPrices"
    assert component.deployment is Disposition.REQUIRED
    assert len(component.registry_expectations) == 1
    row = component.registry_expectations[0]
    assert (row.domain.value, row.registry_id, row.semantic_name) == (
        "price_desk",
        3,
        "BlueChipYield",
    )
    assert row.disposition is Disposition.REQUIRED
    assert policy.canonical_registries[("price_desk", 3)] == "CM-018"
    assert ("price_desk", 3) not in policy.reserved_registries
    assert ("price_desk", 3) in policy.required_registries
