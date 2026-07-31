from __future__ import annotations

import hashlib
import os
import re
import shutil
import socket
import stat
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Protocol
from urllib.parse import urlsplit

import pytest
import requests

from scripts.utils.manifest_schema import (
    ManifestError,
    canonical_json_bytes,
    load_json_bytes,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SUITE_ROOT = Path(__file__).resolve().parent
FRAMEWORK_SCHEMA = "h09-rh-archive-fork-v1"
IDENTITY_SCHEMA = "owner-rh-canonical-identities-v1"
READ_ONLY_OPT_IN = "read-only-archive-fork"
MODE_ENV = "RIPE_RH_FORK_MODE"
MANIFEST_ENV = "RIPE_RH_FORK_MANIFEST"
IDENTITY_MANIFEST_ENV = "RIPE_RH_FORK_IDENTITY_MANIFEST"
DISABLED_MODE = "disabled"
PATH_CEILING = 33

IMPLEMENTED_PATH_LEDGER = (
    "tests/deployment/fork/conftest.py",
    "tests/deployment/fork/identity/conftest.py",
    "tests/deployment/fork/identity/test_canonical_tokens.py",
    "tests/deployment/fork/identity/test_protocol_artifacts.py",
    "tests/deployment/fork/lifecycle/conftest.py",
    "tests/deployment/fork/lifecycle/test_replay_evidence_rollback.py",
    "tests/deployment/fork/network/conftest.py",
    "tests/deployment/fork/network/test_clocks.py",
    "tests/deployment/fork/network/test_fork_lifecycle.py",
    "tests/deployment/fork/network/test_pin_archive.py",
    "tests/deployment/fork/network/test_rpc_inventory.py",
    "tests/deployment/fork/offline/conftest.py",
    "tests/deployment/fork/offline/test_collection_contract.py",
    "tests/deployment/fork/offline/test_entry_gates.py",
    "tests/deployment/fork/offline/test_process_isolation.py",
)

READ_ONLY_RPC_METHODS = frozenset(
    {
        "eth_call",
        "eth_chainId",
        "eth_getBlockByHash",
        "eth_getBlockByNumber",
        "eth_getCode",
        "eth_getProof",
        "eth_getStorageAt",
        "eth_getTransactionByHash",
        "eth_getTransactionReceipt",
    }
)
LOCAL_FORK_ACTIONS = frozenset(
    {"impersonate", "set_balance", "set_storage", "time_travel"}
)
FORBIDDEN_RPC_METHOD_PREFIXES = (
    "eth_send",
    "personal_",
    "wallet_",
    "account_",
    "admin_",
    "miner_",
)
FORBIDDEN_ENV_NAMES = frozenset(
    {
        "ALCHEMY_API_KEY",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "BASE_MAINNET_RPC_URL",
        "BASE_RPC_URL",
        "DEPLOYER_PRIVATE_KEY",
        "ETHERSCAN_API_KEY",
        "ETH_RPC_URL",
        "MNEMONIC",
        "PRIVATE_KEY",
        "ROBINHOOD_MAINNET_RPC_URL",
        "ROBINHOOD_TESTNET_RPC_URL",
        "RPC_URL",
        "TEST_PRIVATE_KEY",
        "WEB3_ALCHEMY_API_KEY",
        "WEB3_PROVIDER_URI",
    }
)

_HEX40 = re.compile(r"[0-9a-f]{40}")
_HEX64 = re.compile(r"[0-9a-f]{64}")
_HASH32 = re.compile(r"0x[0-9a-f]{64}")
_ADDRESS = re.compile(r"0x[0-9A-Fa-f]{40}")
_IDENTIFIER = re.compile(r"[a-z][a-z0-9_-]{0,63}")
_ENV_ALIAS = re.compile(r"OWNER_RH_ARCHIVE_[A-Z0-9_]{1,48}")
_UTC_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
_SENSITIVE_KEY_PARTS = (
    "credential",
    "mnemonic",
    "password",
    "private_key",
    "rpc_url",
    "secret",
    "token",
    "url",
)


class ForkFrameworkError(RuntimeError):
    __slots__ = ("code",)

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class RepositoryAuthority:
    commit: str
    tree: str
    path_ceiling: int


@dataclass(frozen=True, slots=True)
class BlockPin:
    number: int
    block_hash: str
    parent_hash: str
    state_root: str
    timestamp: int
    finality: str


@dataclass(frozen=True, slots=True)
class EndpointIdentity:
    external_alias: str
    fingerprint_sha256: str


@dataclass(frozen=True, slots=True)
class OwnerInputs:
    profile: str
    expected_chain_id: int
    pin: BlockPin
    endpoint: EndpointIdentity
    identity_manifest_sha256: str
    identity_manifest_schema: str
    evidence_destination: Path
    read_only: bool
    affirmative_opt_in: str
    valid_until: datetime
    rpc_methods: tuple[str, ...]
    local_fork_actions: tuple[str, ...]
    bindings: Mapping[str, Mapping[str, str]]
    fork_engine: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class QualificationEnvelope:
    repository: RepositoryAuthority
    owner: OwnerInputs
    canonical_bytes: bytes
    sha256: str


@dataclass(frozen=True, slots=True)
class CanonicalIdentity:
    identity_id: str
    kind: str
    address: str
    proxy_address: str | None
    implementation_address: str | None
    runtime_code_sha256: str
    authority: str
    provenance_sha256: str


@dataclass(frozen=True, slots=True)
class CanonicalIdentityManifest:
    profile: str
    chain_id: int
    identities: tuple[CanonicalIdentity, ...]
    owner_approval_sha256: str
    canonical_bytes: bytes
    sha256: str


@dataclass(frozen=True, slots=True)
class ObservedForkFacts:
    chain_id: int
    block_number: int
    block_hash: str
    parent_hash: str
    state_root: str
    timestamp: int
    endpoint_fingerprint_sha256: str


@dataclass(frozen=True, slots=True)
class BoundForkIdentity:
    repository: RepositoryAuthority
    owner: OwnerInputs
    observed: ObservedForkFacts


@dataclass(frozen=True, slots=True)
class PreflightResult:
    envelope: QualificationEnvelope
    identity_manifest: CanonicalIdentityManifest
    endpoint: OpaqueEndpoint


@dataclass(frozen=True, slots=True)
class OpaqueEndpoint:
    _value: str
    alias: str
    fingerprint_sha256: str

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return (
            f"<archive-endpoint alias={self.alias} "
            f"fingerprint={self.fingerprint_sha256} redacted>"
        )

    def __repr__(self) -> str:
        return (
            "OpaqueEndpoint("
            f"alias={self.alias!r}, "
            f"fingerprint_sha256={self.fingerprint_sha256!r}, "
            "value='<redacted>')"
        )


class RuntimeProcess(Protocol):
    pid: int

    def poll(self) -> int | None: ...

    def terminate(self) -> None: ...

    def wait(self, timeout: float | None = None) -> int: ...


@dataclass(frozen=True, slots=True)
class ForkRuntimeSpec:
    replay_identity: str
    engine_name: str
    engine_version: str
    chain_id: int
    block_number: int
    block_hash: str
    read_only_upstream: bool = True


@dataclass(frozen=True, slots=True)
class RuntimeDestructionProof:
    runtime_id: str
    process_terminated: bool
    storage_disposed: bool


class DisposableForkRuntime:
    def __init__(
        self,
        *,
        external_root: Path,
        repository_root: Path,
        spec: ForkRuntimeSpec,
        process_factory: Callable[[ForkRuntimeSpec, Path], RuntimeProcess],
    ) -> None:
        _validate_digest(spec.replay_identity, "H09_RUNTIME_REPLAY_ID")
        if not spec.read_only_upstream:
            raise ForkFrameworkError("H09_RUNTIME_UPSTREAM_NOT_READ_ONLY")
        validate_external_root(external_root, repository_root=repository_root)
        self.external_root = external_root.resolve()
        self.repository_root = repository_root.resolve()
        self.spec = spec
        self.process_factory = process_factory
        self.runtime_id = hashlib.sha256(
            b"RIPE_H09_RUNTIME_V1\0"
            + canonical_json_bytes(
                {
                    "block_hash": spec.block_hash,
                    "block_number": spec.block_number,
                    "chain_id": spec.chain_id,
                    "engine_name": spec.engine_name,
                    "engine_version": spec.engine_version,
                    "read_only_upstream": spec.read_only_upstream,
                    "replay_identity": spec.replay_identity,
                }
            )
        ).hexdigest()
        self.runtime_dir = self.external_root / f"runtime-{self.runtime_id[:20]}"
        self._process: RuntimeProcess | None = None

    def create(self) -> RuntimeProcess:
        if self._process is not None:
            raise ForkFrameworkError("H09_RUNTIME_ALREADY_CREATED")
        if self.runtime_dir.exists():
            raise ForkFrameworkError("H09_RUNTIME_RESIDUE")
        self.runtime_dir.mkdir(mode=0o700)
        if stat.S_IMODE(self.runtime_dir.stat().st_mode) != 0o700:
            raise ForkFrameworkError("H09_RUNTIME_MODE")
        try:
            process = self.process_factory(self.spec, self.runtime_dir)
        except Exception:
            shutil.rmtree(self.runtime_dir)
            raise
        if process.poll() is not None:
            shutil.rmtree(self.runtime_dir)
            raise ForkFrameworkError("H09_RUNTIME_NOT_LIVE")
        self._process = process
        return process

    def destroy(self) -> RuntimeDestructionProof:
        if self._process is None:
            raise ForkFrameworkError("H09_RUNTIME_NOT_CREATED")
        process = self._process
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
        if process.poll() is None:
            raise ForkFrameworkError("H09_RUNTIME_TEARDOWN")
        if not self.runtime_dir.is_dir():
            raise ForkFrameworkError("H09_RUNTIME_STORAGE_MISSING")
        shutil.rmtree(self.runtime_dir)
        if self.runtime_dir.exists():
            raise ForkFrameworkError("H09_RUNTIME_RESIDUE")
        self._process = None
        return RuntimeDestructionProof(
            runtime_id=self.runtime_id,
            process_terminated=True,
            storage_disposed=True,
        )


def _fail(code: str) -> None:
    raise ForkFrameworkError(code)


def _require_mapping(value: Any, code: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        _fail(code)
    return value


def _require_exact_keys(
    value: Mapping[str, Any], expected: frozenset[str], code: str
) -> None:
    if frozenset(value) != expected:
        _fail(code)


def _require_string(value: Any, code: str) -> str:
    if not isinstance(value, str) or not value:
        _fail(code)
    return value


def _require_bool(value: Any, code: str) -> bool:
    if not isinstance(value, bool):
        _fail(code)
    return value


def _require_positive_int(value: Any, code: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        _fail(code)
    return value


def _validate_digest(value: Any, code: str) -> str:
    digest = _require_string(value, code)
    if not _HEX64.fullmatch(digest) or digest == "0" * 64:
        _fail(code)
    return digest


def _validate_hash32(value: Any, code: str) -> str:
    digest = _require_string(value, code)
    if not _HASH32.fullmatch(digest) or digest == "0x" + "0" * 64:
        _fail(code)
    return digest


def _validate_address(value: Any, code: str) -> str:
    address = _require_string(value, code)
    if not _ADDRESS.fullmatch(address) or int(address[2:], 16) == 0:
        _fail(code)
    return address


def _optional_address(value: Any, code: str) -> str | None:
    if value is None:
        return None
    return _validate_address(value, code)


def _parse_utc(value: Any, code: str) -> datetime:
    text = _require_string(value, code)
    if not _UTC_TIMESTAMP.fullmatch(text):
        _fail(code)
    try:
        return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        _fail(code)


def _canonical_mapping(data: bytes, *, code: str) -> Mapping[str, Any]:
    try:
        value = load_json_bytes(data)
        if canonical_json_bytes(value) != data:
            _fail(f"{code}_NONCANONICAL")
    except (ManifestError, UnicodeDecodeError, ValueError) as error:
        raise ForkFrameworkError(f"{code}_MALFORMED") from error
    return _require_mapping(value, f"{code}_OBJECT")


def _parse_binding_map(value: Any) -> Mapping[str, Mapping[str, str]]:
    bindings = _require_mapping(value, "H09_BINDINGS_OBJECT")
    required = frozenset(
        {
            "h05_plan",
            "typed_actions",
            "h06_evidence",
            "h07_artifacts",
            "h08_assertions",
            "h09_contract",
        }
    )
    _require_exact_keys(bindings, required, "H09_BINDINGS_KEYS")
    parsed: dict[str, Mapping[str, str]] = {}
    for name in sorted(bindings):
        binding = _require_mapping(bindings[name], "H09_BINDING_OBJECT")
        _require_exact_keys(
            binding, frozenset({"version", "sha256"}), "H09_BINDING_KEYS"
        )
        version = _require_string(binding["version"], "H09_BINDING_VERSION")
        digest = _validate_digest(binding["sha256"], "H09_BINDING_DIGEST")
        parsed[name] = {"version": version, "sha256": digest}
    return parsed


def _parse_rpc_methods(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        _fail("H09_RPC_METHODS")
    if any(not isinstance(item, str) for item in value):
        _fail("H09_RPC_METHODS")
    methods = tuple(value)
    if methods != tuple(sorted(set(methods))):
        _fail("H09_RPC_METHOD_ORDER")
    validate_rpc_inventory(methods)
    return methods


def _parse_local_actions(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        _fail("H09_LOCAL_ACTIONS")
    if any(not isinstance(item, str) for item in value):
        _fail("H09_LOCAL_ACTIONS")
    actions = tuple(value)
    if actions != tuple(sorted(set(actions))):
        _fail("H09_LOCAL_ACTION_ORDER")
    unknown = set(actions) - LOCAL_FORK_ACTIONS
    if unknown:
        _fail("H09_LOCAL_ACTION_FORBIDDEN")
    return actions


def parse_input_envelope(
    data: bytes, *, now: datetime | None = None
) -> QualificationEnvelope:
    value = _canonical_mapping(data, code="H09_ENVELOPE")
    _require_exact_keys(
        value,
        frozenset(
            {
                "artifact_kind",
                "schema_version",
                "repository_authority",
                "owner_inputs",
                "requested_capabilities",
            }
        ),
        "H09_ENVELOPE_KEYS",
    )
    if value["artifact_kind"] != "rh_archive_fork_input_envelope":
        _fail("H09_ENVELOPE_KIND")
    if value["schema_version"] != FRAMEWORK_SCHEMA:
        _fail("H09_ENVELOPE_SCHEMA")

    repository_value = _require_mapping(
        value["repository_authority"], "H09_REPOSITORY_OBJECT"
    )
    _require_exact_keys(
        repository_value,
        frozenset({"commit", "tree", "suite_path_ceiling"}),
        "H09_REPOSITORY_KEYS",
    )
    commit = _require_string(repository_value["commit"], "H09_REPOSITORY_COMMIT")
    tree = _require_string(repository_value["tree"], "H09_REPOSITORY_TREE")
    if not _HEX40.fullmatch(commit):
        _fail("H09_REPOSITORY_COMMIT")
    if not _HEX40.fullmatch(tree):
        _fail("H09_REPOSITORY_TREE")
    ceiling = _require_positive_int(
        repository_value["suite_path_ceiling"], "H09_PATH_CEILING"
    )
    if ceiling != PATH_CEILING:
        _fail("H09_PATH_CEILING")
    repository = RepositoryAuthority(commit, tree, ceiling)

    owner_value = _require_mapping(value["owner_inputs"], "H09_OWNER_OBJECT")
    _require_exact_keys(
        owner_value,
        frozenset(
            {
                "profile",
                "expected_chain_id",
                "pin",
                "endpoint",
                "identity_manifest_sha256",
                "identity_manifest_schema",
                "evidence_destination",
                "fork_engine",
                "bindings",
                "read_only",
                "affirmative_opt_in",
                "valid_until",
            }
        ),
        "H09_OWNER_KEYS",
    )
    profile = _require_string(owner_value["profile"], "H09_PROFILE")
    if profile not in {"robinhood-mainnet", "robinhood-testnet"}:
        _fail("H09_PROFILE")
    expected_chain_id = _require_positive_int(
        owner_value["expected_chain_id"], "H09_CHAIN_ID"
    )
    expected_profile_chain = {
        "robinhood-mainnet": 4663,
        "robinhood-testnet": 46630,
    }[profile]
    if expected_chain_id != expected_profile_chain:
        _fail("H09_PROFILE_CHAIN_CONTRADICTION")

    pin_value = _require_mapping(owner_value["pin"], "H09_PIN_OBJECT")
    _require_exact_keys(
        pin_value,
        frozenset(
            {
                "block_number",
                "block_hash",
                "parent_hash",
                "state_root",
                "timestamp",
                "finality",
            }
        ),
        "H09_PIN_KEYS",
    )
    finality = _require_string(pin_value["finality"], "H09_PIN_FINALITY")
    if finality not in {"finalized", "owner-approved-immutable"}:
        _fail("H09_PIN_FINALITY")
    pin = BlockPin(
        number=_require_positive_int(
            pin_value["block_number"], "H09_PIN_NUMBER"
        ),
        block_hash=_validate_hash32(pin_value["block_hash"], "H09_PIN_HASH"),
        parent_hash=_validate_hash32(
            pin_value["parent_hash"], "H09_PIN_PARENT_HASH"
        ),
        state_root=_validate_hash32(
            pin_value["state_root"], "H09_PIN_STATE_ROOT"
        ),
        timestamp=_require_positive_int(
            pin_value["timestamp"], "H09_PIN_TIMESTAMP"
        ),
        finality=finality,
    )
    if pin.block_hash == pin.parent_hash:
        _fail("H09_PIN_CONTRADICTION")

    endpoint_value = _require_mapping(
        owner_value["endpoint"], "H09_ENDPOINT_OBJECT"
    )
    _require_exact_keys(
        endpoint_value,
        frozenset({"external_alias", "fingerprint_sha256"}),
        "H09_ENDPOINT_KEYS",
    )
    alias = _require_string(
        endpoint_value["external_alias"], "H09_ENDPOINT_ALIAS"
    )
    if not _ENV_ALIAS.fullmatch(alias):
        _fail("H09_ENDPOINT_ALIAS")
    endpoint = EndpointIdentity(
        alias,
        _validate_digest(
            endpoint_value["fingerprint_sha256"], "H09_ENDPOINT_FINGERPRINT"
        ),
    )

    destination_text = _require_string(
        owner_value["evidence_destination"], "H09_EVIDENCE_DESTINATION"
    )
    destination = Path(destination_text)
    if not destination.is_absolute():
        _fail("H09_EVIDENCE_DESTINATION")
    validate_external_root(destination)

    engine_value = _require_mapping(
        owner_value["fork_engine"], "H09_ENGINE_OBJECT"
    )
    _require_exact_keys(
        engine_value,
        frozenset({"name", "version", "capability_sha256"}),
        "H09_ENGINE_KEYS",
    )
    engine = {
        "name": _require_string(engine_value["name"], "H09_ENGINE_NAME"),
        "version": _require_string(
            engine_value["version"], "H09_ENGINE_VERSION"
        ),
        "capability_sha256": _validate_digest(
            engine_value["capability_sha256"], "H09_ENGINE_CAPABILITY"
        ),
    }
    bindings = _parse_binding_map(owner_value["bindings"])
    read_only = _require_bool(owner_value["read_only"], "H09_READ_ONLY")
    if not read_only:
        _fail("H09_READ_ONLY")
    opt_in = _require_string(
        owner_value["affirmative_opt_in"], "H09_OPT_IN"
    )
    if opt_in != READ_ONLY_OPT_IN:
        _fail("H09_OPT_IN")
    valid_until = _parse_utc(owner_value["valid_until"], "H09_VALID_UNTIL")
    comparison_time = now or datetime.now(timezone.utc)
    if comparison_time.tzinfo is None:
        _fail("H09_NOW_TIMEZONE")
    if valid_until <= comparison_time.astimezone(timezone.utc):
        _fail("H09_INPUT_STALE")

    capability_value = _require_mapping(
        value["requested_capabilities"], "H09_CAPABILITIES_OBJECT"
    )
    _require_exact_keys(
        capability_value,
        frozenset(
            {
                "rpc_methods",
                "local_fork_actions",
                "real_signer",
                "broadcast",
                "live_mutation",
            }
        ),
        "H09_CAPABILITIES_KEYS",
    )
    for key in ("real_signer", "broadcast", "live_mutation"):
        if _require_bool(capability_value[key], "H09_FORBIDDEN_CAPABILITY"):
            _fail("H09_FORBIDDEN_CAPABILITY")
    rpc_methods = _parse_rpc_methods(capability_value["rpc_methods"])
    local_actions = _parse_local_actions(
        capability_value["local_fork_actions"]
    )

    canonical = canonical_json_bytes(value)
    owner = OwnerInputs(
        profile=profile,
        expected_chain_id=expected_chain_id,
        pin=pin,
        endpoint=endpoint,
        identity_manifest_sha256=_validate_digest(
            owner_value["identity_manifest_sha256"],
            "H09_IDENTITY_MANIFEST_DIGEST",
        ),
        identity_manifest_schema=_require_string(
            owner_value["identity_manifest_schema"],
            "H09_IDENTITY_MANIFEST_SCHEMA",
        ),
        evidence_destination=destination,
        read_only=read_only,
        affirmative_opt_in=opt_in,
        valid_until=valid_until,
        rpc_methods=rpc_methods,
        local_fork_actions=local_actions,
        bindings=bindings,
        fork_engine=engine,
    )
    if owner.identity_manifest_schema != IDENTITY_SCHEMA:
        _fail("H09_IDENTITY_MANIFEST_SCHEMA")
    return QualificationEnvelope(
        repository=repository,
        owner=owner,
        canonical_bytes=canonical,
        sha256=hashlib.sha256(
            b"RIPE_H09_INPUT_ENVELOPE_V1\0" + canonical
        ).hexdigest(),
    )


def parse_identity_manifest(data: bytes) -> CanonicalIdentityManifest:
    value = _canonical_mapping(data, code="H09_IDENTITY_MANIFEST")
    _require_exact_keys(
        value,
        frozenset(
            {
                "artifact_kind",
                "schema_version",
                "profile",
                "chain_id",
                "identities",
                "owner_approval_sha256",
            }
        ),
        "H09_IDENTITY_MANIFEST_KEYS",
    )
    if value["artifact_kind"] != "rh_canonical_identity_manifest":
        _fail("H09_IDENTITY_MANIFEST_KIND")
    if value["schema_version"] != IDENTITY_SCHEMA:
        _fail("H09_IDENTITY_MANIFEST_SCHEMA")
    profile = _require_string(value["profile"], "H09_IDENTITY_PROFILE")
    if profile not in {"robinhood-mainnet", "robinhood-testnet"}:
        _fail("H09_IDENTITY_PROFILE")
    chain_id = _require_positive_int(
        value["chain_id"], "H09_IDENTITY_CHAIN_ID"
    )
    if chain_id != {
        "robinhood-mainnet": 4663,
        "robinhood-testnet": 46630,
    }[profile]:
        _fail("H09_IDENTITY_CHAIN_CONTRADICTION")
    rows = value["identities"]
    if not isinstance(rows, list) or not rows:
        _fail("H09_IDENTITIES")
    identities: list[CanonicalIdentity] = []
    seen_ids: set[str] = set()
    for row_value in rows:
        row = _require_mapping(row_value, "H09_IDENTITY_OBJECT")
        _require_exact_keys(
            row,
            frozenset(
                {
                    "identity_id",
                    "kind",
                    "address",
                    "proxy_address",
                    "implementation_address",
                    "runtime_code_sha256",
                    "authority",
                    "provenance_sha256",
                }
            ),
            "H09_IDENTITY_KEYS",
        )
        identity_id = _require_string(
            row["identity_id"], "H09_IDENTITY_ID"
        )
        kind = _require_string(row["kind"], "H09_IDENTITY_KIND")
        if not _IDENTIFIER.fullmatch(identity_id):
            _fail("H09_IDENTITY_ID")
        if not _IDENTIFIER.fullmatch(kind):
            _fail("H09_IDENTITY_KIND")
        if identity_id in seen_ids:
            _fail("H09_IDENTITY_DUPLICATE")
        seen_ids.add(identity_id)
        authority = _require_string(
            row["authority"], "H09_IDENTITY_AUTHORITY"
        )
        if authority != "owner-supplied":
            _fail("H09_IDENTITY_AUTHORITY")
        identities.append(
            CanonicalIdentity(
                identity_id=identity_id,
                kind=kind,
                address=_validate_address(
                    row["address"], "H09_IDENTITY_ADDRESS"
                ),
                proxy_address=_optional_address(
                    row["proxy_address"], "H09_IDENTITY_PROXY"
                ),
                implementation_address=_optional_address(
                    row["implementation_address"],
                    "H09_IDENTITY_IMPLEMENTATION",
                ),
                runtime_code_sha256=_validate_digest(
                    row["runtime_code_sha256"], "H09_IDENTITY_RUNTIME"
                ),
                authority=authority,
                provenance_sha256=_validate_digest(
                    row["provenance_sha256"], "H09_IDENTITY_PROVENANCE"
                ),
            )
        )
    if tuple(item.identity_id for item in identities) != tuple(
        sorted(seen_ids)
    ):
        _fail("H09_IDENTITY_ORDER")
    canonical = canonical_json_bytes(value)
    return CanonicalIdentityManifest(
        profile=profile,
        chain_id=chain_id,
        identities=tuple(identities),
        owner_approval_sha256=_validate_digest(
            value["owner_approval_sha256"], "H09_OWNER_APPROVAL"
        ),
        canonical_bytes=canonical,
        sha256=hashlib.sha256(canonical).hexdigest(),
    )


def bind_identity_manifest(
    envelope: QualificationEnvelope,
    manifest: CanonicalIdentityManifest,
) -> None:
    if manifest.sha256 != envelope.owner.identity_manifest_sha256:
        _fail("H09_IDENTITY_MANIFEST_DIGEST_MISMATCH")
    if manifest.profile != envelope.owner.profile:
        _fail("H09_IDENTITY_MANIFEST_PROFILE_MISMATCH")
    if manifest.chain_id != envelope.owner.expected_chain_id:
        _fail("H09_IDENTITY_MANIFEST_CHAIN_MISMATCH")


def qualification_mode(environment: Mapping[str, str]) -> str:
    value = environment.get(MODE_ENV)
    if value in (None, "", DISABLED_MODE):
        return DISABLED_MODE
    if value != READ_ONLY_OPT_IN:
        _fail("H09_MODE_INVALID")
    return READ_ONLY_OPT_IN


def validate_environment(
    environment: Mapping[str, str], *, endpoint_alias: str | None = None
) -> None:
    for name in FORBIDDEN_ENV_NAMES:
        if environment.get(name):
            _fail("H09_FORBIDDEN_ENVIRONMENT")
    if endpoint_alias is not None:
        if not _ENV_ALIAS.fullmatch(endpoint_alias):
            _fail("H09_ENDPOINT_ALIAS")
        if not environment.get(endpoint_alias):
            _fail("H09_ENDPOINT_MISSING")
    owner_aliases = sorted(
        name
        for name, value in environment.items()
        if name.startswith("OWNER_RH_ARCHIVE_") and value
    )
    expected = [] if endpoint_alias is None else [endpoint_alias]
    if owner_aliases != expected:
        _fail("H09_ENDPOINT_ALIAS_DRIFT")


def endpoint_fingerprint(value: str) -> str:
    try:
        parsed = urlsplit(value)
        if parsed.scheme.lower() != "https":
            _fail("H09_ENDPOINT_SCHEME")
        if not parsed.hostname:
            _fail("H09_ENDPOINT_HOST")
        port = parsed.port
    except (ValueError, UnicodeError) as error:
        raise ForkFrameworkError("H09_ENDPOINT_MALFORMED") from error
    origin = f"https://{parsed.hostname.lower()}"
    if port not in (None, 443):
        origin += f":{port}"
    return hashlib.sha256(
        b"RIPE_H09_ARCHIVE_ENDPOINT_V1\0" + origin.encode("ascii")
    ).hexdigest()


def resolve_endpoint(
    endpoint: EndpointIdentity, environment: Mapping[str, str]
) -> OpaqueEndpoint:
    validate_environment(environment, endpoint_alias=endpoint.external_alias)
    value = environment[endpoint.external_alias]
    actual = endpoint_fingerprint(value)
    if actual != endpoint.fingerprint_sha256:
        _fail("H09_ENDPOINT_FINGERPRINT_MISMATCH")
    return OpaqueEndpoint(value, endpoint.external_alias, actual)


def _read_external_manifest(
    path_value: str | None, *, code: str, maximum_bytes: int = 1_048_576
) -> bytes:
    if not path_value:
        _fail(f"{code}_MISSING")
    path = Path(path_value)
    if not path.is_absolute() or not path.is_file() or path.is_symlink():
        _fail(f"{code}_PATH")
    try:
        size = path.stat().st_size
        if size <= 0 or size > maximum_bytes:
            _fail(f"{code}_SIZE")
        return path.read_bytes()
    except OSError as error:
        raise ForkFrameworkError(f"{code}_READ") from error


def preflight_from_environment(
    environment: Mapping[str, str],
    *,
    observed_commit: str,
    observed_tree: str,
    changed_paths: Sequence[str] = (),
    staged_paths: Sequence[str] = (),
    ignored_paths: Sequence[str] = (),
    now: datetime | None = None,
) -> PreflightResult:
    if qualification_mode(environment) != READ_ONLY_OPT_IN:
        _fail("H09_OPT_IN_REQUIRED")
    envelope = parse_input_envelope(
        _read_external_manifest(
            environment.get(MANIFEST_ENV), code="H09_ENVELOPE_FILE"
        ),
        now=now,
    )
    identity_manifest = parse_identity_manifest(
        _read_external_manifest(
            environment.get(IDENTITY_MANIFEST_ENV),
            code="H09_IDENTITY_FILE",
        )
    )
    bind_identity_manifest(envelope, identity_manifest)
    validate_repository_authority(
        envelope.repository,
        observed_commit=observed_commit,
        observed_tree=observed_tree,
        changed_paths=changed_paths,
        staged_paths=staged_paths,
        ignored_paths=ignored_paths,
    )
    endpoint = resolve_endpoint(envelope.owner.endpoint, environment)
    return PreflightResult(envelope, identity_manifest, endpoint)


def validate_rpc_inventory(methods: Sequence[str]) -> tuple[str, ...]:
    if any(
        method.startswith(prefix)
        for method in methods
        for prefix in FORBIDDEN_RPC_METHOD_PREFIXES
    ):
        _fail("H09_RPC_METHOD_FORBIDDEN")
    unknown = set(methods) - READ_ONLY_RPC_METHODS
    if unknown:
        _fail("H09_RPC_METHOD_UNAPPROVED")
    return tuple(methods)


def validate_external_root(
    path: Path, *, repository_root: Path = REPOSITORY_ROOT
) -> Path:
    if not path.is_absolute() or not path.is_dir() or path.is_symlink():
        _fail("H09_EXTERNAL_ROOT")
    resolved = path.resolve()
    repository = repository_root.resolve()
    if resolved == repository or repository in resolved.parents:
        _fail("H09_EXTERNAL_ROOT_REPOSITORY")
    if stat.S_IMODE(resolved.stat().st_mode) != 0o700:
        _fail("H09_EXTERNAL_ROOT_MODE")
    return resolved


def validate_repository_authority(
    authority: RepositoryAuthority,
    *,
    observed_commit: str,
    observed_tree: str,
    changed_paths: Sequence[str],
    staged_paths: Sequence[str],
    ignored_paths: Sequence[str],
) -> None:
    if authority.commit != observed_commit:
        _fail("H09_REPOSITORY_COMMIT_MISMATCH")
    if authority.tree != observed_tree:
        _fail("H09_REPOSITORY_TREE_MISMATCH")
    if authority.path_ceiling != PATH_CEILING:
        _fail("H09_PATH_CEILING")
    if changed_paths or staged_paths or ignored_paths:
        _fail("H09_REPOSITORY_NOT_CLEAN")


def bind_observed_facts(
    envelope: QualificationEnvelope,
    observed: ObservedForkFacts,
) -> BoundForkIdentity:
    owner = envelope.owner
    expected = (
        (owner.expected_chain_id, observed.chain_id, "H09_CHAIN_ID_MISMATCH"),
        (owner.pin.number, observed.block_number, "H09_BLOCK_NUMBER_MISMATCH"),
        (owner.pin.block_hash, observed.block_hash, "H09_BLOCK_HASH_MISMATCH"),
        (
            owner.pin.parent_hash,
            observed.parent_hash,
            "H09_PARENT_HASH_MISMATCH",
        ),
        (
            owner.pin.state_root,
            observed.state_root,
            "H09_STATE_ROOT_MISMATCH",
        ),
        (owner.pin.timestamp, observed.timestamp, "H09_TIMESTAMP_MISMATCH"),
        (
            owner.endpoint.fingerprint_sha256,
            observed.endpoint_fingerprint_sha256,
            "H09_ENDPOINT_FINGERPRINT_MISMATCH",
        ),
    )
    for wanted, actual, code in expected:
        if wanted != actual:
            _fail(code)
    return BoundForkIdentity(envelope.repository, owner, observed)


def validate_clock_observation(
    *,
    rpc_child_number: int,
    rpc_l1_number: int,
    evm_number: int,
    timestamp: int,
    arbsys_number: int,
    expected: Mapping[str, int],
) -> None:
    observed = {
        "rpc_child_number": rpc_child_number,
        "rpc_l1_number": rpc_l1_number,
        "evm_number": evm_number,
        "timestamp": timestamp,
        "arbsys_number": arbsys_number,
    }
    if frozenset(expected) != frozenset(observed):
        _fail("H09_CLOCK_FIELDS")
    if any(
        not isinstance(value, int) or isinstance(value, bool) or value < 0
        for value in observed.values()
    ):
        _fail("H09_CLOCK_VALUE")
    if dict(expected) != observed:
        _fail("H09_CLOCK_DIVERGENCE")


def validate_local_fork_action(
    action: str,
    *,
    disposable_runtime_active: bool,
    targets_local_fork: bool,
    requests_real_signer: bool = False,
    requests_broadcast: bool = False,
) -> None:
    if action not in LOCAL_FORK_ACTIONS:
        _fail("H09_LOCAL_ACTION_FORBIDDEN")
    if (
        not disposable_runtime_active
        or not targets_local_fork
        or requests_real_signer
        or requests_broadcast
    ):
        _fail("H09_LOCAL_ACTION_SCOPE")


def _assert_secret_free(value: Any, *, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                _fail("H09_EVIDENCE_KEY")
            lowered = key.lower()
            if any(part in lowered for part in _SENSITIVE_KEY_PARTS):
                _fail("H09_EVIDENCE_SECRET_KEY")
            _assert_secret_free(item, path=(*path, key))
    elif isinstance(value, list):
        for item in value:
            _assert_secret_free(item, path=path)
    elif isinstance(value, str):
        lowered = value.lower()
        if (
            "://" in value
            or "-----begin" in lowered
            or lowered.startswith(("sk-", "pk-"))
        ):
            _fail("H09_EVIDENCE_SECRET_VALUE")


def deterministic_evidence_bytes(value: Mapping[str, Any]) -> bytes:
    _assert_secret_free(value)
    return canonical_json_bytes(dict(value))


def deterministic_evidence_hash(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        b"RIPE_H09_EVIDENCE_V1\0" + deterministic_evidence_bytes(value)
    ).hexdigest()


def ordered_node_digest(node_ids: Sequence[str]) -> str:
    if len(node_ids) != len(set(node_ids)):
        _fail("H09_NODE_LEDGER_DUPLICATE")
    return hashlib.sha256(
        b"RIPE_H09_NODE_LEDGER_V1\0"
        + canonical_json_bytes({"node_ids": list(node_ids)})
    ).hexdigest()


def replay_identity(
    *,
    envelope_sha256: str,
    identity_manifest_sha256: str,
    ordered_node_sha256: str,
) -> str:
    for digest in (
        envelope_sha256,
        identity_manifest_sha256,
        ordered_node_sha256,
    ):
        _validate_digest(digest, "H09_REPLAY_INPUT")
    return hashlib.sha256(
        b"RIPE_H09_REPLAY_V1\0"
        + canonical_json_bytes(
            {
                "envelope_sha256": envelope_sha256,
                "identity_manifest_sha256": identity_manifest_sha256,
                "ordered_node_sha256": ordered_node_sha256,
            }
        )
    ).hexdigest()


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "rh_archive_fork: requires explicit read-only Robinhood archive-fork "
        "opt-in and a complete owner input envelope",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    mode = qualification_mode(os.environ)
    if mode == READ_ONLY_OPT_IN:
        return
    skip = pytest.mark.skip(
        reason="H-09 archive-fork execution requires explicit read-only opt-in"
    )
    for item in items:
        if item.get_closest_marker("rh_archive_fork") is not None:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def ripe_hq() -> None:
    return None


@pytest.fixture(scope="session")
def fork_framework() -> SimpleNamespace:
    return SimpleNamespace(
        **{
            name: value
            for name, value in globals().items()
            if not name.startswith("__")
        }
    )


@pytest.fixture
def digest() -> str:
    return "12" * 32


@pytest.fixture
def hash32() -> str:
    return "0x" + "34" * 32


@pytest.fixture
def owner_bindings(digest: str) -> dict[str, dict[str, str]]:
    return {
        name: {"sha256": digest, "version": f"{name}-v1"}
        for name in (
            "h05_plan",
            "typed_actions",
            "h06_evidence",
            "h07_artifacts",
            "h08_assertions",
            "h09_contract",
        )
    }


@pytest.fixture
def envelope_value(
    tmp_path: Path,
    digest: str,
    hash32: str,
    owner_bindings: dict[str, dict[str, str]],
) -> dict[str, Any]:
    evidence = tmp_path / "evidence"
    evidence.mkdir(mode=0o700)
    return {
        "artifact_kind": "rh_archive_fork_input_envelope",
        "owner_inputs": {
            "affirmative_opt_in": "read-only-archive-fork",
            "bindings": owner_bindings,
            "endpoint": {
                "external_alias": "OWNER_RH_ARCHIVE_TEST",
                "fingerprint_sha256": digest,
            },
            "evidence_destination": str(evidence),
            "expected_chain_id": 46630,
            "fork_engine": {
                "capability_sha256": digest,
                "name": "injected-test-double",
                "version": "1",
            },
            "identity_manifest_schema": IDENTITY_SCHEMA,
            "identity_manifest_sha256": digest,
            "pin": {
                "block_hash": hash32,
                "block_number": 123,
                "finality": "owner-approved-immutable",
                "parent_hash": "0x" + "56" * 32,
                "state_root": "0x" + "78" * 32,
                "timestamp": 1_800_000_000,
            },
            "profile": "robinhood-testnet",
            "read_only": True,
            "valid_until": "2030-01-01T00:00:00Z",
        },
        "repository_authority": {
            "commit": "ab" * 20,
            "suite_path_ceiling": PATH_CEILING,
            "tree": "cd" * 20,
        },
        "requested_capabilities": {
            "broadcast": False,
            "live_mutation": False,
            "local_fork_actions": [
                "impersonate",
                "set_balance",
                "set_storage",
                "time_travel",
            ],
            "real_signer": False,
            "rpc_methods": sorted(READ_ONLY_RPC_METHODS),
        },
        "schema_version": FRAMEWORK_SCHEMA,
    }


@pytest.fixture
def parse_envelope(
    fork_framework: SimpleNamespace, envelope_value: dict[str, Any]
) -> Callable[..., QualificationEnvelope]:
    def parse(value: Any = None, *, now: datetime | None = None):
        actual = envelope_value if value is None else value
        data = canonical_json_bytes(actual)
        return parse_input_envelope(
            data,
            now=now or datetime(2029, 1, 1, tzinfo=timezone.utc),
        )

    return parse


@pytest.fixture(autouse=True)
def safe_default_network_block(monkeypatch: pytest.MonkeyPatch) -> None:
    if qualification_mode(os.environ) == READ_ONLY_OPT_IN:
        return

    def blocked(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("H-09 default mode disables external networking")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(requests.sessions.Session, "request", blocked)
