import json
from pathlib import Path
import sys

import pytest

from scripts.export_abis import export_abis
from scripts.probes.stock_token_transfer_probe import (
    ApprovalError,
    compile_probe_runtime_code_hash,
    load_approval,
    main,
    parse_approval,
)
from scripts.utils.migration_helpers import load_vyper_files


APPROVAL_PATH = Path("scripts/probes/aapl-robinhood-mainnet-fork.json")


def test_fork_approval_is_explicitly_non_broadcast():
    data = json.loads(APPROVAL_PATH.read_text())
    approved = parse_approval(data)
    assert data["scope"] == "fork-only"
    assert data["broadcast_allowed"] is False
    assert approved.chain_id == 4663
    assert approved.amount == 10**15


def test_approved_probe_bytecode_hash_matches_current_contract():
    approved = load_approval(APPROVAL_PATH)
    assert compile_probe_runtime_code_hash(approved) == approved.expected_probe_runtime_code_hash


def test_broadcast_flag_always_fails_closed(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "stock_token_transfer_probe.py",
            "--approval-file",
            str(APPROVAL_PATH),
            "--rpc-url",
            "https://rpc.mainnet.chain.robinhood.com",
            "--broadcast",
        ],
    )
    with pytest.raises(ApprovalError, match="broadcast is disabled"):
        main()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("chain_id", 1),
        ("sender", "0x0000000000000000000000000000000000000000"),
        ("amount", "0"),
        ("broadcast_allowed", True),
    ],
)
def test_approval_validation_fails_closed(field, value):
    data = json.loads(APPROVAL_PATH.read_text())
    data[field] = value
    if field == "chain_id":
        data.pop("chain_id")
    with pytest.raises(ApprovalError):
        parse_approval(data)


def test_production_migration_discovery_excludes_testing_contracts():
    files = load_vyper_files()
    assert "StockTokenTransferProbe" not in files
    assert all("contracts/testing/" not in path for path in files.values())


def test_abi_export_excludes_mock_and_testing_by_default(tmp_path):
    contracts = tmp_path / "contracts"
    output = tmp_path / "abis"
    (contracts / "production").mkdir(parents=True)
    (contracts / "mock").mkdir()
    (contracts / "testing").mkdir()

    source = "# @version 0.4.3\n@external\ndef answer() -> uint256:\n    return 42\n"
    (contracts / "production" / "Production.vy").write_text(source)
    (contracts / "mock" / "Mock.vy").write_text(source)
    (contracts / "testing" / "Probe.vy").write_text(source)

    export_abis(contracts, output)

    assert (output / "Production.json").exists()
    assert not (output / "Mock.json").exists()
    assert not (output / "Probe.json").exists()
