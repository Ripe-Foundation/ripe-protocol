from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from typing import Mapping

import pytest
import requests

from scripts.utils.verify_etherscan import (
    _compiler_version,
    CHAIN_SPECS,
    PROVIDER_POLICIES,
    EtherscanVerifier,
    KeyPolicy,
    ProviderPolicy,
    VerificationStatus,
    VerifierConfigurationError,
    _api_key_for_policy,
    create_verifier,
)


class FakeResponse:
    def __init__(self, payload, *, status_error=None):
        self.payload = payload
        self.status_error = status_error

    def raise_for_status(self):
        if self.status_error:
            raise self.status_error

    def json(self):
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


class FakeSession:
    def __init__(self, *responses):
        self.responses = deque(responses)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        response = self.responses.popleft()
        if isinstance(response, Exception):
            raise response
        if isinstance(response, FakeResponse):
            return response
        return FakeResponse(response)


def manifest(**updates):
    value = {
        "address": "0x0000000000000000000000000000000000000001",
        "language": "vyper",
        "code_format": "vyper-json",
        "compiler_version": "vyper:0.4.3",
        "source_path": "contracts/Example.vy",
        "solc_json": {"sources": {"contracts/Example.vy": {"content": ""}}},
    }
    value.update(updates)
    return value


def verifier(*responses, timeout=7.5):
    session = FakeSession(*responses)
    adapter = EtherscanVerifier(
        chain="base-sepolia",
        api_key="test-key",
        timeout=timeout,
        session=session,
        sleep=lambda _seconds: None,
    )
    return adapter, session


def test_chain_identities_and_supported_provider_boundaries_are_exact():
    assert CHAIN_SPECS["robinhood-mainnet"].chain_id == 4663
    assert CHAIN_SPECS["robinhood-testnet"].chain_id == 46630
    assert CHAIN_SPECS["base-goerli"].chain_id == 84531
    assert CHAIN_SPECS["base-sepolia"].chain_id == 84532
    assert CHAIN_SPECS["robinhood-mainnet"].provider is None
    assert CHAIN_SPECS["robinhood-testnet"].provider is None
    assert CHAIN_SPECS["base-goerli"].provider is None
    assert CHAIN_SPECS["base-sepolia"].provider == "etherscan"


def test_unsupported_provider_and_keyless_policy_fail_before_http():
    with pytest.raises(
        VerifierConfigurationError,
        match="no supported official verifier provider",
    ):
        create_verifier(chain="robinhood-mainnet", api_key="unused")
    with pytest.raises(
        VerifierConfigurationError, match="unsupported verifier provider"
    ):
        create_verifier(
            chain="base-sepolia",
            api_key="unused",
            provider="blockscout",
        )
    with pytest.raises(VerifierConfigurationError, match="requires an API key"):
        create_verifier(chain="base-sepolia", api_key=None)

    keyless = ProviderPolicy(
        name="mock-keyless",
        key_policy=KeyPolicy.KEYLESS,
        api_url="https://invalid.example",
    )
    assert _api_key_for_policy(keyless, None) == ""
    with pytest.raises(VerifierConfigurationError, match="must not receive"):
        _api_key_for_policy(keyless, "unexpected-key")


@pytest.mark.parametrize(
    ("payload", "status"),
    [
        ({"status": "1", "message": "OK", "result": "[]"}, VerificationStatus.SUCCESS),
        (
            {
                "status": "0",
                "message": "NOTOK",
                "result": "Contract source code not verified",
            },
            VerificationStatus.UNVERIFIED,
        ),
        (
            {"status": "0", "message": "NOTOK", "result": "Max rate limit reached"},
            VerificationStatus.RATE_LIMIT,
        ),
        (
            {"status": "0", "message": "NOTOK", "result": "unknown failure"},
            VerificationStatus.PROVIDER_ERROR,
        ),
    ],
)
def test_lookup_classifies_provider_responses(payload, status):
    adapter, session = verifier(payload)
    result = adapter.lookup("0x1")
    assert result.status is status
    assert session.calls[0][2]["timeout"] == 7.5
    assert session.calls[0][1] == PROVIDER_POLICIES["etherscan"].api_url


def test_success_status_wins_over_error_like_abi_text():
    adapter, _ = verifier(
        {
            "status": "1",
            "message": "OK",
            "result": '[{"name":"not verified rate limit"}]',
        }
    )
    assert adapter.lookup("0x1").status is VerificationStatus.SUCCESS


def test_lookup_classifies_timeout_and_provider_error():
    timeout_adapter, _ = verifier(requests.Timeout("slow"))
    assert timeout_adapter.lookup("0x1").status is VerificationStatus.TIMEOUT

    error_adapter, _ = verifier(requests.ConnectionError("offline"))
    assert error_adapter.lookup("0x1").status is VerificationStatus.PROVIDER_ERROR

    http_adapter, _ = verifier(
        FakeResponse({}, status_error=requests.HTTPError("bad status"))
    )
    assert http_adapter.lookup("0x1").status is VerificationStatus.PROVIDER_ERROR


def test_submission_pending_and_success_paths_are_deterministic():
    pending_adapter, pending_session = verifier(
        {"status": "0", "result": "Contract source code not verified"},
        {"status": "1", "result": "GUID-1"},
    )
    pending = pending_adapter.verify_manifest("Example", manifest(), wait=False)
    assert pending.status is VerificationStatus.PENDING
    assert pending.guid == "GUID-1"
    submission = pending_session.calls[1][2]["data"]
    assert submission["compilerversion"] == "vyper:0.4.3"
    assert "optimizationUsed" not in submission
    assert "runs" not in submission
    assert "evmversion" not in submission

    success_adapter, _ = verifier(
        {"status": "0", "result": "Contract source code not verified"},
        {"status": "1", "result": "GUID-2"},
        {"status": "0", "result": "Pending in queue"},
        {"status": "1", "result": "Pass - Verified"},
    )
    success = success_adapter.verify_manifest(
        "Example", manifest(), max_polls=2, poll_interval=0
    )
    assert success.status is VerificationStatus.SUCCESS
    assert success.guid == "GUID-2"


def test_polling_budget_exhaustion_is_timeout():
    adapter, _ = verifier(
        {"status": "0", "result": "Contract source code not verified"},
        {"status": "1", "result": "GUID"},
        {"status": "0", "result": "Pending in queue"},
        {"status": "0", "result": "Pending in queue"},
    )
    result = adapter.verify_manifest("Example", manifest(), max_polls=2)
    assert result.status is VerificationStatus.TIMEOUT


@pytest.mark.parametrize(
    ("updates", "message"),
    [
        ({"language": "solidity"}, "unsupported verification language"),
        (
            {"code_format": "solidity-standard-json-input"},
            "unsupported verification format",
        ),
        ({"compiler_version": None}, "compiler_version must be an explicit"),
    ],
)
def test_unsupported_language_or_format_fails_before_http(updates, message):
    adapter, session = verifier()
    with pytest.raises(VerifierConfigurationError, match=message):
        adapter.verify_manifest("Example", manifest(**updates))
    assert session.calls == []


# --- the committed manifests must actually verify --------------------------
#
# Every test above builds a synthetic manifest carrying a record-level
# "compiler_version". No manifest in this repository has one:
# deployed_contracts_manifest emits address/abi/solc_json/args/file, here and on
# master. So the adapter rejected every real manifest while its suite passed.
# These tests use the committed manifests instead of a fixture.


def _committed_manifest_records():
    root = Path(__file__).resolve().parents[2] / "migration_history"
    for path in sorted(root.glob("*/*/current-manifest.json")):
        contracts = json.loads(path.read_text()).get("contracts", {})
        for name, record in sorted(contracts.items()):
            if isinstance(record.get("solc_json"), Mapping):
                yield f"{path.parent.parent.name}/{path.parent.name}", name, record


def test_no_committed_manifest_carries_a_record_level_compiler_version():
    # Pins the premise: if this ever becomes false, the fallback is dead code.
    records = list(_committed_manifest_records())
    assert records, "expected committed manifests with solc_json"
    assert all("compiler_version" not in rec for _, _, rec in records)


def test_committed_manifests_resolve_a_compiler_version():
    for where, name, record in _committed_manifest_records():
        resolved = _compiler_version(record, record["solc_json"])
        assert resolved == "vyper:0.4.3", f"{where}:{name} -> {resolved}"


def test_a_committed_manifest_submits_successfully():
    where, name, record = next(_committed_manifest_records())
    session = FakeSession(
        FakeResponse({"status": "0", "message": "NOTOK", "result": "not verified"}),
        FakeResponse({"status": "1", "message": "OK", "result": "GUID"}),
        FakeResponse({"status": "1", "message": "OK", "result": "Pass - Verified"}),
    )
    verifier = create_verifier(
        chain="base-mainnet",
        api_key="probe",
        session=session,
        sleep=lambda *_: None,
    )

    result = verifier.verify_manifest(name, record)

    assert result.ok, f"{where}:{name} -> {result}"
    submission = next(
        kwargs for _method, _url, kwargs in session.calls
        if (kwargs.get("data") or {}).get("action") == "verifysourcecode"
    )
    assert submission["data"]["compilerversion"] == "vyper:0.4.3"
    assert submission["data"]["codeformat"] == "vyper-json"
