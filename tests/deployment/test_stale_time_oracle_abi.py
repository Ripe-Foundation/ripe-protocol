from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.export_abis import _compile_abi


ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "contracts"
ABIS = ROOT / "scripts" / "abis"
STALE_TIME_SOURCES = (
    ("priceSources/ChainlinkPrices.vy", "ChainlinkPrices.json"),
    ("priceSources/PythPrices.vy", "PythPrices.json"),
    ("priceSources/RedStone.vy", "RedStone.json"),
    ("priceSources/StorkPrices.vy", "StorkPrices.json"),
    ("registries/PriceDesk.vy", "PriceDesk.json"),
)
ORACLE_ABIS = tuple(name for _, name in STALE_TIME_SOURCES[:4])


def _function_signatures(abi_name: str) -> set[tuple[str, tuple[str, ...]]]:
    entries = json.loads((ABIS / abi_name).read_text())
    return {
        (
            entry["name"],
            tuple(item["type"] for item in entry.get("inputs", ())),
        )
        for entry in entries
        if entry.get("type") == "function"
    }


@pytest.mark.parametrize(("source_name", "abi_name"), STALE_TIME_SOURCES)
def test_stale_time_contract_abi_is_byte_current(source_name, abi_name):
    source = CONTRACTS / source_name
    assert (ABIS / abi_name).read_bytes() == _compile_abi(source, CONTRACTS)


@pytest.mark.parametrize("abi_name", ORACLE_ABIS)
def test_oracle_abi_exposes_narrow_governance_stale_time_update(abi_name):
    signatures = _function_signatures(abi_name)
    assert ("updateStaleTime", ("address", "uint256")) in signatures
    assert ("isValidStaleTimeUpdate", ("address", "uint256")) in signatures


@pytest.mark.parametrize("abi_name", ORACLE_ABIS)
def test_oracle_read_abi_preserves_all_default_argument_overloads(abi_name):
    signatures = _function_signatures(abi_name)
    expected_inputs = {
        ("address",),
        ("address", "uint256"),
        ("address", "uint256", "address"),
    }
    assert {
        inputs for name, inputs in signatures if name == "getPrice"
    } == expected_inputs
    assert {
        inputs for name, inputs in signatures if name == "getPriceAndHasFeed"
    } == expected_inputs


def test_price_desk_read_abi_preserves_explicit_stale_time_overload():
    signatures = _function_signatures("PriceDesk.json")
    assert {
        inputs for name, inputs in signatures if name == "getPrice"
    } == {
        ("address",),
        ("address", "bool"),
        ("address", "bool", "uint256"),
    }
    assert {
        inputs
        for name, inputs in signatures
        if name == "qualifyCallerPriceSource"
    } == {
        ("address",),
        ("address", "uint256"),
    }
