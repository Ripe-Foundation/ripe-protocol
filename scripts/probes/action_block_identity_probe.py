#!/usr/bin/env python3
"""Fail-closed Robinhood testnet runner for ActionBlockIdentityProbe.

The default dry run is local-only and never reads an RPC URL or signing key.
RPC preflight is read-only. Live execution is testnet-only and requires an
explicit approval file, an additional CLI confirmation flag, and secrets
supplied only through named environment variables.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Callable

import boa
import requests
import rlp
import vyper
from boa.interpret import set_cache_dir
from eth_abi import decode, encode
from eth_account import Account
from eth_utils import keccak, to_checksum_address
from vyper.compiler.output import build_abi_output


REPO_ROOT = Path(__file__).resolve().parents[2]
PROBE_CONTRACT = REPO_ROOT / "contracts/testing/ActionBlockIdentityProbe.vy"
BOA_CACHE_ROOT = Path(tempfile.gettempdir()) / "ripe-action-block-probe-cache"

ROBINHOOD_TESTNET_CHAIN_ID = 46630
ARB_SYS = to_checksum_address("0x0000000000000000000000000000000000000064")
ARB_BLOCK_SELECTOR = "0x" + keccak(text="arbBlockNumber()")[:4].hex()
ARB_OS_VERSION_SELECTOR = "0x" + keccak(text="arbOSVersion()")[:4].hex()
OBSERVE_SELECTOR = keccak(text="observe(uint256)")[:4]
OBSERVED_EVENT_TOPIC = (
    "0x"
    + keccak(
        text="ActionBlockObserved(uint256,address,uint256,uint256,uint256)"
    ).hex()
)

NITRO_COMMIT = "3599acae1ad2fab4059fc46453c9cd3294126641"
ARB_SYS_INTERFACE_COMMIT = "7e88c8cc53c2e96201a23c638f1536557b9cb68b"
ROBINHOOD_NODE_IMAGE = "offchainlabs/nitro-node:v3.11.2-3599aca"
ROBINHOOD_PUBLISHED_ARB_OS_PROFILE = 61
SOURCE_PIN_DATE = "2026-07-24"
# Pinned Nitro precompiles/ArbSys.go returns 55 + c.State.ArbOSVersion().
# The pinned ArbSys.sol interface independently documents the same offset.
PINNED_NITRO_ARB_SYS_VERSION_OFFSET = 55
EXPECTED_ARB_SYS_ARB_OS_VERSION_RETURN = (
    ROBINHOOD_PUBLISHED_ARB_OS_PROFILE + PINNED_NITRO_ARB_SYS_VERSION_OFFSET
)
ARB_SYS_VERSION_RETURN_DERIVATION = (
    f"{ROBINHOOD_PUBLISHED_ARB_OS_PROFILE} + "
    f"{PINNED_NITRO_ARB_SYS_VERSION_OFFSET} = "
    f"{EXPECTED_ARB_SYS_ARB_OS_VERSION_RETURN}"
)

EXPECTED_PROBE_SOURCE_SHA256 = (
    "0x95716e4e2b383f2a07826be94d9ee402d263eec522bb4f77efd72a5e5f6eafe5"
)
EXPECTED_PROBE_ABI_SHA256 = (
    "0x2c237ba7e43aa009c69eabe950c733c79415b7eab37e874e065494273a45b359"
)
EXPECTED_PROBE_COMPILER_INPUTS_SHA256 = (
    "0xf251237b97029e29122f5578c38817e518abcc3062c6d32019de028bdef79a65"
)
EXPECTED_PROBE_CREATION_BYTECODE_KECCAK256 = (
    "0x835fdafe8f7e61253237837ae17cf7985a3cef2eb7e1c274ba2f98f8ea044333"
)
EXPECTED_PROBE_RUNTIME_BYTECODE_KECCAK256 = (
    "0xd4114b7780177700bfac10a60e77a4ca49a4ad10a92f01685ea72bbd1c54ab56"
)

REQUIRED_TOPOLOGY_CASES = (
    "each emitted ArbSys value equals its receipt blockNumber",
    "two separate transactions included in one child block share one ArbSys identity",
    "transactions included in successive child blocks have distinct ArbSys identities",
    "successive child blocks share one native ancestor block.number",
    "bounded repeated and advancing values without a protocol-maximum claim",
)

APPROVAL_HASH_RE = re.compile(r"^0x[0-9a-f]{64}$")
RUNTIME_HASH_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")
SELECTOR_RE = re.compile(r"^0x[0-9a-f]{8}$")
ENV_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
MAX_OBSERVATION_TRANSACTIONS = 16
MIN_OBSERVATION_TRANSACTIONS = 4

set_cache_dir(BOA_CACHE_ROOT / "compiler")


class ApprovalError(RuntimeError):
    """An approval input or observed preflight invariant did not match."""


@dataclass(frozen=True)
class ProbeArtifacts:
    compiler_version: str
    compiler_settings: str
    source_sha256: str
    abi_sha256: str
    compiler_inputs_sha256: str
    creation_bytecode_keccak256: str
    runtime_bytecode_keccak256: str
    creation_bytecode_length: int
    runtime_bytecode_length: int
    creation_bytecode: bytes

    def sanitized(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("creation_bytecode")
        return data


@dataclass(frozen=True)
class ApprovedRun:
    approval_reference: str
    owner_approval_date: str
    owner_approval_reference: str
    security_approval_date: str
    security_approval_reference: str
    deployment_approval_date: str
    deployment_approval_reference: str
    chain_id: int
    rpc_label: str
    rpc_url_env: str
    rpc_url_sha256: str
    robinhood_published_arb_os_profile: int
    expected_arb_sys_arb_os_version_return: int
    signer_address: str
    private_key_env: str
    expected_nonce: int
    expected_probe_address: str
    expected_source_sha256: str
    expected_abi_sha256: str
    expected_compiler_inputs_sha256: str
    expected_creation_bytecode_hash: str
    expected_runtime_bytecode_hash: str
    deployment_gas_limit: int
    observation_gas_limit: int
    max_fee_per_gas_wei: int
    max_priority_fee_per_gas_wei: int
    max_total_fee_wei: int
    max_observation_transactions: int
    receipt_timeout_seconds: int

    @property
    def max_transaction_count(self) -> int:
        return 1 + self.max_observation_transactions

    @property
    def worst_case_total_fee_wei(self) -> int:
        gas = self.deployment_gas_limit + (
            self.observation_gas_limit * self.max_observation_transactions
        )
        return gas * self.max_fee_per_gas_wei


def _required(data: dict[str, Any], key: str) -> Any:
    if key not in data:
        raise ApprovalError(f"missing approved input: {key}")
    return data[key]


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ApprovalError(f"approved field must be an object: {field}")
    return value


def _nonempty_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ApprovalError(f"approved text must be nonempty: {field}")
    return value.strip()


def _iso_date(value: Any, field: str) -> str:
    text = _nonempty_text(value, field)
    try:
        parsed = date.fromisoformat(text)
    except ValueError as exc:
        raise ApprovalError(f"approved date must use YYYY-MM-DD: {field}") from exc
    if parsed.isoformat() != text:
        raise ApprovalError(f"approved date must use YYYY-MM-DD: {field}")
    return text


def _positive_int(value: Any, field: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ApprovalError(f"invalid approved integer: {field}") from exc
    if parsed <= 0:
        raise ApprovalError(f"approved integer must be positive: {field}")
    return parsed


def _nonnegative_int(value: Any, field: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ApprovalError(f"invalid approved integer: {field}") from exc
    if parsed < 0:
        raise ApprovalError(f"approved integer must be nonnegative: {field}")
    return parsed


def _address(value: Any, field: str) -> str:
    try:
        address = to_checksum_address(value)
    except Exception as exc:
        raise ApprovalError(f"invalid approved address: {field}") from exc
    if int(address, 16) == 0:
        raise ApprovalError(f"zero approved address: {field}")
    return address


def _approval_hash(value: Any, field: str) -> str:
    if not isinstance(value, str) or not APPROVAL_HASH_RE.fullmatch(value):
        raise ApprovalError(
            f"invalid lowercase 0x-prefixed approved hash: {field}"
        )
    return value


def _runtime_hash(value: Any, field: str) -> str:
    if not isinstance(value, str) or not RUNTIME_HASH_RE.fullmatch(value):
        raise ApprovalError(f"invalid RPC/runtime hash: {field}")
    return value.lower()


def _selector(value: Any, field: str) -> str:
    if not isinstance(value, str) or not SELECTOR_RE.fullmatch(value):
        raise ApprovalError(f"invalid lowercase approved selector: {field}")
    return value


def _env_name(value: Any, field: str) -> str:
    if not isinstance(value, str) or not ENV_NAME_RE.fullmatch(value):
        raise ApprovalError(f"invalid environment-variable name: {field}")
    return value


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return str(value)


def _sha256_bytes(value: bytes) -> str:
    return "0x" + hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _keccak_bytes(value: bytes) -> str:
    return "0x" + keccak(value).hex()


def compile_probe_artifacts() -> ProbeArtifacts:
    deployer = boa.load_partial(str(PROBE_CONTRACT))
    compiler_data = deployer.compiler_data
    source = compiler_data.source_code.encode("utf-8")
    abi = build_abi_output(compiler_data)
    settings = _canonical_json(
        {
            key: _jsonable(value)
            for key, value in vars(compiler_data.settings).items()
        }
    )
    compiler_version = (
        f"vyper=={vyper.__version__}"
        f"+commit.{getattr(vyper, '__commit__', 'unknown')}"
    )
    abi_json = _canonical_json(abi).encode("utf-8")
    creation_bytecode = bytes(compiler_data.bytecode)
    runtime_bytecode = bytes(compiler_data.bytecode_runtime)
    compiler_inputs = _canonical_json(
        {
            "source_sha256": _sha256_bytes(source),
            "compiler_version": compiler_version,
            "compiler_settings": settings,
            "abi_sha256": _sha256_bytes(abi_json),
        }
    ).encode("utf-8")
    return ProbeArtifacts(
        compiler_version=compiler_version,
        compiler_settings=settings,
        source_sha256=_sha256_bytes(source),
        abi_sha256=_sha256_bytes(abi_json),
        compiler_inputs_sha256=_sha256_bytes(compiler_inputs),
        creation_bytecode_keccak256=_keccak_bytes(creation_bytecode),
        runtime_bytecode_keccak256=_keccak_bytes(runtime_bytecode),
        creation_bytecode_length=len(creation_bytecode),
        runtime_bytecode_length=len(runtime_bytecode),
        creation_bytecode=creation_bytecode,
    )


def _validate_compiled_artifacts(artifacts: ProbeArtifacts) -> None:
    expected = {
        "source_sha256": EXPECTED_PROBE_SOURCE_SHA256,
        "abi_sha256": EXPECTED_PROBE_ABI_SHA256,
        "compiler_inputs_sha256": EXPECTED_PROBE_COMPILER_INPUTS_SHA256,
        "creation_bytecode_keccak256": (
            EXPECTED_PROBE_CREATION_BYTECODE_KECCAK256
        ),
        "runtime_bytecode_keccak256": EXPECTED_PROBE_RUNTIME_BYTECODE_KECCAK256,
    }
    for field, expected_value in expected.items():
        if getattr(artifacts, field) != expected_value:
            raise ApprovalError(
                f"compiled probe {field} disagrees with reviewed hardcoded identity"
            )


def _predict_create_address(sender: str, nonce: int) -> str:
    encoded = rlp.encode([bytes.fromhex(sender[2:]), nonce])
    return to_checksum_address(keccak(encoded)[-20:])


def parse_approval(data: dict[str, Any]) -> ApprovedRun:
    if _required(data, "schema_version") != 2:
        raise ApprovalError("unsupported approval schema")
    if _required(data, "scope") != "robinhood-testnet-action-block-proof":
        raise ApprovalError("approval scope mismatch")
    if _required(data, "network") != "Robinhood Chain testnet":
        raise ApprovalError("approved network must be Robinhood Chain testnet")
    if _required(data, "live_testnet_approved") is not True:
        raise ApprovalError("live Robinhood testnet execution is not approved")

    try:
        chain_id = int(_required(data, "chain_id"))
    except (TypeError, ValueError) as exc:
        raise ApprovalError("approved chain ID must be an integer") from exc
    if chain_id != ROBINHOOD_TESTNET_CHAIN_ID:
        raise ApprovalError("approved chain ID must be 46630")

    approval_reference = _nonempty_text(
        _required(data, "owner_approval_reference"),
        "owner_approval_reference",
    )

    provenance = _mapping(
        _required(data, "approval_provenance"),
        "approval_provenance",
    )
    approval_records: dict[str, tuple[str, str]] = {}
    for role in ("owner", "independent_security", "deployment"):
        record = _mapping(
            _required(provenance, role),
            f"approval_provenance.{role}",
        )
        if _required(record, "approved") is not True:
            raise ApprovalError(f"{role} approval is not explicitly approved")
        approval_records[role] = (
            _iso_date(
                _required(record, "decision_date"),
                f"approval_provenance.{role}.decision_date",
            ),
            _nonempty_text(
                _required(record, "reference"),
                f"approval_provenance.{role}.reference",
            ),
        )
    if approval_reference != approval_records["owner"][1]:
        raise ApprovalError(
            "owner approval reference disagrees with owner provenance reference"
        )

    rpc = _mapping(_required(data, "rpc"), "rpc")
    signer = _mapping(_required(data, "signer"), "signer")
    probe = _mapping(_required(data, "probe"), "probe")
    fees = _mapping(_required(data, "fees"), "fees")
    execution = _mapping(_required(data, "execution"), "execution")
    source_pins = _mapping(_required(data, "source_pins"), "source_pins")

    if _required(rpc, "approved") is not True:
        raise ApprovalError("RPC endpoint is not explicitly approved")
    if _required(signer, "approved") is not True:
        raise ApprovalError("testnet signer is not explicitly approved")
    if _required(signer, "funding_approved") is not True:
        raise ApprovalError("testnet funding is not explicitly approved")
    if _required(fees, "owner_approved") is not True:
        raise ApprovalError("total fee cap is not explicitly owner-approved")

    expected_source_sha256 = _approval_hash(
        _required(probe, "source_sha256"),
        "probe.source_sha256",
    )
    expected_abi_sha256 = _approval_hash(
        _required(probe, "abi_sha256"),
        "probe.abi_sha256",
    )
    expected_compiler_inputs_sha256 = _approval_hash(
        _required(probe, "compiler_inputs_sha256"),
        "probe.compiler_inputs_sha256",
    )
    expected_creation_bytecode_hash = _approval_hash(
        _required(probe, "creation_bytecode_keccak256"),
        "probe.creation_bytecode_keccak256",
    )
    expected_runtime_bytecode_hash = _approval_hash(
        _required(probe, "runtime_bytecode_keccak256"),
        "probe.runtime_bytecode_keccak256",
    )
    expected_artifact_facts = {
        "probe.source_sha256": (
            expected_source_sha256,
            EXPECTED_PROBE_SOURCE_SHA256,
        ),
        "probe.abi_sha256": (
            expected_abi_sha256,
            EXPECTED_PROBE_ABI_SHA256,
        ),
        "probe.compiler_inputs_sha256": (
            expected_compiler_inputs_sha256,
            EXPECTED_PROBE_COMPILER_INPUTS_SHA256,
        ),
        "probe.creation_bytecode_keccak256": (
            expected_creation_bytecode_hash,
            EXPECTED_PROBE_CREATION_BYTECODE_KECCAK256,
        ),
        "probe.runtime_bytecode_keccak256": (
            expected_runtime_bytecode_hash,
            EXPECTED_PROBE_RUNTIME_BYTECODE_KECCAK256,
        ),
    }
    for field, (observed, expected) in expected_artifact_facts.items():
        if observed != expected:
            raise ApprovalError(f"approved packet fact mismatch: {field}")

    approved_arb_sys = _address(
        _required(probe, "arb_sys_address"),
        "probe.arb_sys_address",
    )
    if approved_arb_sys != ARB_SYS:
        raise ApprovalError("approved packet fact mismatch: probe.arb_sys_address")
    if (
        _selector(
            _required(probe, "arb_block_number_selector"),
            "probe.arb_block_number_selector",
        )
        != ARB_BLOCK_SELECTOR
    ):
        raise ApprovalError(
            "approved packet fact mismatch: probe.arb_block_number_selector"
        )
    if (
        _selector(
            _required(probe, "arb_os_version_selector"),
            "probe.arb_os_version_selector",
        )
        != ARB_OS_VERSION_SELECTOR
    ):
        raise ApprovalError(
            "approved packet fact mismatch: probe.arb_os_version_selector"
        )

    source_pin_facts = {
        "source_pins.evidence_date": (
            _required(source_pins, "evidence_date"),
            SOURCE_PIN_DATE,
        ),
        "source_pins.robinhood_node_image": (
            _required(source_pins, "robinhood_node_image"),
            ROBINHOOD_NODE_IMAGE,
        ),
        "source_pins.nitro_commit": (
            _required(source_pins, "nitro_commit"),
            NITRO_COMMIT,
        ),
        "source_pins.arb_sys_interface_commit": (
            _required(source_pins, "arb_sys_interface_commit"),
            ARB_SYS_INTERFACE_COMMIT,
        ),
        "source_pins.pinned_nitro_arb_sys_version_offset": (
            _required(source_pins, "pinned_nitro_arb_sys_version_offset"),
            PINNED_NITRO_ARB_SYS_VERSION_OFFSET,
        ),
        "source_pins.version_return_derivation": (
            _required(source_pins, "version_return_derivation"),
            ARB_SYS_VERSION_RETURN_DERIVATION,
        ),
    }
    for field, (observed, expected) in source_pin_facts.items():
        if observed != expected:
            raise ApprovalError(f"approved packet fact mismatch: {field}")

    topology_cases = _required(execution, "topology_cases")
    if topology_cases != list(REQUIRED_TOPOLOGY_CASES):
        raise ApprovalError(
            "approved packet fact mismatch: execution.topology_cases"
        )
    if _required(execution, "stop_on_inconclusive_bound") is not True:
        raise ApprovalError(
            "approved packet fact mismatch: execution.stop_on_inconclusive_bound"
        )
    native_value = _required(execution, "native_value_wei")
    if isinstance(native_value, bool) or native_value != 0:
        raise ApprovalError(
            "approved packet fact mismatch: execution.native_value_wei"
        )
    if _required(execution, "token_transfer") is not False:
        raise ApprovalError(
            "approved packet fact mismatch: execution.token_transfer"
        )

    max_observations = _positive_int(
        _required(execution, "max_observation_transactions"),
        "execution.max_observation_transactions",
    )
    if not MIN_OBSERVATION_TRANSACTIONS <= max_observations <= MAX_OBSERVATION_TRANSACTIONS:
        raise ApprovalError(
            "approved observation count must be between "
            f"{MIN_OBSERVATION_TRANSACTIONS} and {MAX_OBSERVATION_TRANSACTIONS}"
        )

    approved = ApprovedRun(
        approval_reference=approval_reference,
        owner_approval_date=approval_records["owner"][0],
        owner_approval_reference=approval_records["owner"][1],
        security_approval_date=approval_records["independent_security"][0],
        security_approval_reference=approval_records["independent_security"][1],
        deployment_approval_date=approval_records["deployment"][0],
        deployment_approval_reference=approval_records["deployment"][1],
        chain_id=chain_id,
        rpc_label=str(_required(rpc, "label")).strip(),
        rpc_url_env=_env_name(
            _required(rpc, "url_environment_variable"),
            "rpc.url_environment_variable",
        ),
        rpc_url_sha256=_approval_hash(
            _required(rpc, "url_sha256"),
            "rpc.url_sha256",
        ),
        robinhood_published_arb_os_profile=_positive_int(
            _required(data, "robinhood_published_arb_os_profile"),
            "robinhood_published_arb_os_profile",
        ),
        expected_arb_sys_arb_os_version_return=_positive_int(
            _required(data, "expected_arb_sys_arb_os_version_return"),
            "expected_arb_sys_arb_os_version_return",
        ),
        signer_address=_address(
            _required(signer, "address"),
            "signer.address",
        ),
        private_key_env=_env_name(
            _required(signer, "private_key_environment_variable"),
            "signer.private_key_environment_variable",
        ),
        expected_nonce=_nonnegative_int(
            _required(signer, "expected_nonce"),
            "signer.expected_nonce",
        ),
        expected_probe_address=_address(
            _required(probe, "expected_address"),
            "probe.expected_address",
        ),
        expected_source_sha256=expected_source_sha256,
        expected_abi_sha256=expected_abi_sha256,
        expected_compiler_inputs_sha256=expected_compiler_inputs_sha256,
        expected_creation_bytecode_hash=expected_creation_bytecode_hash,
        expected_runtime_bytecode_hash=expected_runtime_bytecode_hash,
        deployment_gas_limit=_positive_int(
            _required(fees, "deployment_gas_limit"),
            "fees.deployment_gas_limit",
        ),
        observation_gas_limit=_positive_int(
            _required(fees, "observation_gas_limit"),
            "fees.observation_gas_limit",
        ),
        max_fee_per_gas_wei=_positive_int(
            _required(fees, "max_fee_per_gas_wei"),
            "fees.max_fee_per_gas_wei",
        ),
        max_priority_fee_per_gas_wei=_nonnegative_int(
            _required(fees, "max_priority_fee_per_gas_wei"),
            "fees.max_priority_fee_per_gas_wei",
        ),
        max_total_fee_wei=_positive_int(
            _required(fees, "max_total_fee_wei"),
            "fees.max_total_fee_wei",
        ),
        max_observation_transactions=max_observations,
        receipt_timeout_seconds=_positive_int(
            _required(execution, "receipt_timeout_seconds"),
            "execution.receipt_timeout_seconds",
        ),
    )

    if not approved.rpc_label:
        raise ApprovalError("approved RPC label must be nonempty")
    if (
        approved.robinhood_published_arb_os_profile
        != ROBINHOOD_PUBLISHED_ARB_OS_PROFILE
    ):
        raise ApprovalError(
            "approved published Robinhood ArbOS profile must equal pinned "
            f"profile {ROBINHOOD_PUBLISHED_ARB_OS_PROFILE}"
        )
    derived_arb_sys_return = (
        approved.robinhood_published_arb_os_profile
        + PINNED_NITRO_ARB_SYS_VERSION_OFFSET
    )
    if (
        approved.expected_arb_sys_arb_os_version_return
        != derived_arb_sys_return
    ):
        raise ApprovalError(
            "approved expected ArbSys arbOSVersion() return must equal the "
            "published Robinhood ArbOS profile plus the pinned Nitro offset "
            f"{PINNED_NITRO_ARB_SYS_VERSION_OFFSET}"
        )
    if approved.max_priority_fee_per_gas_wei > approved.max_fee_per_gas_wei:
        raise ApprovalError("priority fee cap exceeds max fee per gas")
    if approved.receipt_timeout_seconds > 300:
        raise ApprovalError("receipt timeout may not exceed 300 seconds")
    if approved.worst_case_total_fee_wei > approved.max_total_fee_wei:
        raise ApprovalError("approved gas limits exceed total fee cap")

    predicted = _predict_create_address(
        approved.signer_address,
        approved.expected_nonce,
    )
    if predicted != approved.expected_probe_address:
        raise ApprovalError(
            "approved nonce and signer do not predict the approved probe address"
        )
    return approved


def load_approval(path: Path) -> ApprovedRun:
    with path.open() as approval_file:
        return parse_approval(json.load(approval_file))


def _rpc(rpc_url: str, method: str, params: list[Any]) -> Any:
    try:
        response = requests.post(
            rpc_url,
            json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
            timeout=30,
            allow_redirects=False,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise ApprovalError(f"RPC request failed for {method}") from exc
    if "error" in payload:
        raise ApprovalError(f"RPC returned an error for {method}")
    if "result" not in payload:
        raise ApprovalError(f"RPC omitted a result for {method}")
    return payload["result"]


def _rpc_url_from_environment(approved: ApprovedRun) -> str:
    rpc_url = os.environ.get(approved.rpc_url_env)
    if not rpc_url:
        raise ApprovalError(
            f"approved RPC environment variable is unset: {approved.rpc_url_env}"
        )
    if _sha256_text(rpc_url) != approved.rpc_url_sha256:
        raise ApprovalError("RPC endpoint fingerprint mismatch")
    return rpc_url


def _signing_secret_from_environment(approved: ApprovedRun) -> str:
    private_key = os.environ.get(approved.private_key_env)
    if not private_key:
        raise ApprovalError(
            "approved private-key environment variable is unset: "
            f"{approved.private_key_env}"
        )
    return private_key


def _decode_uint256_response(raw: Any, field: str) -> int:
    if not isinstance(raw, str) or not raw.startswith("0x"):
        raise ApprovalError(f"{field} returned non-hex data")
    response = bytes.fromhex(raw[2:])
    if len(response) != 32:
        raise ApprovalError(f"{field} returned an incompatible ABI length")
    return decode(["uint256"], response)[0]


def _hex_int(value: Any, field: str) -> int:
    if not isinstance(value, str) or not value.startswith("0x"):
        raise ApprovalError(f"{field} is not a hex quantity")
    return int(value, 16)


def local_dry_run() -> dict[str, Any]:
    artifacts = compile_probe_artifacts()
    _validate_compiled_artifacts(artifacts)
    return {
        "mode": "local-dry-run",
        "broadcast_enabled": False,
        "rpc_contacted": False,
        "rpc_endpoint_read": False,
        "signing_secret_read": False,
        "required_chain_id": ROBINHOOD_TESTNET_CHAIN_ID,
        "arb_sys": {
            "address": ARB_SYS,
            "arb_block_number_selector": ARB_BLOCK_SELECTOR,
            "arb_os_version_selector": ARB_OS_VERSION_SELECTOR,
            "robinhood_published_arb_os_profile": (
                ROBINHOOD_PUBLISHED_ARB_OS_PROFILE
            ),
            "pinned_nitro_arb_sys_version_offset": (
                PINNED_NITRO_ARB_SYS_VERSION_OFFSET
            ),
            "required_approved_arb_sys_arb_os_version_return": (
                EXPECTED_ARB_SYS_ARB_OS_VERSION_RETURN
            ),
            "version_return_derivation": ARB_SYS_VERSION_RETURN_DERIVATION,
        },
        "artifacts": artifacts.sanitized(),
        "transaction_constraints": {
            "native_value_wei": 0,
            "token_transfer": False,
            "minimum_observation_transactions": MIN_OBSERVATION_TRANSACTIONS,
            "maximum_supported_observation_transactions": MAX_OBSERVATION_TRANSACTIONS,
            "deployment_transactions": 1,
        },
        "source_pins": {
            "nitro_commit": NITRO_COMMIT,
            "arb_sys_interface_commit": ARB_SYS_INTERFACE_COMMIT,
            "robinhood_node_image": ROBINHOOD_NODE_IMAGE,
            "robinhood_published_arb_os_profile": (
                ROBINHOOD_PUBLISHED_ARB_OS_PROFILE
            ),
            "pinned_nitro_arb_sys_version_offset": (
                PINNED_NITRO_ARB_SYS_VERSION_OFFSET
            ),
            "expected_arb_sys_arb_os_version_return": (
                EXPECTED_ARB_SYS_ARB_OS_VERSION_RETURN
            ),
        },
        "pending_approvals": [
            "exact RPC endpoint and its SHA-256 fingerprint",
            "approved testnet signer address and private-key environment-variable name",
            "explicit approval to use that signer's existing testnet gas funds",
            "current pending nonce and predicted probe address",
            "owner-approved max fee per gas, priority fee, gas limits, and total fee cap",
            "owner-approved bounded observation-transaction count",
            "exact creation/runtime bytecode hashes copied into the approval file",
            "explicitly approved published Robinhood ArbOS profile "
            f"{ROBINHOOD_PUBLISHED_ARB_OS_PROFILE} and derived ArbSys "
            "arbOSVersion() return "
            f"{EXPECTED_ARB_SYS_ARB_OS_VERSION_RETURN}",
        ],
        "next_allowed_action": (
            "Provide a secret-free approval file; then run read-only RPC preflight. "
            "Do not execute until every preflight field matches."
        ),
    }


def preflight(
    approved: ApprovedRun,
    rpc_url: str,
    *,
    artifacts: ProbeArtifacts | None = None,
) -> dict[str, Any]:
    if _sha256_text(rpc_url) != approved.rpc_url_sha256:
        raise ApprovalError("RPC endpoint fingerprint mismatch")
    artifacts = artifacts or compile_probe_artifacts()
    _validate_compiled_artifacts(artifacts)
    if artifacts.source_sha256 != approved.expected_source_sha256:
        raise ApprovalError("probe source hash mismatch")
    if artifacts.abi_sha256 != approved.expected_abi_sha256:
        raise ApprovalError("probe ABI hash mismatch")
    if artifacts.compiler_inputs_sha256 != approved.expected_compiler_inputs_sha256:
        raise ApprovalError("probe compiler-input hash mismatch")
    if artifacts.creation_bytecode_keccak256 != approved.expected_creation_bytecode_hash:
        raise ApprovalError("probe creation-bytecode hash mismatch")
    if artifacts.runtime_bytecode_keccak256 != approved.expected_runtime_bytecode_hash:
        raise ApprovalError("probe runtime-bytecode hash mismatch")

    chain_id = _hex_int(_rpc(rpc_url, "eth_chainId", []), "eth_chainId")
    if chain_id != ROBINHOOD_TESTNET_CHAIN_ID or chain_id != approved.chain_id:
        raise ApprovalError("RPC chain ID is not approved Robinhood testnet 46630")

    client_version = str(_rpc(rpc_url, "web3_clientVersion", []))
    latest = _rpc(rpc_url, "eth_getBlockByNumber", ["latest", False])
    if not isinstance(latest, dict):
        raise ApprovalError("latest block is unavailable")
    latest_number = _hex_int(latest.get("number"), "latest block number")
    latest_timestamp = _hex_int(latest.get("timestamp"), "latest block timestamp")
    latest_hash = _runtime_hash(latest.get("hash"), "latest block hash")
    base_fee = _hex_int(latest.get("baseFeePerGas"), "latest base fee")
    if base_fee + approved.max_priority_fee_per_gas_wei > approved.max_fee_per_gas_wei:
        raise ApprovalError("approved max fee cannot cover current base plus priority fee")

    arb_value = _decode_uint256_response(
        _rpc(
            rpc_url,
            "eth_call",
            [{"to": ARB_SYS, "data": ARB_BLOCK_SELECTOR, "value": "0x0"}, "latest"],
        ),
        "ArbSys(0x64).arbBlockNumber()",
    )
    arb_sys_arb_os_version_return = _decode_uint256_response(
        _rpc(
            rpc_url,
            "eth_call",
            [
                {
                    "to": ARB_SYS,
                    "data": ARB_OS_VERSION_SELECTOR,
                    "value": "0x0",
                },
                "latest",
            ],
        ),
        "ArbSys(0x64).arbOSVersion()",
    )
    if (
        arb_sys_arb_os_version_return
        != approved.expected_arb_sys_arb_os_version_return
    ):
        raise ApprovalError(
            "observed ArbSys arbOSVersion() return disagrees with the "
            "approved derived return"
        )

    nonce = _hex_int(
        _rpc(
            rpc_url,
            "eth_getTransactionCount",
            [approved.signer_address, "pending"],
        ),
        "pending signer nonce",
    )
    if nonce != approved.expected_nonce:
        raise ApprovalError("pending signer nonce mismatch")
    predicted_probe = _predict_create_address(approved.signer_address, nonce)
    if predicted_probe != approved.expected_probe_address:
        raise ApprovalError("predicted deployment address mismatch")
    if _rpc(rpc_url, "eth_getCode", [predicted_probe, "latest"]) != "0x":
        raise ApprovalError("predicted deployment address already contains code")

    signer_balance = _hex_int(
        _rpc(rpc_url, "eth_getBalance", [approved.signer_address, "latest"]),
        "signer balance",
    )
    if signer_balance < approved.max_total_fee_wei:
        raise ApprovalError("approved signer balance is below the total fee cap")

    deployment_call = {
        "from": approved.signer_address,
        "data": "0x" + artifacts.creation_bytecode.hex(),
        "value": "0x0",
    }
    deployment_estimate = _hex_int(
        _rpc(rpc_url, "eth_estimateGas", [deployment_call]),
        "deployment gas estimate",
    )
    if deployment_estimate > approved.deployment_gas_limit:
        raise ApprovalError("deployment gas estimate exceeds approved gas limit")

    return {
        "mode": "rpc-preflight",
        "report_generated_at": datetime.now(UTC).isoformat(),
        "broadcast_enabled": False,
        "rpc_endpoint_read": True,
        "signing_secret_read": False,
        "approval_reference": approved.approval_reference,
        "approval_provenance": {
            "owner": {
                "decision_date": approved.owner_approval_date,
                "reference": approved.owner_approval_reference,
            },
            "independent_security": {
                "decision_date": approved.security_approval_date,
                "reference": approved.security_approval_reference,
            },
            "deployment": {
                "decision_date": approved.deployment_approval_date,
                "reference": approved.deployment_approval_reference,
            },
        },
        "network": "Robinhood Chain testnet",
        "chain_id": chain_id,
        "rpc_identity": {
            "approved_label": approved.rpc_label,
            "url_sha256": approved.rpc_url_sha256,
            "observed_web3_client_version": client_version,
            "client_version_evidence_limit": (
                "Observed evidence only; not proof of the pinned Nitro build."
            ),
        },
        "latest_block": {
            "number": latest_number,
            "hash": latest_hash,
            "timestamp": latest_timestamp,
            "base_fee_per_gas_wei": base_fee,
        },
        "arb_sys_preflight": {
            "address": ARB_SYS,
            "arb_block_number_selector": ARB_BLOCK_SELECTOR,
            "arb_block_number_observed": arb_value,
            "arb_os_version_selector": ARB_OS_VERSION_SELECTOR,
            "robinhood_published_arb_os_profile": (
                approved.robinhood_published_arb_os_profile
            ),
            "pinned_nitro_arb_sys_version_offset": (
                PINNED_NITRO_ARB_SYS_VERSION_OFFSET
            ),
            "expected_arb_sys_arb_os_version_return": (
                approved.expected_arb_sys_arb_os_version_return
            ),
            "observed_arb_sys_arb_os_version_return": (
                arb_sys_arb_os_version_return
            ),
            "version_return_derivation": ARB_SYS_VERSION_RETURN_DERIVATION,
        },
        "signer": {
            "address": approved.signer_address,
            "pending_nonce": nonce,
            "native_balance_wei": signer_balance,
        },
        "probe": {
            "source_path": str(PROBE_CONTRACT.relative_to(REPO_ROOT)),
            "predicted_address": predicted_probe,
            "deployment_gas_estimate": deployment_estimate,
            **artifacts.sanitized(),
        },
        "source_pins": {
            "pin_date": "2026-07-24",
            "nitro_commit": NITRO_COMMIT,
            "arb_sys_interface_commit": ARB_SYS_INTERFACE_COMMIT,
            "robinhood_node_image": ROBINHOOD_NODE_IMAGE,
            "robinhood_published_arb_os_profile": (
                ROBINHOOD_PUBLISHED_ARB_OS_PROFILE
            ),
            "pinned_nitro_arb_sys_version_offset": (
                PINNED_NITRO_ARB_SYS_VERSION_OFFSET
            ),
            "expected_arb_sys_arb_os_version_return": (
                EXPECTED_ARB_SYS_ARB_OS_VERSION_RETURN
            ),
        },
        "transaction_constraints": {
            "native_value_wei": 0,
            "token_transfer": False,
            "max_transaction_count": approved.max_transaction_count,
            "max_observation_transactions": approved.max_observation_transactions,
            "deployment_gas_limit": approved.deployment_gas_limit,
            "observation_gas_limit": approved.observation_gas_limit,
            "max_fee_per_gas_wei": approved.max_fee_per_gas_wei,
            "max_priority_fee_per_gas_wei": approved.max_priority_fee_per_gas_wei,
            "worst_case_total_fee_wei": approved.worst_case_total_fee_wei,
            "owner_approved_total_fee_cap_wei": approved.max_total_fee_wei,
        },
        "ready_for_live_testnet_execution": True,
    }


def _observe_calldata(observation_id: int) -> str:
    return "0x" + (OBSERVE_SELECTOR + encode(["uint256"], [observation_id])).hex()


def _transaction(
    approved: ApprovedRun,
    *,
    nonce: int,
    gas: int,
    data: str,
    to: str | None = None,
) -> dict[str, Any]:
    transaction: dict[str, Any] = {
        "chainId": approved.chain_id,
        "nonce": nonce,
        "gas": gas,
        "maxFeePerGas": approved.max_fee_per_gas_wei,
        "maxPriorityFeePerGas": approved.max_priority_fee_per_gas_wei,
        "value": 0,
        "data": data,
        "type": 2,
    }
    if to is not None:
        transaction["to"] = to_checksum_address(to)
    return transaction


def _prepare_signed_transaction(
    transaction: dict[str, Any],
    private_key: str,
    intended_action: str,
) -> tuple[bytes, dict[str, Any]]:
    signed = Account.sign_transaction(transaction, private_key)
    raw = getattr(signed, "raw_transaction", None)
    if raw is None:
        raw = signed.rawTransaction
    raw_bytes = bytes(raw)
    local_hash = _keccak_bytes(raw_bytes)
    nonce = transaction.get("nonce")
    if not isinstance(nonce, int) or nonce < 0:
        raise ApprovalError("signed transaction nonce is invalid")
    return raw_bytes, {
        "transaction_hash": local_hash,
        "nonce": nonce,
        "intended_action": intended_action,
        "broadcast_status": "signed-and-persisted-before-broadcast",
    }


def _wait_receipt(
    rpc_url: str,
    transaction_hash: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        receipt = _rpc(
            rpc_url,
            "eth_getTransactionReceipt",
            [transaction_hash],
        )
        if receipt is not None:
            if not isinstance(receipt, dict):
                raise ApprovalError("transaction receipt has invalid shape")
            return receipt
        time.sleep(1)
    raise ApprovalError("transaction receipt timeout")


def _receipt_fee(receipt: dict[str, Any]) -> int:
    gas_used = _hex_int(receipt.get("gasUsed"), "receipt gasUsed")
    gas_price = _hex_int(
        receipt.get("effectiveGasPrice"),
        "receipt effectiveGasPrice",
    )
    return gas_used * gas_price


def _decode_observation(
    rpc_url: str,
    receipt: dict[str, Any],
    *,
    expected_probe: str,
    expected_signer: str,
    expected_observation_id: int,
) -> dict[str, Any]:
    if _hex_int(receipt.get("status"), "receipt status") != 1:
        raise ApprovalError("observation transaction reverted")
    matching_logs = []
    for log in receipt.get("logs", []):
        topics = log.get("topics", [])
        if (
            to_checksum_address(log.get("address")) == expected_probe
            and topics
            and str(topics[0]).lower() == OBSERVED_EVENT_TOPIC.lower()
        ):
            matching_logs.append(log)
    if len(matching_logs) != 1:
        raise ApprovalError("expected exactly one ActionBlockObserved event")

    raw_data = bytes.fromhex(matching_logs[0]["data"][2:])
    if len(raw_data) != 160:
        raise ApprovalError("ActionBlockObserved event has incompatible ABI data")
    (
        observation_id,
        caller,
        native_block,
        arb_block,
        observed_at,
    ) = decode(
        ["uint256", "address", "uint256", "uint256", "uint256"],
        raw_data,
    )
    if observation_id != expected_observation_id:
        raise ApprovalError("observation ID mismatch")
    if to_checksum_address(caller) != expected_signer:
        raise ApprovalError("observation caller mismatch")

    receipt_block = _hex_int(receipt.get("blockNumber"), "receipt block number")
    block = _rpc(rpc_url, "eth_getBlockByNumber", [hex(receipt_block), False])
    block_timestamp = _hex_int(block.get("timestamp"), "receipt block timestamp")
    transaction_hash = _runtime_hash(
        receipt.get("transactionHash"),
        "receipt transaction hash",
    )
    return {
        "observation_id": observation_id,
        "transaction_hash": transaction_hash,
        "receipt_block_number": receipt_block,
        "receipt_block_timestamp": block_timestamp,
        "native_block_number": native_block,
        "arb_block_number": arb_block,
        "arb_receipt_agreement": arb_block == receipt_block,
        "contract_observed_at": observed_at,
        "gas_used": _hex_int(receipt.get("gasUsed"), "observation gas used"),
        "effective_gas_price_wei": _hex_int(
            receipt.get("effectiveGasPrice"),
            "observation effective gas price",
        ),
        "fee_paid_wei": _receipt_fee(receipt),
    }


def analyze_observations(observations: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(
        observations,
        key=lambda item: (
            item["receipt_block_number"],
            item["observation_id"],
        ),
    )
    agreement = all(
        item["arb_block_number"] == item["receipt_block_number"]
        for item in ordered
    )

    by_child: dict[int, list[dict[str, Any]]] = {}
    for item in ordered:
        by_child.setdefault(item["receipt_block_number"], []).append(item)
    same_child_groups = [
        {
            "child_block": child,
            "transaction_hashes": [item["transaction_hash"] for item in items],
            "arb_block_number": items[0]["arb_block_number"],
        }
        for child, items in sorted(by_child.items())
        if len({item["transaction_hash"] for item in items}) >= 2
    ]

    child_blocks = sorted(by_child)
    successive_pairs: list[dict[str, Any]] = []
    repeated_native_successive_pairs: list[dict[str, Any]] = []
    for first_block, second_block in zip(child_blocks, child_blocks[1:]):
        if second_block != first_block + 1:
            continue
        first = by_child[first_block][0]
        second = by_child[second_block][0]
        pair = {
            "first_child_block": first_block,
            "second_child_block": second_block,
            "first_arb_block_number": first["arb_block_number"],
            "second_arb_block_number": second["arb_block_number"],
            "first_native_block_number": first["native_block_number"],
            "second_native_block_number": second["native_block_number"],
        }
        successive_pairs.append(pair)
        if first["native_block_number"] == second["native_block_number"]:
            repeated_native_successive_pairs.append(pair)

    missing: list[str] = []
    if not agreement:
        missing.append("direct ArbSys/receipt agreement")
    if not same_child_groups:
        missing.append("two separate transactions in one child block")
    if not successive_pairs:
        missing.append("observations in successive child blocks")
    if not repeated_native_successive_pairs:
        missing.append("successive child blocks sharing one native ancestor number")

    native_values = [item["native_block_number"] for item in ordered]
    arb_values = [item["arb_block_number"] for item in ordered]
    return {
        "proof_complete": not missing,
        "status": "complete" if not missing else "inconclusive",
        "direct_arb_receipt_agreement": agreement,
        "same_child_block_groups": same_child_groups,
        "successive_child_block_pairs": successive_pairs,
        "successive_child_blocks_with_repeated_native_number": (
            repeated_native_successive_pairs
        ),
        "missing_topologies": missing,
        "bounded_observation": {
            "transaction_count": len(ordered),
            "distinct_child_blocks": len(set(arb_values)),
            "distinct_native_values": len(set(native_values)),
            "observed_child_values": sorted(set(arb_values)),
            "observed_native_values": sorted(set(native_values)),
            "interpretation": (
                "These values and deltas are bounded observations only; no "
                "observed repetition or jump is a protocol maximum."
            ),
        },
    }


def _persist_progress(report: dict[str, Any], output: Path | None) -> None:
    if output is not None:
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


def _enforce_observation_burst_fee_cap(
    report: dict[str, Any],
    output: Path | None,
    *,
    actual_fee: int,
    batch_worst_case: int,
    max_total_fee: int,
) -> None:
    projected_total_fee = actual_fee + batch_worst_case
    if projected_total_fee <= max_total_fee:
        return

    report["result"] = "stopped-before-observation-burst-total-fee-cap"
    report.setdefault("fees", {}).update(
        {
            "next_observation_burst_worst_case_wei": batch_worst_case,
            "projected_total_fee_wei": projected_total_fee,
        }
    )
    _persist_progress(report, output)
    raise ApprovalError("next observation burst would exceed total fee cap")


def _journal_and_broadcast(
    report: dict[str, Any],
    output: Path | None,
    rpc_url: str,
    transaction: dict[str, Any],
    private_key: str,
    intended_action: str,
) -> str:
    raw_transaction, journal_entry = _prepare_signed_transaction(
        transaction,
        private_key,
        intended_action,
    )
    report.setdefault("signed_transactions", []).append(journal_entry)
    _persist_progress(report, output)

    try:
        rpc_hash = _runtime_hash(
            _rpc(
                rpc_url,
                "eth_sendRawTransaction",
                ["0x" + raw_transaction.hex()],
            ),
            "broadcast transaction hash",
        )
    except Exception:
        journal_entry["broadcast_status"] = (
            "rpc-error-after-submit-acceptance-ambiguous"
        )
        report["result"] = "stopped-ambiguous-broadcast-outcome"
        _persist_progress(report, output)
        raise

    journal_entry["rpc_returned_hash"] = rpc_hash
    if rpc_hash != journal_entry["transaction_hash"]:
        journal_entry["broadcast_status"] = "rpc-returned-hash-mismatch"
        report["result"] = "stopped-rpc-transaction-hash-mismatch"
        _persist_progress(report, output)
        raise ApprovalError(
            "RPC-returned transaction hash disagrees with locally derived hash"
        )

    journal_entry["broadcast_status"] = "rpc-hash-matched"
    _persist_progress(report, output)
    return journal_entry["transaction_hash"]


def execute_live_testnet(
    approved: ApprovedRun,
    rpc_url: str,
    *,
    progress_output: Path | None = None,
    signing_secret_loader: Callable[[], Any] | None = None,
    artifacts: ProbeArtifacts | None = None,
) -> dict[str, Any]:
    if progress_output is None:
        raise ApprovalError(
            "live execution requires a sanitized progress output file"
        )
    artifacts = artifacts or compile_probe_artifacts()
    _validate_compiled_artifacts(artifacts)
    report = preflight(approved, rpc_url, artifacts=artifacts)
    private_key = (
        signing_secret_loader()
        if signing_secret_loader is not None
        else _signing_secret_from_environment(approved)
    )

    try:
        signer_from_key = to_checksum_address(Account.from_key(private_key).address)
    except Exception as exc:
        raise ApprovalError("approved private key could not be loaded") from exc
    if signer_from_key != approved.signer_address:
        raise ApprovalError("private key does not match approved testnet signer")

    report.update(
        {
            "mode": "live-testnet-proof",
            "broadcast_enabled": True,
            "rpc_endpoint_read": True,
            "signing_secret_read": True,
            "signed_transactions": [],
            "observations": [],
            "pending_observation_transactions": [],
            "result": "live-execution-in-progress",
        }
    )
    _persist_progress(report, progress_output)

    creation_data = "0x" + artifacts.creation_bytecode.hex()
    deploy_tx = _transaction(
        approved,
        nonce=approved.expected_nonce,
        gas=approved.deployment_gas_limit,
        data=creation_data,
    )
    deploy_hash = _journal_and_broadcast(
        report,
        progress_output,
        rpc_url,
        deploy_tx,
        private_key,
        "deploy-probe",
    )
    report["probe"]["deployment_transaction_hash"] = deploy_hash
    report["result"] = "deployment-broadcast-awaiting-receipt"
    _persist_progress(report, progress_output)
    deploy_receipt = _wait_receipt(
        rpc_url,
        deploy_hash,
        approved.receipt_timeout_seconds,
    )
    if _hex_int(deploy_receipt.get("status"), "deployment status") != 1:
        raise ApprovalError("probe deployment reverted")
    deployed_address = to_checksum_address(deploy_receipt.get("contractAddress"))
    if deployed_address != approved.expected_probe_address:
        raise ApprovalError("deployed probe address mismatch")
    deployed_code = _rpc(rpc_url, "eth_getCode", [deployed_address, "latest"])
    if deployed_code == "0x":
        raise ApprovalError("deployed probe has no runtime code")
    if _keccak_bytes(bytes.fromhex(deployed_code[2:])) != approved.expected_runtime_bytecode_hash:
        raise ApprovalError("deployed probe runtime-bytecode hash mismatch")

    deployment_block_number = _hex_int(
        deploy_receipt.get("blockNumber"),
        "deployment receipt block number",
    )
    deployment_block = _rpc(
        rpc_url,
        "eth_getBlockByNumber",
        [hex(deployment_block_number), False],
    )
    if not isinstance(deployment_block, dict):
        raise ApprovalError("deployment block is unavailable")
    deployment_block_timestamp = _hex_int(
        deployment_block.get("timestamp"),
        "deployment block timestamp",
    )
    deployment_fee = _receipt_fee(deploy_receipt)
    if deployment_fee > approved.max_total_fee_wei:
        raise ApprovalError("deployment consumed more than the approved total fee cap")

    report["probe"].update(
        {
            "address": deployed_address,
            "deployment_receipt_block_number": deployment_block_number,
            "deployment_block_timestamp": deployment_block_timestamp,
            "deployed_runtime_bytecode_keccak256": (
                approved.expected_runtime_bytecode_hash
            ),
        }
    )
    report["fees"] = {
        "deployment_fee_paid_wei": deployment_fee,
        "actual_total_fee_paid_wei": deployment_fee,
        "owner_approved_total_fee_cap_wei": approved.max_total_fee_wei,
    }
    report["result"] = "deployment-confirmed"
    _persist_progress(report, progress_output)

    observation_estimate = _hex_int(
        _rpc(
            rpc_url,
            "eth_estimateGas",
            [
                {
                    "from": approved.signer_address,
                    "to": deployed_address,
                    "data": _observe_calldata(0),
                    "value": "0x0",
                }
            ],
        ),
        "observation gas estimate",
    )
    if observation_estimate > approved.observation_gas_limit:
        raise ApprovalError("observation gas estimate exceeds approved gas limit")

    observations: list[dict[str, Any]] = []
    actual_fee = deployment_fee
    next_nonce = approved.expected_nonce + 1
    hard_stop = False
    while len(observations) < approved.max_observation_transactions:
        batch_size = min(
            2,
            approved.max_observation_transactions - len(observations),
        )
        batch_worst_case = (
            batch_size
            * approved.observation_gas_limit
            * approved.max_fee_per_gas_wei
        )
        _enforce_observation_burst_fee_cap(
            report,
            progress_output,
            actual_fee=actual_fee,
            batch_worst_case=batch_worst_case,
            max_total_fee=approved.max_total_fee_wei,
        )

        pending: list[tuple[int, str]] = []
        for offset in range(batch_size):
            observation_id = len(observations) + offset
            tx = _transaction(
                approved,
                nonce=next_nonce + offset,
                gas=approved.observation_gas_limit,
                data=_observe_calldata(observation_id),
                to=deployed_address,
            )
            pending.append(
                (
                    observation_id,
                    _journal_and_broadcast(
                        report,
                        progress_output,
                        rpc_url,
                        tx,
                        private_key,
                        f"observe:{observation_id}",
                    ),
                )
            )
        next_nonce += batch_size
        report["pending_observation_transactions"] = [
            {
                "observation_id": observation_id,
                "transaction_hash": transaction_hash,
            }
            for observation_id, transaction_hash in pending
        ]
        report["result"] = "observations-broadcast-awaiting-receipts"
        _persist_progress(report, progress_output)

        for observation_id, transaction_hash in pending:
            receipt = _wait_receipt(
                rpc_url,
                transaction_hash,
                approved.receipt_timeout_seconds,
            )
            observation = _decode_observation(
                rpc_url,
                receipt,
                expected_probe=deployed_address,
                expected_signer=approved.signer_address,
                expected_observation_id=observation_id,
            )
            actual_fee += observation["fee_paid_wei"]
            if actual_fee > approved.max_total_fee_wei:
                raise ApprovalError("actual fees exceeded the approved total fee cap")
            observations.append(observation)
            report["observations"] = observations
            report["fees"]["actual_total_fee_paid_wei"] = actual_fee
            report["pending_observation_transactions"] = [
                item
                for item in report["pending_observation_transactions"]
                if item["transaction_hash"] != transaction_hash
            ]
            if not observation["arb_receipt_agreement"]:
                hard_stop = True
                report["result"] = "stopped-arbsys-receipt-disagreement"
            _persist_progress(report, progress_output)

        topology = analyze_observations(observations)
        if topology["proof_complete"] or hard_stop:
            break

    topology = analyze_observations(observations)
    report.update(
        {
            "mode": "live-testnet-proof",
            "broadcast_enabled": True,
            "probe": {
                **report["probe"],
            },
            "observations": observations,
            "pending_observation_transactions": [],
            "topology": topology,
            "fees": {
                "deployment_fee_paid_wei": deployment_fee,
                "actual_total_fee_paid_wei": actual_fee,
                "owner_approved_total_fee_cap_wei": approved.max_total_fee_wei,
                "observation_gas_estimate": observation_estimate,
            },
            "result": (
                "stopped-arbsys-receipt-disagreement"
                if hard_stop
                else (
                    "complete"
                    if topology["proof_complete"]
                    else "inconclusive-within-approved-bound"
                )
            ),
        }
    )
    _persist_progress(report, progress_output)
    return report


def _write_or_print(report: dict[str, Any], output: Path | None) -> None:
    serialized = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if output is None:
        print(serialized, end="")
        return
    output.write_text(serialized)
    print(f"sanitized report written to {output}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--approval-file", type=Path)
    parser.add_argument("--confirm-live-testnet", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.dry_run:
        if args.approval_file or args.confirm_live_testnet:
            raise ApprovalError("local dry run does not accept live approval inputs")
        _write_or_print(local_dry_run(), args.output)
        return 0

    if args.approval_file is None:
        raise ApprovalError("RPC preflight and execution require an approval file")
    approved = load_approval(args.approval_file)

    if args.preflight:
        if args.confirm_live_testnet:
            raise ApprovalError("read-only preflight does not accept live confirmation")
        artifacts = compile_probe_artifacts()
        _validate_compiled_artifacts(artifacts)
        rpc_url = _rpc_url_from_environment(approved)
        _write_or_print(
            preflight(approved, rpc_url, artifacts=artifacts),
            args.output,
        )
        return 0

    if not args.confirm_live_testnet:
        raise ApprovalError("live execution requires --confirm-live-testnet")
    if args.output is None:
        raise ApprovalError(
            "live execution requires --output for sanitized progress evidence"
        )
    artifacts = compile_probe_artifacts()
    _validate_compiled_artifacts(artifacts)
    rpc_url = _rpc_url_from_environment(approved)
    report = execute_live_testnet(
        approved,
        rpc_url,
        progress_output=args.output,
        artifacts=artifacts,
    )
    _write_or_print(report, args.output)
    return 0


def cli() -> int:
    try:
        return main()
    except ApprovalError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except Exception:
        print("error: unexpected probe failure", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(cli())
