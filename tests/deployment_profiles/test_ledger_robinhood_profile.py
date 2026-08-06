"""DRAFT — owner approval required before integration or use."""

import copy
import hashlib
import sys
import types
from pathlib import Path

import boa
import pytest
from eth_utils import keccak, to_checksum_address

from scripts.proposals import ledger_robinhood_profile as profile


L3B_MANIFEST_MUTATION_SHA256 = {
    profile.ZERO_ADDRESS: (
        "ece7fa2b42d892e7e46b199e75f9050a"
        "397b8a89dd6d1ed2328fbb1715ca81e0"
    ),
    "0x0000000000000000000000000000000000000065": (
        "259a192a718e82f6866ea3c4807b7c0"
        "add05208ef051ab1a3407cc22fe66cbb4"
    ),
}
L3B_SOURCE_MUTATION_SHA256 = {
    "immutable_readback": (
        "03c63ca6744e62024fe7ffaa573110554f"
        "c68f08513cf505afd4dd05cea48785"
    ),
    "post_deploy_assertions": (
        "9fd01fe6ee51b2f15162670761516e227"
        "f6b5fcfce38b837366e6c0e87e6dd6d"
    ),
}


def _unsupported_sources():
    fixed = [
        "0x0000000000000000000000000000000000000000",
        "0x0000000000000000000000000000000000000001",
        "0x0000000000000000000000000000000000000063",
        "0x0000000000000000000000000000000000000065",
        "0xffffffffffffffffffffffffffffffffffffffff",
    ]
    derived = [
        to_checksum_address(keccak(text=f"unsupported-rh-source:{index}")[-20:])
        for index in range(8)
    ]
    return fixed + derived


def _manifest_with_source(source):
    manifest = copy.deepcopy(profile.load_manifest())
    manifest["constructor"]["action_block_source"] = source
    manifest["constructor"]["ordered_arguments"][2] = source
    return manifest


def _load_source_mutant(old, new, name, expected_sha256):
    source = Path(profile.__file__).read_text()
    assert source.count(old) == 1
    mutant = source.replace(old, new, 1)
    assert hashlib.sha256(mutant.encode()).hexdigest() == expected_sha256
    module = types.ModuleType(name)
    module.__file__ = str(Path(profile.__file__))
    sys.modules[name] = module
    exec(compile(mutant, module.__file__, "exec"), module.__dict__)
    return module


def test_r1_manifest_is_canonical_draft_with_deterministic_placeholders():
    manifest = profile.load_manifest()
    profile.validate_manifest(manifest)
    assert profile.MANIFEST_PATH.read_bytes() == profile.canonical_json_bytes(
        manifest
    )
    assert b"\r" not in profile.MANIFEST_PATH.read_bytes()
    assert b"/Users/" not in profile.MANIFEST_PATH.read_bytes()
    assert "timestamp" not in manifest

    for name, label in profile.PLACEHOLDER_LABELS.items():
        entry = manifest["inputs"][name]
        assert entry["address"] == profile.deterministic_placeholder_address(
            label
        )
        assert entry["approval_status"] == "unapproved_placeholder"


def test_r1_compiles_reviewed_ledger_with_pinned_source_owned_settings():
    compiled = profile.compile_reviewed_ledger()
    assert len(compiled.creation) == 13_730
    assert len(compiled.runtime_template) == 13_125
    assert compiled.integrity == (
        "62cc9e492ee1b1a3e84ad104507d684dc"
        "81edecef969fc0ae0f7a1586dd0d830"
    )


def test_r1_local_profile_deploys_exact_0x64_and_completes_all_readbacks():
    result = profile.deploy_local_robinhood_profile()
    assert result.ledger.ACTION_BLOCK_SOURCE() == profile.ARB_SYS
    assert result.ledger.getRipeHq() == result.manifest["inputs"]["ripe_hq"][
        "address"
    ]
    assert result.evidence == {
        key: True for key in profile.REQUIRED_EVIDENCE
    }


@pytest.mark.parametrize("source", _unsupported_sources())
def test_r1_robinhood_profile_rejects_zero_and_sampled_unsupported_sources(
    source,
):
    with pytest.raises(
        profile.ProfileGateError,
        match="requires exact action-block source 0x64",
    ):
        profile.validate_manifest(_manifest_with_source(source))


def test_r1_unsupported_source_space_is_closed_by_contract_two_branch_allowlist():
    source = profile.LEDGER_PATH.read_text()
    assert source.count(
        "assert _actionBlockSource in [empty(address), ARB_SYS]"
    ) == 1
    assert source.count("if _actionBlockSource == ARB_SYS:") == 1
    assert "ACTION_BLOCK_SOURCE = _actionBlockSource" in source


def test_l3b_zero_or_wrong_source_mutant_fails_the_profile_gate():
    baseline = profile.load_manifest()
    for source, expected_sha256 in L3B_MANIFEST_MUTATION_SHA256.items():
        mutant = _manifest_with_source(source)
        assert mutant["constructor"]["action_block_source"] != (
            baseline["constructor"]["action_block_source"]
        )
        assert mutant["constructor"]["ordered_arguments"][2] != (
            baseline["constructor"]["ordered_arguments"][2]
        )
        assert hashlib.sha256(
            profile.canonical_json_bytes(mutant)
        ).hexdigest() == expected_sha256
        with pytest.raises(profile.ProfileGateError):
            profile.deploy_local_robinhood_profile(mutant)


def test_l3b_omitted_immutable_readback_mutant_fails_evidence_completeness():
    mutant = _load_source_mutant(
        '    evidence["action_block_source_readback"] = (\n'
        "        ledger.ACTION_BLOCK_SOURCE() == ARB_SYS\n"
        "    )\n",
        "",
        "ledger_profile_no_immutable_readback",
        L3B_SOURCE_MUTATION_SHA256["immutable_readback"],
    )
    with pytest.raises(
        mutant.ProfileGateError,
        match="incomplete profile evidence",
    ):
        mutant.deploy_local_robinhood_profile()


def test_l3b_omitted_post_deploy_assertions_mutant_fails_evidence_completeness():
    mutant = _load_source_mutant(
        "    evidence.update(_post_deploy_assertions(ledger, selected))\n",
        "",
        "ledger_profile_no_post_deploy_assertions",
        L3B_SOURCE_MUTATION_SHA256["post_deploy_assertions"],
    )
    with pytest.raises(
        mutant.ProfileGateError,
        match="incomplete profile evidence",
    ):
        mutant.deploy_local_robinhood_profile()


def test_l3b_failed_readback_stops_before_profile_result(monkeypatch):
    original = profile._post_deploy_assertions

    def mismatched_readback(ledger, manifest):
        evidence = original(ledger, manifest)
        evidence["ripe_hq_readback"] = False
        return evidence

    monkeypatch.setattr(
        profile,
        "_post_deploy_assertions",
        mismatched_readback,
    )
    with pytest.raises(
        profile.ProfileGateError,
        match="post-deploy assertions failed",
    ):
        profile.deploy_local_robinhood_profile()
