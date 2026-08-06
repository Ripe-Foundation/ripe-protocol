from dataclasses import replace
import json
from pathlib import Path
import sys

import pytest

from scripts.export_abis import export_abis
from scripts.probes import stock_token_transfer_probe as probe_runner
from scripts.probes.stock_token_transfer_probe import (
    ApprovalError,
    _format_token_amount,
    _validate_multiplier_state,
    cli,
    compile_probe_runtime_code_hash,
    load_approval,
    parse_approval,
)
from scripts.utils.migration_helpers import load_vyper_files


APPROVAL_PATH = Path("scripts/probes/aapl-robinhood-mainnet-fork.json")


def test_fork_approval_is_explicitly_non_broadcast():
    data = json.loads(APPROVAL_PATH.read_text())
    approved = parse_approval(data)
    assert data["schema_version"] == 2
    assert data["scope"] == "fork-only"
    assert data["broadcast_allowed"] is False
    assert approved.chain_id == 4663
    assert approved.amount == 10**15


def test_approved_probe_bytecode_hash_matches_current_contract():
    approved = load_approval(APPROVAL_PATH)
    assert compile_probe_runtime_code_hash(approved) == approved.expected_probe_runtime_code_hash


def test_broadcast_flag_always_fails_closed_without_traceback(monkeypatch, capsys):
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
    assert cli() == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        "error: broadcast is disabled; Phase D approval and implementation are required\n"
    )
    assert "Traceback" not in captured.err


@pytest.mark.parametrize(
    ("amount", "decimals", "formatted"),
    [
        (10**15, 18, "0.001"),
        (1234567890123456789, 18, "1.234567890123456789"),
        (42, 0, "42"),
        (10**18, 18, "1"),
    ],
)
def test_amount_formatting_is_exact(amount, decimals, formatted):
    assert _format_token_amount(amount, decimals) == formatted


def test_pending_multiplier_fails_closed():
    approved = load_approval(APPROVAL_PATH)
    block_timestamp = 1_000
    effective_at = block_timestamp + 1
    pending_approval = replace(
        approved,
        multiplier_effective_at=effective_at,
    )
    with pytest.raises(ApprovalError, match="pending UI multiplier"):
        _validate_multiplier_state(
            pending_approval,
            approved.ui_multiplier,
            approved.new_ui_multiplier,
            effective_at,
            block_timestamp,
        )


def test_preflight_rejects_rpc_chain_id_mismatch(monkeypatch):
    approved = load_approval(APPROVAL_PATH)

    def wrong_chain_rpc(_rpc_url, method, params):
        assert method == "eth_chainId"
        assert params == []
        return hex(approved.chain_id + 1)

    monkeypatch.setattr(probe_runner, "_rpc", wrong_chain_rpc)
    with pytest.raises(ApprovalError, match="chain_id mismatch"):
        probe_runner.preflight(approved, "https://rpc.invalid.example")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("sender", "0x0000000000000000000000000000000000000000"),
        ("amount", "0"),
        ("broadcast_allowed", True),
    ],
)
def test_approval_validation_fails_closed(field, value):
    data = json.loads(APPROVAL_PATH.read_text())
    data[field] = value
    with pytest.raises(ApprovalError):
        parse_approval(data)


def test_approval_validation_rejects_missing_chain_id():
    data = json.loads(APPROVAL_PATH.read_text())
    data.pop("chain_id")
    with pytest.raises(ApprovalError, match="missing approved input: chain_id"):
        parse_approval(data)


def test_approval_validation_rejects_obsolete_schema():
    data = json.loads(APPROVAL_PATH.read_text())
    data["schema_version"] = 1
    with pytest.raises(ApprovalError, match="unsupported approval schema"):
        parse_approval(data)


@pytest.mark.parametrize(
    "field",
    ["ui_multiplier", "new_ui_multiplier", "multiplier_effective_at"],
)
def test_schema_v2_requires_multiplier_fields(field):
    data = json.loads(APPROVAL_PATH.read_text())
    data["token"].pop(field)
    with pytest.raises(ApprovalError, match=f"missing approved input: {field}"):
        parse_approval(data)


def test_approval_validation_requires_sender_to_equal_owner():
    data = json.loads(APPROVAL_PATH.read_text())
    data["owner"] = "0x0000000000000000000000000000000000000002"
    with pytest.raises(ApprovalError, match="sender must equal probe owner"):
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
