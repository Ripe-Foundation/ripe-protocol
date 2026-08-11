import json
import re
from pathlib import Path

import pytest

from config.BluePrint import ROBINHOOD_REGISTRY_TOPOLOGY
from config.Ccip import (
    CCIP,
    CCIP_EVIDENCE_GATES,
    CCIP_OWNER_DISPOSITION_GATES,
    CCIP_POOL_HQ_IDS,
    CURRENT_RATE_LIMIT_ADMIN,
    NO_RATE_LIMIT,
    require_ccip_owner_disposition,
    require_ccip_wiring_gates,
)


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = (
    ROOT / "docs/chains/rh/evidence/ccip-live-snapshot-20260811.json"
)
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def _evidence():
    return json.loads(EVIDENCE_PATH.read_bytes())


def _vyper_constant(name):
    source = (ROOT / "contracts/modules/Addys.vy").read_text()
    match = re.search(rf"^{name}: constant\(uint256\) = ([0-9]+)$", source, re.MULTILINE)
    assert match, f"missing {name} in Addys.vy"
    return int(match.group(1))


def _python_constant(path, name):
    source = (ROOT / path).read_text()
    match = re.search(rf"^{name} = ([0-9]+)$", source, re.MULTILINE)
    assert match, f"missing {name} in {path}"
    return int(match.group(1))


def test_every_registry_id_copy_matches_confirmed_live_topology():
    assert CCIP_POOL_HQ_IDS == {"RIPE": 23, "GREEN": 24}
    assert _evidence()["ripe_hq_registry_ids"] == CCIP_POOL_HQ_IDS
    assert _vyper_constant("RIPE_CCIP_POOL_ID") == 23
    assert _vyper_constant("GREEN_CCIP_POOL_ID") == 24
    assert _python_constant("scripts/params/params_utils.py", "RIPE_CCIP_POOL_ID") == 23
    assert _python_constant("scripts/params/params_utils.py", "GREEN_CCIP_POOL_ID") == 24
    assert _python_constant("tests/constants.py", "RIPE_CCIP_POOL_HQ_ID") == 23
    assert _python_constant("tests/constants.py", "GREEN_CCIP_POOL_HQ_ID") == 24

    topology = {
        row.registry_id: (row.semantic_name, row.component_id)
        for row in ROBINHOOD_REGISTRY_TOPOLOGY
        if row.domain == "ripe_hq" and row.registry_id in (23, 24)
    }
    assert topology == {
        23: ("RIPE CCIP BurnMint pool", "CM-052"),
        24: ("GREEN CCIP BurnMint pool", "CM-051"),
    }


def test_live_snapshot_matches_config_and_current_manifests():
    evidence = _evidence()
    manifest_keys = {
        "RIPE": ("RipeToken", "RipeCcipBurnMintTokenPool"),
        "GREEN": ("GreenToken", "GreenCcipBurnMintTokenPool"),
    }

    for chain, chain_evidence in evidence["chains"].items():
        config = CCIP[chain]
        assert chain_evidence["chain_selector"] == config["CHAIN_SELECTOR"]
        assert chain_evidence["router"].lower() == config["ROUTER"].lower()
        assert chain_evidence["rmn_proxy"].lower() == config["RMN_PROXY"].lower()
        assert (
            chain_evidence["token_admin_registry"].lower()
            == config["TOKEN_ADMIN_REGISTRY"].lower()
        )
        assert config["REMOTE_CHAINS"] == [chain_evidence["remote_chain"]]
        assert (
            chain_evidence["remote_chain_selector"]
            == CCIP[chain_evidence["remote_chain"]]["CHAIN_SELECTOR"]
        )

        manifest_path = (
            ROOT / "migration_history" / chain / "v1" / "current-manifest.json"
        )
        contracts = json.loads(manifest_path.read_bytes())["contracts"]
        assert contracts["RipeHq"]["address"].lower() == chain_evidence["ripe_hq"].lower()

        for label, (token_key, pool_key) in manifest_keys.items():
            pool = chain_evidence["pools"][label]
            assert pool["registry_id"] == CCIP_POOL_HQ_IDS[label]
            assert contracts[token_key]["address"].lower() == pool["token"].lower()
            assert contracts[pool_key]["address"].lower() == pool["pool"].lower()


def test_live_pool_capabilities_wiring_and_unresolved_policy_are_explicit(monkeypatch):
    evidence = _evidence()
    assert set(CCIP_OWNER_DISPOSITION_GATES) == {
        "RATE_LIMIT_POLICY",
        "RATE_LIMIT_ADMIN",
    }
    assert all(value is None for value in CCIP_OWNER_DISPOSITION_GATES.values())
    assert CCIP_EVIDENCE_GATES == {
        "AUTOMATIC_EXECUTION_DESTINATION_GAS": None,
    }
    assert NO_RATE_LIMIT == (False, 0, 0)
    assert CURRENT_RATE_LIMIT_ADMIN == ZERO_ADDRESS
    with pytest.raises(RuntimeError, match="CCIP_OWNER_DISPOSITION_REQUIRED"):
        require_ccip_owner_disposition("RATE_LIMIT_POLICY", "RATE_LIMIT_ADMIN")
    with pytest.raises(RuntimeError, match="CCIP_OWNER_DISPOSITION_REQUIRED"):
        require_ccip_wiring_gates()
    for name in CCIP_OWNER_DISPOSITION_GATES:
        monkeypatch.setitem(CCIP_OWNER_DISPOSITION_GATES, name, "test-disposition")
    with pytest.raises(RuntimeError, match="CCIP_EVIDENCE_REQUIRED"):
        require_ccip_wiring_gates()

    for chain, chain_evidence in evidence["chains"].items():
        remote = evidence["chains"][chain_evidence["remote_chain"]]
        for label, pool in chain_evidence["pools"].items():
            assert pool["owner"].lower() == evidence["governance_safe"].lower()
            assert (
                pool["token_administrator"].lower()
                == evidence["governance_safe"].lower()
            )
            assert pool["pending_token_administrator"].lower() == ZERO_ADDRESS
            assert pool["type_and_version"] == "BurnMintTokenPool 1.5.1"
            assert pool["rate_limit_admin"].lower() == ZERO_ADDRESS
            for direction in ("outbound_rate_limit", "inbound_rate_limit"):
                assert pool[direction] == {
                    "is_enabled": False,
                    "capacity": 0,
                    "rate": 0,
                }
            assert pool["remote_token"].lower() == remote["pools"][label]["token"].lower()
            assert [value.lower() for value in pool["remote_pools"]] == [
                remote["pools"][label]["pool"].lower()
            ]

        assert chain_evidence["pools"]["RIPE"]["can_mint_ripe"]
        assert not chain_evidence["pools"]["RIPE"]["can_mint_green"]
        assert chain_evidence["pools"]["GREEN"]["can_mint_green"]
        assert not chain_evidence["pools"]["GREEN"]["can_mint_ripe"]


def test_live_snapshot_keeps_known_provenance_gaps_visible():
    unresolved = "\n".join(_evidence()["unresolved_evidence"])
    for required in (
        "setPool transaction hashes",
        "applyChainUpdates transaction hashes",
        "OffRamp automatic-execution gas",
        "live ccipSend signer or Safe transaction backend",
        "license legal conclusions",
    ):
        assert required in unresolved
